#coding: utf8



from django.core import serializers

from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse, Http404, JsonResponse

from django.views.static import serve

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages



from registration.modelhome import SocialMediaLink
from registration.models import MasterAmount, MasterCategory, MasterColumn, MasterDateLimit, MasterDocument, MasterGroup, MasterGroupCity, MasterLabels, MasterPartner, MasterRoles, MasterSeason, MasterState, MasterCity, MasterPosition, Player, Upload, Uploadfile,Payment


from django.db import IntegrityError
from django.db.models import Q
from django.views.decorators.cache import cache_control

import qrcode
from PIL import Image

from barcode.writer import ImageWriter
import barcode
import oss2


# def login(request):
#     if request.method == 'POST':
#         season = request.POST.getlist('season')[0]
#         datevalue=list(MasterDateLimit.objects.filter(season=season).values())

#         return JsonResponse(datevalue[0], safe=False)

def login(request):
    lang = "en"
    langqueryset = MasterLabels.objects.filter().values('keydata', lang)
    dict = {}
    for item in langqueryset:
        dict[item['keydata']] = item[lang]
    return render(request, 'login.html', dict)

def verifylogin(request):
    if request.method == 'POST':
        ikfuniqueid = request.POST.getlist('ikfuniqueid')[0]
        mobile = request.POST.getlist('mobile')[0]
        player=list(Player.objects.filter(ikfuniqueid=ikfuniqueid,mobile=mobile).values())
        if player:
            dictdata=dict()
            dictdata['error']="false"
            dictdata['login']="success"
            dictdata['ikfuniqueid']=player[0]['ikfuniqueid']
            return JsonResponse(dictdata,safe=False)
        else:
            dictdata=dict()
            dictdata['error']="false"
            dictdata['login']="failed"
            return JsonResponse(dictdata, safe=False)   
    else:
        dictdata=dict()
        dictdata['error']="true"
        dictdata['login']="failed"
        return JsonResponse(dictdata, safe=False) 

def playerdashboard(request):
    lang = "en"

    langqueryset = MasterLabels.objects.filter().values('keydata', lang)

    mycolumns = MasterColumn.objects.filter(includep2=1).values(
        'columnid', 'label_key', 'type', 'orderid')

    dict = {}

    for item in langqueryset:
        dict[item['keydata']] = item[lang]
    for item in mycolumns:
        item['label'] = dict[item['label_key']]
    dict['formikf'] = mycolumns
    dict['url_prev'] = "uploaddoc"
    dict['preview_type'] = "preview2"
    dict['url_next'] = "main"
    dict['button_text'] = "Submit"
    return render(request, 'playerdashboard.html', dict)

def playerdatalogin(request):
    if request.method == 'POST':
        
        ikfid = request.POST.get('ikfuniqueid')
        playerdata = list(Player.objects.filter(ikfuniqueid=ikfid).values())
        print(playerdata)
        
    return JsonResponse(playerdata[0], safe=False)
