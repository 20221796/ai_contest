from glob import glob
from http.client import HTTPResponse
from django.shortcuts import render, HttpResponse, redirect
from django.views.decorators import gzip
from django.http import StreamingHttpResponse
import cv2
from pathlib import Path
# import playsound
import time
import threading
from django.urls import reverse

# from .models import *

import math
# Create your views here.

def index(request):
    return render(request, 'bodygree/index.html')

def test(request):
    return render(request, 'bodygree/test.html')

# MPII에서 각 파트 번호, 선으로 연결될 POSE_PAIRS
BODY_PARTS = { "Head": 0, "Neck": 1, "RShoulder": 2, "RElbow": 3, "RWrist": 4,
                "LShoulder": 5, "LElbow": 6, "LWrist": 7, "RHip": 8, "RKnee": 9,
                "RAnkle": 10, "LHip": 11, "LKnee": 12, "LAnkle": 13, "Chest": 14,
                "Background": 15 }

POSE_PAIRS = [ ["Head", "Neck"], ["Neck", "RShoulder"], ["RShoulder", "RElbow"],
                ["RElbow", "RWrist"], ["Neck", "LShoulder"], ["LShoulder", "LElbow"],
                ["LElbow", "LWrist"], ["Neck", "Chest"], ["Chest", "RHip"], ["RHip", "RKnee"],
                ["RKnee", "RAnkle"], ["Chest", "LHip"], ["LHip", "LKnee"], ["LKnee", "LAnkle"] ]

# 각 파일 path
BASE_DIR = Path(__file__).resolve().parent
# protoFile = "bodygree\pose_deploy_linevec_faster_4_stages.prototxt"
# weightsFile = "bodygree\pose_iter_160000.caffemodel"
protoFile = "bodygree/pose_deploy_linevec_faster_4_stages.prototxt"
weightsFile = "bodygree/pose_iter_160000.caffemodel"

# 위의 path에 있는 network 모델 불러오기
net = cv2.dnn.readNetFromCaffe(protoFile, weightsFile)

# openCV의 좌표계는 좌측위가 (0,0)이다...
# 아래/오른쪽으로 갈수록 증가한다


status=2
keep_time=[0,0,0]
points = []
Success_Fail=["Success","Fail"]

return_result=""

############################################
# 1초마다 자세를 체크하도록 코드를 짰다. => threading.Timer 사용
        
def check_timer2(pose_type):
    global keep_time,status
    global return_result
    if show_result(pose_type,status) =='Success':
        if keep_time[0]==10 or keep_time[2] == 10: # 자세유지 10초 하면 끝
            result=show_result(pose_type,status) #Success / Fail
            return_result=result
        
        elif keep_time[status]==0:
            #다른 모션에서 바뀌어 들어옴
            # keep_time[0]=keep_time[2]=0
            keep_time[status]+=1

        elif keep_time[status]!=0:
            keep_time[status]+=1
    else:
        keep_time[1] +=1

    print(keep_time[0],keep_time[1],keep_time[2])
    
    if return_result=="":
        threading.Timer(1.0,check_timer2,(pose_type,)).start()


##################################################
# 자세 체크 함수들

def check_body(points):
    if points[0] and points[2] and points[5] and points[8] and points [11]:
        head_x,head_y=points[0] #머리
        rs_x,rs_y=points[2] #오른쪽 어깨
        ls_x,ls_y=points[5] #왼쪽 어깨
        rh_x,rh_y=points[8] #오른쪽 골반
        lh_x,lh_y=points[11] #왼쪽 골반

        if rs_y > ls_y or rs_y < ls_y or rh_y > lh_y or rh_y < lh_y: #어깨 높이나 골반 높이가 차이 남
            s_gradient = (rs_y-ls_y)/(rs_x-ls_x) #어깨 기울기
            h_gradient = (rh_y-lh_y)/(rh_x-lh_x) #골반 기울기
            degree = math.radians(5)
            standard_gradient = math.tan(degree)
            
            if s_gradient > standard_gradient or h_gradient > standard_gradient:
                return True
            else:
                return False

#################################################
# 결과를 반환하는 함수

def show_result(pose_type,status): #END/Again
    global points
    
    try:
        if points[0] and points[2] and points[5] and points[8] and points[11]:
            if status==0: #status 0
                if pose_type=="bodycheck":
                    print("자세 검출중 (척추 측만증)") 
                    return "Success"
            
            elif status==2: #status 2     
                if pose_type=="bodycheck":
                    print("자세 검출중 (정상 척추)")
                    return "Success"
            else:
                return "Again"
    except:
        return "Again"
            
##################################################

    
class Openpose(object):
    def __init__(self):
        #self.video = cv2.VideoCapture(0)  #for mac
        self.video = cv2.VideoCapture(0,cv2.CAP_DSHOW)  #for window
        global status,return_result
        status=2
        return_result=""
        
    def __del__(self):
        self.video.release()
        cv2.destroyAllWindows()
    
    def get_frame(self,pose_type):
        global status,return_result
        self.status=status
        _,frame = self.video.read()
        inputWidth=320;
        inputHeight=240;
        inputScale=1.0/255;
        
        frameWidth = frame.shape[1]
        frameHeight = frame.shape[0]
    
        inpBlob = cv2.dnn.blobFromImage(frame, inputScale, (inputWidth, inputHeight), (0, 0, 0), swapRB=False, crop=False)
        
        # network에 넣어주기
        net.setInput(inpBlob)

        # 결과 받아오기
        output = net.forward() #추론을 진행할때 이용하는 함수
        
        # 키포인트 검출시 이미지에 그려줌
        global points
        points = []
        for i in range(0,15):
            # 해당 신체부위 신뢰도 얻음.
            probMap = output[0, i, :, :]

            # global 최대값 찾기
            minVal, prob, minLoc, point = cv2.minMaxLoc(probMap)

            # 원래 이미지에 맞게 점 위치 변경
            x = (frameWidth * point[0]) / output.shape[3]
            y = (frameHeight * point[1]) / output.shape[2]

            # 키포인트 검출한 결과가 0.1보다 크면(검출한곳이 위 BODY_PARTS랑 맞는 부위면) points에 추가, 검출했는데 부위가 없으면 None으로    
            if prob > 0.1 :    
                cv2.circle(frame, (int(x), int(y)), 3, (0, 255, 255), thickness=-1, lineType=cv2.FILLED) # circle(그릴곳, 원의 중심, 반지름, 색)
                cv2.putText(frame, "{}".format(i), (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, lineType=cv2.LINE_AA)
                points.append((int(x), int(y)))
            else :
                points.append(None)
                             
        #bodycheck일때
        if pose_type=="bodycheck":
            if check_body(points):
                status=0
                cv2.putText(frame, "Bad Spine status" , (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 1, lineType=cv2.LINE_AA)
            else:
                status=2
                cv2.putText(frame, "Good Spine status" , (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 1, lineType=cv2.LINE_AA)

        #결과가 결정이 나면 반환
        if return_result in Success_Fail:
            return return_result
        
        
        # 각 POSE_PAIRS별로 선 그어줌 (머리 - 목, 목 - 왼쪽어깨, ...)
        for pair in POSE_PAIRS:
            partA = pair[0]             # Head
            partA = BODY_PARTS[partA]   # 0
            partB = pair[1]             # Neck
            partB = BODY_PARTS[partB]   # 1

            #print(partA," 와 ", partB, " 연결\n")
            if points[partA] and points[partB]:
                cv2.line(frame, points[partA], points[partB], (0, 255, 0), 2)
                
        #self.fps.update()
        _, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()
    
def gen(camera,pose_type):
    check_timer2(pose_type)
    
    while True:
        frame = camera.get_frame(pose_type)
        
        #결과가 나오면 카메라를 끄고 반복문 break
        if frame in Success_Fail: 
            del camera
            break
        else:
            yield(b'--frame\r\n'
                 b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')



#########################################
# detectme 관련 함수들

@gzip.gzip_page
def detectme_bodycheck(request):
    try:
        return StreamingHttpResponse(gen(Openpose(),"bodycheck"), content_type="multipart/x-mixed-replace;boundary=frame")
    except:  # This is bad! replace it with proper handling
        print("에러입니다...")
        pass


##########################################
# 링크 관련 함수들

def home(request):
    return render(request, "bodygree/home.html") #home.html을 호출해서 띄워준다.

def login(request):
    return render(request, "bodygree/login.html")

def HTMLTemplate(request,pose_type):
    return render(request,"bodygree/HTMLTemplate.html",{"pose_type":pose_type})

def Bodycheck(request):
    pose_type="bodycheck"
    return HttpResponse(HTMLTemplate(request,pose_type))

def dignore(request):
    return render(request, "bodygree/dignore.html")

def result(request):
    if keep_time[0] == 10:
        return render(request, "bodygree/result_bad.html")
    elif keep_time[2] == 10:
        return render(request, "bodygree/result_good.html")