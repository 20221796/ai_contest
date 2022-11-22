from django.db import models

# Create your models here.
class login(models.Model):
    id = models.CharField(max_length=100, primary_key=True, unique=True)
    pw = models.CharField(max_length=200)