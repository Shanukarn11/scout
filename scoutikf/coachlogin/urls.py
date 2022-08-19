#coding: utf8
from django.contrib import admin
from django.urls import path
from coachlogin import views as coachlogin
from django.conf.urls.static import static
from django.conf import settings
import re

from registration import coachviews
from registration import views as regviews


urlpatterns = [
    path("", coachlogin.login, name='coachlogin'),
    path("verifycoachlogin", coachlogin.verifylogin, name='verifycoachlogin'),
    path("coachdashboard", coachlogin.coachdashboard, name='coachdashboard'),
    path("coachdatalogin", coachlogin.coachdatalogin, name='coachdatalogin'),
    path("positiondata", regviews.positiondata, name='positiondata'),
    path("academypreview", coachviews.academypreview, name='academypreview'),
    path("addplayer", coachviews.addplayer, name='addplayer'),
    path("addcoach", coachviews.addcoach, name='addcoach'),
    path("admitcard", coachviews.admitcard, name='admitcard'),
    path("coachplayer", coachviews.coachplayer, name='coachplayer'),
    path('coachamount',coachlogin.amount,name='coachamount'),
    path('coachpayment',coachlogin.payment,name='coachpayment'),
    path('coachorder',coachlogin.order,name='coachorder'),
    path('coachpaymentstatus',coachlogin.paymentstatus,name='coachpaymentstatus'),
    path('reciept',coachlogin.reciept,name='reciept'),
    path('documentid',coachlogin.documentid,name='documentid'),
    path('checkage',coachviews.checkAge,name='checkage'),
    path('getcity',coachlogin.getcity,name='getcity'),
    path('getstate',coachlogin.getstate,name='getstate'),
    path("limitdate",regviews.limitdate, name='limitdate'),













]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
