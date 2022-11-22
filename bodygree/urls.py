from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('test', views.test, name='test'),
    path('home', views.home, name='home'), # 웹사이트 링크 home.html
    # path("detectme", views.detectme, name='detectme'), # 웹캠 링크

    path("detectme_OX", views.detectme_OX, name="detectme_OX"),
    path("detectme_XHandsUp", views.detectme_XHandsUp, name="detectme_XHandsUp"),
    path("detectme_Stretching", views.detectme_Stretching, name="detectme_Stretching"),
    
    path('OX', views.OX, name="OX"),
    path('XHandsUp', views.XHandsUp, name="XHandsUp"),
    path('Stretching', views.Stretching, name="Stretching"),
]