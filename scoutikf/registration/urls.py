#coding: utf8
from django.contrib import admin
from django.urls import path
from registration import views
from django.conf.urls.static import static
from django.conf import settings
import re


urlpatterns = [
    path("", views.homeindex, name='homeindex'),
    path("category/<lang>", views.category, name='category'),
    path("coachorplayer/<lang>/<category>",
         views.coachorplayer, name='coachorplayer'),



    path("main", views.main, name='main'),
    path("mygroup", views.mygroup, name='mygroup'),
    path("preview1", views.preview1, name='preview1'),
    path("preview2", views.preview2, name='preview2'),
    path("uploaddoc", views.uploaddoc, name='uploaddoc'),
    path("viewpic", views.viewpic, name='viewpic'),
    path("uploadpic", views.uploadpic, name='uploadpic'),
    path("viewdoc", views.viewdoc, name='viewdoc'),
    path("viewdocpic", views.viewdocpic, name='viewdocpic'),
    path("save", views.save, name='save'),
    path("amount", views.amount, name="amount"),
    path("order", views.order, name='order'),
    path("payment", views.paymentfun, name='payment'),

    path("statedata", views.statedata, name='statedata'),
    path("citydata", views.citydata, name='citydata'),
    path("positiondata", views.positiondata, name='positiondata'),
    path("documentdata", views.documentdata, name='documentdata'),

    path("printpdf", views.printpdf, name='printpdf'),
    path("paymentfail", views.paymentfail, name='paymentfail'),

    path("converter", views.converter, name='converter'),

    path("playerdata",views.playerdata, name='playerdata'),
    path("partnerinfo",views.partnerinfo, name='partnerinfo'),
    path("paymentstatus",views.paymentstatus, name='paymentstatus'),
    

    path("limitdate",views.limitdate, name='limitdate'),










]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
