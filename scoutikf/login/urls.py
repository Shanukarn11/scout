#coding: utf8
from django.contrib import admin
from django.urls import path
from login import views
from django.conf.urls.static import static
from django.conf import settings
import re


urlpatterns = [
    path("", views.login, name='login'),
    path("verifylogin", views.verifylogin, name='verifylogin'),
    path("playerdashboard", views.playerdashboard, name='playerdashboard'),
    path("playerdatalogin", views.playerdatalogin, name='playerdatalogin'),
    












]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
