#coding: utf8
from email.errors import StartBoundaryNotFoundDefect
from errno import errorcode
from http import HTTPStatus
import os
import shutil
import json
import glob
import subprocess
import time
from tokenize import group
import uuid
import PIL
from django.core import serializers
from numpy import less_equal
import razorpay
import datetime
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseBadRequest, JsonResponse
from django.db.models import Q

from django.views.static import serve

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django import forms
import pathlib
from django.db import transaction
from treepoem import barcode_types

from registration.coach_models import CoachModel, MasterCoachLabels
from .models import  MasterCategory, MasterDocument, MasterGroup, MasterGroupCity, MasterLabels, MasterPosition, MasterRoles, MasterSeason, MasterState, MasterCity, Scout
from django.db import IntegrityError


from PIL import Image
from barcode.writer import ImageWriter
import barcode

import base64


BASE_DIR = pathlib.Path(__file__).parent.parent.resolve()
HOME_PATH = os.path.join(BASE_DIR, 'home')
STATIC_PATH = os.path.join(BASE_DIR, 'static')
CONFIG_FILE = 'config_win.json'


def coach(request):
    lang = "en"
    langqueryset = MasterCoachLabels.objects.filter().values('keydata', lang)
    dict = {}
    miscSet=MasterLabels.objects.filter(keydata__in=['submit','prev','next','whoisfilling']).values('keydata', lang)
    for item in langqueryset:
        dict[item['keydata']] = item[lang]
    
    for item in miscSet:
        dict[item['keydata']] = item[lang]
    return render(request, 'coach/coach.html', dict)


def academypreview(request):
    context = {}
    lang="en"
    langqueryset = MasterCoachLabels.objects.filter(keydata__in=['review_before_submit']).values('keydata', lang)
    for item in langqueryset:
        context[item['keydata']] = item[lang]
    return render(request, 'coach/academypreview.html', context)

def addplayer(request):
    lang="en"
    # miscSet=MasterLabels.objects.filter(keydata__in=['male','female']).values('keydata', lang)
    context = {}
    return render(request, 'coach/addplayer.html', context)

def addcoach(request):
    if(request.method == 'POST'):
        try:
            coachdata=request.POST
            coachmodel=CoachModel(
                coach_name=coachdata['coach_name'],
                coach_email=coachdata['coach_email'],
                coach_mobile=coachdata['coach_mobile'],
                academy_name=coachdata['academy_name'],
                academy_email=coachdata['academy_email'],
                academy_mobile=coachdata['academy_mobile'],
                tournament_city=MasterCity.objects.get(id=coachdata['tournament_city']),
                tournament_state=MasterState.objects.get(id=coachdata['tournament_state']),
            )
            coachmodel.save()
            coach_id="IKFCOA"+coachmodel.tournament_city.city[:3].upper()+coachmodel.tournament_state.name[:3].upper()+f"{coachmodel.id:04d}"
            barcode_url=generatebarcode(coach_id)
            coachmodel.barcode_url=barcode_url
            coachmodel.coach_id=coach_id
            coachmodel.save(update_fields=['coach_id','barcode_url'])
            errorResponse = JsonResponse({"success": "true","message": "Saved Successfully","coach_id":coach_id})
            errorResponse.status_code = 200
            return errorResponse
        except IntegrityError as e:
            errorResponse = {'success': 'false','message': 'Uncessfull'}
            if(e.args[1].find("coach_mobile")):
                errorResponse["message"] = "Coach Mobile Number Already Exists"
            elif(e.args[1].find("coach_id")):
                errorResponse["message"] = "Coach Already Exists!"
            else:
                errorResponse["message"] = "An Error Occurred"
            errorResponse=JsonResponse(errorResponse)
            errorResponse.status_code = 403
        except:
            errorResponse = {'success': 'false','message': 'An Error Occured'}
            errorResponse=JsonResponse(errorResponse)
            errorResponse.status_code = 404
        return errorResponse


def admitcard(request):
    coach_data = {}
    if request.method=='POST':
        try:
            coach_id=request.POST['id']
            coachModel=CoachModel.objects.get(coach_id=coach_id)
            coach_data['coach_id']=coachModel.coach_id
            coach_data['coach_name']=coachModel.coach_name
            coach_data['coach_email']=coachModel.coach_email
            coach_data['coach_mobile']=coachModel.coach_mobile
            coach_data['academy_name']=coachModel.academy_name
            coach_data['academy_email']=coachModel.academy_email
            coach_data['academy_mobile']=coachModel.academy_mobile
            coach_data['tournament_city']=coachModel.tournament_city.city
            coach_data['tournament_state']=coachModel.tournament_state.name
            coach_data['id']=coachModel.id
            coach_data['barcode_url']=coachModel.barcode_url

            lang="en"
            langqueryset = MasterCoachLabels.objects.filter(keydata__in=['timer_text']).values('keydata', lang)
            for item in langqueryset:
                coach_data[item['keydata']] = item[lang]
            return HttpResponse(json.dumps(coach_data))
        except:
            return HttpResponseBadRequest()
        
    return render(request, 'coach/admitcard.html',coach_data)

def generatebarcode(coach_id):
    hr= barcode.get_barcode_class('code128')
    Hr=hr(str(coach_id), writer=ImageWriter())
    Hr.save('media/coach/barcode/'+coach_id)
    barcode_url='media/coach/barcode/'+coach_id+'.png'
    to_be_resized = Image.open(barcode_url)
    newSize = (270, 90)
    resized = to_be_resized.resize(newSize, resample=PIL.Image.NEAREST) 
    resized.save(barcode_url)
    return barcode_url


def coachplayer(request):
    if(request.method=="GET"):
        players =[]
        coach_id=request.GET.get('coach_id')
        try:
            fetched_players=Scout.objects.filter(Q(coach_id=coach_id)).filter(Q(status='failed')|Q(status=None)).values()
            for player in fetched_players:
                singleplayer={}
                singleplayer['ikfuniqueid']=player["ikfuniqueid"]
                singleplayer['gender']=player["gender"]
                singleplayer['first_name']=player["first_name"]
                singleplayer['last_name']=player["last_name"]
                singleplayer['dob']=player["dob"]
                singleplayer['coach_id']=player["coach_id"]
                singleplayer["primary_position"]=player["primary_position_id"]
                singleplayer["secondary_position"]=player["secondary_position_id"]
                singleplayer["mobile"]=player["mobile"]
                singleplayer["document_id_selected"]=player["document_id_selected_id"]
                players.append(singleplayer)
        except Scout.DoesNotExist:
            print("does not exist")
        return JsonResponse(players,safe=False)

    elif(request.method=="POST"):
        try:
            coach_id=request.POST["coach_id"]
            coachmodel=CoachModel.objects.get(coach_id=coach_id)
            coach_data={}
            coach_data['coach_id']=coachmodel.coach_id
            coach_data['tournament_city']=coachmodel.tournament_city
            coach_data['tournament_state']=coachmodel.tournament_state

            playerdata=request.POST
            gender=playerdata["Gender"]
            dob=playerdata["D.O.B"]
            datagroup = MasterGroup.objects.filter(gender=gender, include=True, start__lte=dob, end__gte=dob)
            playermodel=Scout(
                first_name=playerdata['First Name'],
                last_name=playerdata['Last Name'],
                dob=playerdata['D.O.B'],
                gender=playerdata["Gender"],
                coach_id=playerdata['coach_id'],
                tournament_city=coach_data['tournament_city'],
                tournament_state=coach_data['tournament_state'],
                primary_position=MasterPosition.objects.get(id=playerdata['Primary Position']),
                secondary_position=MasterPosition.objects.get(id=playerdata['Secondary Position']),
                mobile=playerdata['Phone No.'],
                document_id_selected=MasterDocument.objects.get(id=playerdata['Document Type']),
                group=datagroup[0],
                season=MasterSeason.objects.get(id="S02"),
                category=MasterCategory.objects.get(id="C"),
            )
            playermodel.save()
            id=playermodel.id
            playermodel.ikfuniqueid="IKF-S02"+coach_data["tournament_state"].name[:3].upper()+coach_data['tournament_city'].city[:3].upper()+f"{id:04d}"

            player_image_url='media/images/'+playermodel.ikfuniqueid+'.png'
            base64ToImage(playerdata['player_image'],player_image_url)
            
            player_document_url='media/documents/'+playermodel.ikfuniqueid+'.png'
            base64ToImage(playerdata['player_document'],player_document_url)

            playermodel.playeruploadid=playermodel.ikfuniqueid
            playermodel.whoisfilling=MasterRoles.objects.get(id='Coach')
            playermodel.pic_file=player_image_url
            playermodel.document_id_file=player_document_url
            playermodel.save(update_fields=['ikfuniqueid','playeruploadid','whoisfilling','pic_file','document_id_file'])
            errorResponse = JsonResponse({"success": "true","message": "Saved Successfully","id":playermodel.ikfuniqueid})
            errorResponse.status_code = 200
            return errorResponse
        except IntegrityError as e:
            errorResponse={'success': 'false','message': 'Uncessfull'}
            print(errorResponse)
            return JsonResponse(errorResponse)
    elif request.method=="DELETE":
        try:
            player_id=request.GET['id']
            playermodel=Scout.objects.get(ikfuniqueid=player_id)
            pic_url=str(playermodel.pic_file)
            doc_url=str(playermodel.document_id_file)
            playermodel.delete()
            if pic_url !="":
                os.remove(pic_url)
            if doc_url !="":
                os.remove(doc_url)
            errorResponse = JsonResponse({"success": "true","message": "Deleted Successfully"})
            errorResponse.status_code = 200
            return errorResponse
        except Exception as e:
            errorResponse = JsonResponse({"success": "false","message": "Uncessfull"})
            errorResponse.status_code = 400
            return errorResponse
    elif request.method=="PUT":
        try:
            new_player_data=json.loads(request.body)
            playermodel=Scout.objects.get(ikfuniqueid=new_player_data['id'])
            playermodel.first_name=new_player_data['First Name']
            playermodel.last_name=new_player_data['Last Name']
            playermodel.dob=new_player_data['D.O.B']
            playermodel.gender=new_player_data["Gender"]
            playermodel.mobile=new_player_data["Phone No."]
            playermodel.primary_position=MasterPosition.objects.get(id=new_player_data['Primary Position'])
            playermodel.secondary_position=MasterPosition.objects.get(id=new_player_data['Secondary Position'])
            playermodel.document_id_selected=MasterDocument.objects.get(id=new_player_data['Document Type'])
            playermodel.save()

            player_image_url='media/images/'+playermodel.ikfuniqueid+'.png'
            base64ToImage(new_player_data['player_image'],player_image_url)
            
            player_document_url='media/documents/'+playermodel.ikfuniqueid+'.png'
            base64ToImage(new_player_data['player_document'],player_document_url)

            errorResponse = JsonResponse({"success": "true","message": "Updated Successfully"})
            errorResponse.status_code = 200
            return errorResponse
        except Exception as e:
            errorResponse = JsonResponse({"success": "false","message": "Uncessfull"})
            errorResponse.status_code = 400
            return errorResponse

def base64ToImage(base64_string, file_name):
    if os.path.exists(file_name):
        os.remove(file_name)
    with open(file_name, 'wb') as f:
        if base64_string not in ['', 'null']:
            f.write(base64.b64decode(base64_string))


def checkAge(request):
    if request.method=="POST":
        try:
            coach_id=request.POST["coach_id"]
            coachmodel=CoachModel.objects.get(coach_id=coach_id)
            coach_data={}
            coach_data['coach_id']=coachmodel.coach_id
            coach_data['tournament_city']=coachmodel.tournament_city
            coach_data['tournament_state']=coachmodel.tournament_state
            playerdata=request.POST
            gender=playerdata["gender"]
            dob=playerdata["dob"]
            datagroup = MasterGroup.objects.filter(gender=gender, include=True, start__lte=dob, end__gte=dob).values()
            if datagroup:
                datacity = MasterGroupCity.objects.filter(cityid_id=coach_data['tournament_city'], groupid_id=datagroup[0]['id']).values()
                if(datacity):
                    print('this is datacity')
                else:
                    errorResponse = JsonResponse({"success": "false","message": "Age criteria not available for this city and gender"})
                    errorResponse.status_code = 404
                    return errorResponse
            else:
                errorResponse = JsonResponse({"success": "false","message": "Age criteria not available for this city and gender"})
                errorResponse.status_code = 404
                return errorResponse
            
            success=JsonResponse({"success":True,"message":"criteria OK"})
            success.status_code=200
            return success
        except:
            error= JsonResponse({"success":False,"message":"Age criteria not available for this city and gender"})
            error.status_code=404
            return error

