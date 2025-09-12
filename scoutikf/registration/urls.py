#coding: utf8
from django.contrib import admin
from django.urls import path
from registration import views
from registration import views_level2
from django.conf.urls.static import static
from django.conf import settings
import re


urlpatterns = [
    path("", views.homeindex, name='homeindex'),
    path("category/<lang>", views.category, name='category'),
    path("scoutpage/<lang>/<category>",
         views.scoutpage, name='scoutpage'),



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
    path("scoutdiscountamount",views.scoutdiscountamount, name='scoutdiscountamount'),
    path('update-scout-payment-status/', views.update_scout_payment_status, name='update_scout_payment_status'),





  path("level2", views_level2.level2_form, name="level2_form"),                    # GET → page
    path("level2/prefill", views_level2.level2_prefill, name="level2_prefill"),      # POST
    path("level2/save", views_level2.level2_save, name="level2_save"),               # POST (Confirm)
    path("level2/order", views_level2.level2_order, name="level2_order"),            # POST (Create Razorpay order)
    path("level2/payment-status", views_level2.level2_payment_status, name="level2_payment_status"),  # POST (optional)
    path("level2/level2_pass", views_level2.level2_pass, name="level2_pass"),


  # POST



]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
