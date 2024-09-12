#coding: utf8
import os
from django.utils import timezone
import shutil
import json
import glob
import subprocess
import time
from uuid import uuid1
import PIL
from django.db.models import Q
from django.core import serializers
from django.core.paginator import Paginator
import razorpay
import datetime
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse, Http404, JsonResponse
import requests
import threading

from django.views.static import serve

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

import pathlib
from django.db import transaction

from registration.modelhome import SocialMediaLink
from .models import ScoutCourseDiscount, ScoutCourse,MasterAmount, MasterCategory, MasterColumn, MasterDateLimit, MasterDocument, MasterGroup, MasterGroupCity, MasterLabels, MasterPartner, MasterRoles, MasterSeason, MasterState, MasterCity, MasterPosition, Scout, Upload, Uploadfile
from .forms import UploadForm, UploadfileForm

from django.db import IntegrityError
from django.views.decorators.cache import cache_control

import qrcode
from PIL import Image
from datetime import datetime
from barcode.writer import ImageWriter
import barcode
import oss2

OSS_ACCESS_KEY_ID = "LTAI5tJoy1BhmrzS6vWDM73F"
OSS_ACCESS_KEY_SECRET = "WUEAB6baG5LI17dLy3vkGfAi9pVwlS"
OSS_BUCKET_NAME = "ikfseason2"
OSS_BUCKET_ACL = "public-read"  # private, public-read, public-read-write

# # Refer https://www.alibabacloud.com/help/zh/doc-detail/31837.htm about endpoint
OSS_ENDPOINT = "oss-ap-south-1.aliyuncs.com"

def amount(request):
    if request.method == "POST":
        datastr = request.POST.getlist('course')[0]
        data = json.loads(datastr)
        #printdata)
        #printdata['city'])
        amount = MasterAmount.objects.filter(course=data['course']).values()
        
        amount_value=amount[0]["amount"]

        return HttpResponse(amount_value)

def send_whatsapp_public_message(mobilenumber,firstname,lastname,obj):
    url = 'https://api.interakt.ai/v1/public/message/'
    api_key = 'aWZNYkJ4UWFBTG5nUTZZVHdDTndLQ0ViZTV4d1o4cHBiNGdGV1Joc01SNDo='
    print('mobilenumber')
    print(mobilenumber)
    headers = {
        'Authorization': f'Basic {api_key}',
        'Content-Type': 'application/json'
    }
    payload = {
        'countryCode': '+91',
        'phoneNumber': mobilenumber,
        'callbackData': 'Succesfully sent Message',
        'type': 'Template',
        'template': {
            'name': 'scouting_certification_2024',
            'languageCode': 'en',
            'headerValues': [
                
            ],
            'bodyValues': [
                firstname
          
                
            ]
        }
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code >= 200 and response.status_code < 300:
            # The request was successful, do something here
            print("Public message API request was successful!")
            obj.whatsapp_sent=True
            obj.save()
        else:
            # The request failed, handle the error here
            print(f"Public message API request failed with status code {response.status_code}")
            print(response.content)

    except Exception as e:
        print(e)
        return None
    
def interakt_add_user(mobilenumber,firstname,lastname,obj):
    # city=MasterCity.objects.get(id=obj.tournament_city_id).city
   
    # primary_position=MasterPosition.objects.get(id=obj.primary_position_id).label
    # secondary_position=MasterPosition.objects.get(id=obj.secondary_position_id).label
    
    url = 'https://api.interakt.ai/v1/public/track/users/'
    api_key = 'aWZNYkJ4UWFBTG5nUTZZVHdDTndLQ0ViZTV4d1o4cHBiNGdGV1Joc01SNDo='
    print('mobilenumber')
    print(mobilenumber)
    headers = {
        'Authorization': f'Basic {api_key}',
        'Content-Type': 'application/json'
    }
    payload = {
    "userId": obj.ikfuniqueid,
    "phoneNumber": mobilenumber,
    "countryCode": "+91",
    "traits": {

        "first_name": obj.first_name,
        "last_name":obj.last_name,
        "gender":obj.gender,
        "email": obj.email,
        
        "contact_number":obj.mobile,

       

    },
    "tags": ["Scout4"]
}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code >= 200 and response.status_code < 300:
            # The request was successful, do something here
            print("add track API request was successful!")
            obj.player_added_interakt=True
            obj.save()
        else:
            # The request failed, handle the error here
            print(f"Add track API request failed with status code {response.status_code}")
            print(response.content)

    except Exception as e:
        print(e)
        return None
def order(request):
    if request.method == "POST":
        ikfuniqueid = request.POST.getlist('ikfuniqueid')[0]
        id=request.POST.getlist('id')[0]
        # print(request.POST.getlist('amount'))
        amountinput=int(request.POST.getlist('amount')[0])
        amount = amountinput*100
        # data['city']
        # data['season']
        # data['category']
        # data['']
        playerdata = Scout

        client = razorpay.Client(
            auth=("rzp_live_KlzrczXDhMbptD", "VVQDQYdjlQp7LM2f9mouLOwK"))
        DATA = {
            "amount": amount,
            "currency": "INR",
            "receipt": ikfuniqueid,
            "notes": {"id": id, "key2": "value2d"
                      }}
        response = client.order.create(data=DATA)
        #printresponse)
        if response:
                try:
                    obj = Scout.objects.get(
                         ikfuniqueid=ikfuniqueid,
                         id=id
                    )
                    obj.order_id=response["id"]

                    obj.save()
                    errordict = {"error": "false",
                                "message": "order generated successfully", "order_id":response["id"],"ikfuniqueid": obj.ikfuniqueid ,"id":obj.id }
                    return HttpResponse(json.dumps(errordict))
                except Scout.DoesNotExist:
                    errordict = {"error": "true",
                                "message": "erro in order id"}
                    return HttpResponse(json.dumps(errordict))


        js_state = json.dumps(response)
        return HttpResponse(js_state)


@cache_control(no_cache=True, must_revalidate=True)
def paymentfun(request):
    lang = "en"
    langqueryset = MasterLabels.objects.filter().values('keydata', lang)
    dict = {}
    for item in langqueryset:
        dict[item['keydata']] = item[lang]

    return render(request, 'player/payment.html', dict)

# with transaction.atomic():
#     for i, row in df.iterrows():
#         mv = MeasureValue.objects.get(org=row.org, month=month)

#         if (row.percentile is None) or np.isnan(row.percentile):
#             # if it's already None, why set it to None?
#             row.percentile = None

#         mv.percentile = row.percentile
#         mv.save()
# @transaction.atomic
# def viewfunc(request):
#     create_parent()

#     try:
#         with transaction.atomic():
#             generate_relationships()
#     except IntegrityError:
#         handle_exception()


#     add_children()
BASE_DIR = pathlib.Path(__file__).parent.parent.resolve()
HOME_PATH = os.path.join(BASE_DIR, 'home')
STATIC_PATH = os.path.join(BASE_DIR, 'static')
CONFIG_FILE = 'config_win.json'


def homeindex(request):
    lang = "en"
    langqueryset = MasterLabels.objects.filter().values('keydata', lang)
    dict = {

    }
    socialMediaLink = SocialMediaLink.objects.filter(
        include=1, type_of_link="social").values('icon', 'url', 'name',)
    website = SocialMediaLink.objects.filter(
        include=1, type_of_link="website").values('icon', 'url', 'name',)
    phone = SocialMediaLink.objects.filter(
        include=1, type_of_link="phone").values('icon', 'url', 'name',)

    # for notice board
    # noticeBoard = NoticeBoard.objects.filter(include=1).values(
    #     'title', 'description', 'isHeading', 'include',)
    for item in langqueryset:
        dict[item['keydata']] = item[lang]

    dict['social_links'] = socialMediaLink
    dict['website_links'] = website
    dict['phone_links'] = phone
    dict['notice_board'] = ""
    dict['code']=request.GET.get('code')
    #printnoticeBoard)
    return render(request, 'index.html', dict)


def category(request, lang):

    langqueryset = MasterLabels.objects.filter().values('keydata', lang)
    dict = {}
    for item in langqueryset:
        dict[item['keydata']] = item[lang]
    masterroles = MasterRoles.objects.filter(include=1).values()
    dict['masterroles'] = masterroles

    return render(request, 'category.html', dict)


def scoutpage(request, lang, category):
    context = {}

    langqueryset = MasterLabels.objects.filter().values('keydata', lang)
    dict = {}

    for item in langqueryset:
        dict[item['keydata']] = item[lang]
    if(category == "Coach"):
        dict["coach_or_player"] = "Coach"
        return redirect('/coach/', dict)

    else:
        dict["coach_or_player"] = "Scout"
        dict['playeruploadid'] = uuid1()
        return render(request, 'player/scout.html', dict)


def main(request):
    context = {}
    lang = "en"
    langqueryset = MasterLabels.objects.filter().values('keydata', lang)
    dict = {}
    for item in langqueryset:
        dict[item['keydata']] = item[lang]
    #printuuid1())
    dict['playeruploadid'] = uuid1()
    
    if is_ajax(request=request):
        form = UploadForm(request.POST, request.FILES)

        if form.is_valid():

            form.save()

            return JsonResponse({'message': "yes"})

    else:
        form = UploadForm()
        dict["uploadform"]=form
        return render(request, 'player/main.html', dict)


def preview1(request):

    lang = "en"
    langqueryset = MasterLabels.objects.filter().values('keydata', lang)

    mycolumns = MasterColumn.objects.filter(includep1=1).values(
        'columnid', 'label_key', 'type', 'orderid')
    dict = {

    }

    for item in langqueryset:
        dict[item['keydata']] = item[lang]
    arrayfordict = []

    for item in mycolumns:
        item['label'] = dict[item['label_key']]

    dict['formikf'] = mycolumns

    dict['preview_type'] = "preview1"
    dict['url_prev'] = "scoutpage"
    dict['url_prev_para'] = "Scout"
    dict['url_next'] = "main"
    dict['button_text'] = "Next"

    return render(request, 'player/preview.html', dict)


@cache_control(no_cache=True, must_revalidate=True)
def preview2(request):

    #
    imageid = "d83f5a87-dfdb-11ec-a390-b42e990d79d6"
    lang = "en"
    langqueryset = MasterLabels.objects.filter().values('keydata', lang)

    mycolumns = MasterColumn.objects.filter(includep2=1).values(
        'columnid', 'label_key', 'type', 'orderid')

    dict = {

    }

    for item in langqueryset:
        dict[item['keydata']] = item[lang]
    for item in mycolumns:
        item['label'] = dict[item['label_key']]
    dict['formikf'] = mycolumns
    dict['url_prev'] = "uploaddoc"
    dict['preview_type'] = "preview2"
    dict['url_next'] = "main"
    dict['button_text'] = "Save"


    return render(request, 'player/preview.html', dict)

def viewpic(request):
    dict={}
    if request.method=="POST":
        
        
        imageid = request.POST.getlist('playeruploadidfinal')[0]
        
        if(imageid):
            print("Image id")
            print(imageid)
            myupload = Upload.objects.filter(unique=imageid).order_by("-id")[0]
            dict['myupload']=myupload
            #printmyupload.image.url)
            return HttpResponse(myupload.image.url)

        else:
            dict['myupload'] = ""
            return HttpResponse("")
            
    else:
        dict['myupload'] = ""
        return HttpResponse("")
        
def viewdoc(request):
    dict={}
    if request.method=="POST":
        
        
        imageid = request.POST.getlist('playeruploadidfinal')[0]
        if(imageid):
            myupload = Uploadfile.objects.filter(unique=imageid).order_by("-id")[0]
            dict['myupload']=myupload
            
            return HttpResponse(myupload.file.url)

        else:
            dict['myupload'] = ""
            return HttpResponse("")
            
    else:
        dict['myupload'] = ""
        return HttpResponse("")


def viewdocpic(request):
    dict={}
    if request.method=="POST":
        
        
        imageid = request.POST.getlist('playeruploadidfinal')[0]
        if(imageid):
            myupload = Upload.objects.filter(unique=imageid).order_by("-id")[0]
            myuploadfile = Uploadfile.objects.filter(unique=imageid).order_by("-id")[0]
            if(myupload and myuploadfile):
                dict['pic']=myupload.image.url
                dict['doc']=myuploadfile.file.url
                return JsonResponse(dict)
            elif(myupload):
                dict['pic']=myupload.image.url
                dict['doc']=""
                return JsonResponse(dict)
            elif(myuploadfile):
                dict['pic']=""
                dict['doc']=myuploadfile.file.url
                return JsonResponse(dict)
            else:
                return JsonResponse({})



        else:
            dict['myupload'] = ""
            return JsonResponse({})
            
    else:
        dict['myupload'] = ""
        return HttpResponse("")

def printpdf(request):
    if request.method=="GET":
        context = {}
        lang = "en"
        langqueryset = MasterLabels.objects.filter().values('keydata', lang)
        dict = {}
        for item in langqueryset:
            dict[item['keydata']] = item[lang]
        return render(request, 'player/printpdf.html', dict)
def paymentfail(request):
    if request.method=="GET":
        context = {}
        lang = "en"
        langqueryset = MasterLabels.objects.filter().values('keydata', lang)
        dict = {}
        for item in langqueryset:
            dict[item['keydata']] = item[lang]
        return render(request, 'player/paymentfail.html', dict)    

def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

def handle_uploaded_file(f):
    print(f.name)
    
    auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
    bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)
    headers=dict()
    # headers["x-oss-storage-class"] = "Standard"
    # headers["x-oss-object-acl"] = oss2.OBJECT_ACL_PUBLIC_READ
    # headers['x-oss-process']="image/resize,w_300,h_300"
    headers['x-oss-forbid-overwrite']="false"
    f.seek(1000, os.SEEK_SET)
    filename="images/" +f.name
    result=bucket.put_object(filename,f,headers=headers)
    print(result)
    # f.seek(1000, os.SEEK_SET)
    # current = f.tell()
    # for chunk in f.chunks():
    #     result= 
    #     print(result)   
     
    
    
# with open('D:\\localpath\\examplefile.txt', 'rb') as fileobj:
#     # Use the seek method to read data from byte 1000 of the file. The data is uploaded from byte 1000 to the last byte of the local file. 
    # f.seek(1000, os.SEEK_SET)
    # # Use the tell method to obtain the current position. 
    # current = f.tell()
#     print(auth)
    # with open(f, 'wb+') as destination:
    #     for chunk in f.chunks():
    #         destination.write(chunk)
def uploaddoc(request):
    lang = "en"
    langqueryset = MasterLabels.objects.filter().values('keydata', lang)
    dict = {}
    for item in langqueryset:
        dict[item['keydata']] = item[lang]

    if is_ajax(request=request):
        form = UploadfileForm(request.POST, request.FILES)

        if form.is_valid():
            #handle_uploaded_file(request.FILES['file'])
            form.save()

            return JsonResponse({'message': "yes"})

    else:
        form = UploadfileForm()
        dict["uploadfileform"] = form
        return render(request, 'player/uploaddoc.html', dict)


def uploadpic(request):
    lang = "en"
    langqueryset = MasterLabels.objects.filter().values('keydata', lang)
    dict = {}
    for item in langqueryset:
        dict[item['keydata']] = item[lang]

    if is_ajax(request=request):
        form = UploadForm(request.POST, request.FILES)

        if form.is_valid():

            form.save()

            return JsonResponse({'message': "yes"})

    else:
        form = UploadForm()
        dict["uploadform"]=form
        return render(request, 'player/uploadpic.html', dict)






def statedata(request):
    if request.method == 'POST':
        #      try:

        #     F.objects.filter().update(status='P')
        #     F.objects.filter(file=filename).update(status='C')
        include = request.POST.getlist('include')[0]
        if(include == "3" or include == 3):
            state = MasterState.objects.filter()
        else:
            state = MasterState.objects.filter(include=include)
        statevalue = state.values()
        #printstatevalue)
        arrayobj = []

        for state in statevalue:
            newstate = {}
            newstate['value'] = state['name']
            newstate['id'] = state['id']
            arrayobj.append(newstate)
        
        js_state = json.dumps(arrayobj)
        return HttpResponse(js_state)

    #           # If get() throws an error you need to handle it.
    #           # You can use either the generic ObjectDoesNotExist or
    #           # <model>.DoesNotExist which inherits from
    #           # django.core.exceptions.ObjectDoesNotExist, so you can target multiple
    #           # DoesNotExist exceptions
    #      except MasterState.DoesNotExist: # or the generic "except ObjectDoesNotExist:"
    #            #print"State Does Not Exist")
    #            return HttpResponse({})


def citydata(request):
    if request.method == 'POST':
        state = request.POST.getlist('state')[0]
        #printstate)
    #      try:

    #     F.objects.filter().update(status='P')
    #     F.objects.filter(file=filename).update(status='C')
        city = MasterCity.objects.filter(include=1, state_id=state)
        cityvalue = city.values()

        arrayobj = []

        for cityitem in cityvalue:
            newcity = {}
            newcity['value'] = cityitem['city']
            newcity['id'] = cityitem['id']
            arrayobj.append(newcity)

        js_city = json.dumps(arrayobj)
        return HttpResponse(js_city)

    #           # If get() throws an error you need to handle it.
    #           # You can use either the generic ObjectDoesNotExist or
    #           # <model>.DoesNotExist which inherits from
    #           # django.core.exceptions.ObjectDoesNotExist, so you can target multiple
    #           # DoesNotExist exceptions
    #      except MasterState.DoesNotExist: # or the generic "except ObjectDoesNotExist:"
    #            #print"State Does Not Exist")
    #            return HttpResponse({})


def positiondata(request):
    if request.method == 'POST':

        positions = MasterPosition.objects.filter()
        positionvalue = positions.values()
        #printpositionvalue)
        arrayobj = []

        for position in positionvalue:
            newstate = {}
            newstate['value'] = position['label']
            newstate['id'] = position['id']
            arrayobj.append(newstate)

        js_state = json.dumps(arrayobj)
        return HttpResponse(js_state)


def documentdata(request):
    if request.method == 'POST':

        positions = MasterDocument.objects.filter(include=1)
        positionvalue = positions.values()
        #printpositionvalue)
        arrayobj = []
        lang = 'en'
        for position in positionvalue:
            newstate = {}
            newstate['value'] = position[lang]
            newstate['id'] = position['id']
            arrayobj.append(newstate)

        js_state = json.dumps(arrayobj)
        return HttpResponse(js_state)




def save(request):
    if request.method == 'POST':
        datastr = request.POST.getlist('data')[0]
        dictdata = json.loads(datastr)

        # #printdictdata)
        context = {}
        # data_id_selected_data=dictdata['document_id_selected']
        # if(data_id_selected_data=="" or data_id_selected_data== None or data_id_selected_data=="undefined" or data_id_selected_data=="NA" ):
        #     data_selected=None
        # else:
        #     data_selected= MasterDocument.objects.get(id=data_id_selected_data)
        


        print("first_name") 
        print(dictdata['extrafield1'])

        scout = Scout(
            first_name=dictdata['first_name'],
            last_name=dictdata['last_name'],


            gender=dictdata['gender'],
            playeruploadid=dictdata['playeruploadid'],
            pan=dictdata['pan'],
            



            mobile=dictdata['mobile'],

            email=dictdata['email'],
            dob=dictdata['dob'],
            extrafield1=dictdata['extrafield1'],

            course=ScoutCourse.objects.get(id=dictdata['course']),
            associated_years = dictdata['associated_years'],
            associated_as = dictdata['associated_as'],
            
            referral = dictdata['referral'],
            discount = dictdata['discount'],




 
            season=MasterSeason.objects.get(id=dictdata['season']),

        )

        try:
            scout.save()
            try:
                obj = Scout.objects.get(


                    
                    dob=dictdata['dob'],
                    mobile=dictdata['mobile'],
                    playeruploadid=dictdata['playeruploadid'],

                )


                # category=MasterCategory.objects.get(id=obj.category).id
                gender = obj.gender[0:1]
                number = f'{obj.id:06}'

                obj.ikfuniqueid = "IKF" + obj.season.id + gender + number
                obj.save() 

                errordict = {"error": "false",
                             "message": "Saved Successfully", "ikfuniqueid": obj.ikfuniqueid ,"id":obj.id,
                             "first_name":obj.first_name, "last_name":obj.last_name,
                             "course":obj.course_id,"associated_years":obj.associated_years ,"associated_as":obj.associated_as ,
                             "referral":obj.referral ,"discount":obj.discount ,"email":obj.email ,"mobile":obj.mobile ,
                             "gender":obj.gender ,"playeruploadid":obj.playeruploadid,"pan":obj.pan,"extrafield1":obj.extrafield1,
                             }
                             
                return HttpResponse(json.dumps(errordict))
            except Scout.DoesNotExist:
                errordict = {"error": "true",
                             "message": "Scout does not exist"}
                return HttpResponse(json.dumps(errordict))

        except IntegrityError as e:
            #printe)

            errordict = {"error": "true", "message": str(e)}
            #printjson.dumps(errordict))
            return HttpResponse(json.dumps(errordict))


def converter(request):
    if request.method == 'POST':
        inputid = request.POST.getlist('id')[0]
        if(inputid=="" or inputid=="undefined" or inputid=="NA"):
            inputid=None
        inputtype = request.POST.getlist('type')[0]
        if(inputtype == "state" or inputtype == "state_id" or  inputtype == "state" or inputtype == "state_id"):
            input = MasterState.objects.filter(id=inputid)
            namevar = 'name'
            inputvalue = input.values()
            arrayobj = []

            for inpu in inputvalue:
                output = {}
                output['label'] = inpu[namevar]

                arrayobj.append(output)
            js_state = json.dumps(arrayobj)
            return HttpResponse(js_state)

        elif(inputtype == "city" or inputtype == "city_id"):
            input = MasterCity.objects.filter(id=inputid)
            namevar = 'city'
            inputvalue = input.values()
            arrayobj = []

            for inpu in inputvalue:
                output = {}
                output['label'] = inpu[namevar]

                arrayobj.append(output)
            js_state = json.dumps(arrayobj)
            return HttpResponse(js_state)
        elif(inputtype == "primary_position" or inputtype == "primary_position_id" or inputtype == "secondary_position" or inputtype == "secondary_position_id"):
            input = MasterPosition.objects.filter(id=inputid)
            namevar = 'label'
            inputvalue = input.values()

            arrayobj = []

            for inpu in inputvalue:
                output = {}
                output['label'] = inpu[namevar]

                arrayobj.append(output)
            js_state = json.dumps(arrayobj)
            return HttpResponse(js_state)
        elif(inputtype == "document_id_selected_id" or inputtype=="document_id_selected"):
            #print'document input id',inputid)
            input = MasterDocument.objects.filter(id=inputid)
            lang = "en"
            namevar = lang
            inputvalue = input.values()
            arrayobj = []

            for inpu in inputvalue:
                output = {}
                output['label'] = inpu[namevar]

                arrayobj.append(output)
            js_state = json.dumps(arrayobj)
            return HttpResponse(js_state)


def mygroup(request):
    if request.method == 'POST':
        gender = request.POST.getlist('gender')[0]
        dob = request.POST.getlist('dob')[0]
        city = request.POST.getlist('city')[0]
        #printdob)
        # datedob=datetime.datetime(dob)
        include = request.POST.getlist('include')[0]

        datagroup = MasterGroup.objects.filter(
            gender=gender, include=include, start__lte=dob, end__gte=dob).values()
        if(datagroup):
            #print"group id :")
            #printdatagroup[0]['id'])
            #print"city id")
            #printcity)
            datacity = MasterGroupCity.objects.filter(
                cityid_id=city, groupid_id=datagroup[0]['id']).values()
            #printdatacity)
            if(datacity):
                context = {
                    "present": "1",
                    "id": datagroup[0]['id'],
                    "group": datagroup[0]['group'],

                    "gender": datagroup[0]['gender'],
                    "start": datagroup[0]['start'].strftime("%d %b %Y "),
                    "end": datagroup[0]['end'].strftime("%d %b %Y ")
                }
                js_state = json.dumps(context)
                return HttpResponse(js_state)
            else:
                context = {
                    "present": "0",
                    "text_code": "error_code"
                }

                js_state = json.dumps(context)
                return HttpResponse(js_state)
        else:
            context = {
                "present": "0",
                "text_code": "error_code"
            }
            js_state = json.dumps(context)
            return HttpResponse(js_state)


# FOR PLAYER DATA IN PRINT PDF

def playerdata(request):
    if request.method == 'POST':
        
        ikfid = request.POST.get('ikfuniqueid')
        playerdata = list(Scout.objects.filter(ikfuniqueid=ikfid).values())
        print(playerdata)
        generatebarcode(playerdata[0])
    return JsonResponse(playerdata[0], safe=False)

# For partner info

def partnerinfo(request):
    if request.method == 'POST':
        season = request.POST.get('season')
        city = request.POST.get('city')
        category = request.POST.get('category')
        partnerdata = list(MasterPartner.objects.filter(season=season,city=city,category=category).values())
        print(partnerdata)
    return JsonResponse(partnerdata[0], safe=False)

# To generate QR

def generateqrcode(data):
    # taking base width
    basewidth = 100
    QRcode = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H
    )
    
    # url = 'https://www.geeksforgeeks.org/'
    
    # adding URL or text to QRcode
    QRcode.add_data(data)
    
    # generating QR code
    QRcode.make()
    QRcolor = 'Green'
    
    # adding color to QR code
    QRimg = QRcode.make_image(
        fill_color=QRcolor, back_color="white").convert('RGB')
    QRimg.save(data[0]['playeruploadid']+'.png')
    
    #print'QR code generated!')


def generatebarcode(data):
    ikfuniqueid = data['ikfuniqueid']
    modifiedid=ikfuniqueid.replace("-","")
    hr= barcode.get_barcode_class('code128')
    Hr=hr(str(modifiedid), writer=ImageWriter())
    Hr.save('media/barcode/'+ikfuniqueid)
    to_be_resized = Image.open('media/barcode/'+ikfuniqueid+'.png')
    newSize = (270, 90)
    resized = to_be_resized.resize(newSize, resample=PIL.Image.NEAREST) 
    print(resized)
    resized.save('media/barcode/'+ikfuniqueid+'.png')

def paymentstatus(request):
    if request.method == 'POST':
        ikfuniqueid = request.POST.getlist('ikfuniqueid')[0]
        

        try:
            obj = Scout.objects.get(
                ikfuniqueid=ikfuniqueid,

                

            )
            #print"gettig data")
            obj.status=request.POST.getlist('status')[0]
            obj.razorpay_payment_id=request.POST.getlist('razorpay_payment_id')[0]
            obj.razorpay_order_id=request.POST.getlist('razorpay_order_id')[0]
            obj.razorpay_signature=request.POST.getlist('razorpay_signature')[0]
            #print"in between")
            obj.error_code=request.POST.getlist('error_code')[0]
            obj.error_description=request.POST.getlist('error_description')[0]
            obj.error_source=request.POST.getlist('error_source')[0]
            obj.error_reason=request.POST.getlist('error_reason')[0]
            obj.error_meta_order_id=request.POST.getlist('error_meta_order_id')[0]
            obj.error_meta_payment_id=request.POST.getlist('error_meta_payment_id')[0]
            obj.amount=request.POST.getlist('amount')[0]
            #print"setting data")

            obj.save()
            mobilenumber=""
            if obj.mobile:
               mobilenumber=obj.mobile


            t1 = threading.Thread(target=send_whatsapp_public_message,args=(mobilenumber,obj.first_name,obj.last_name,obj))
            
            t2 = threading.Thread(target=interakt_add_user,args=(mobilenumber,obj.first_name,obj.last_name,obj))
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            errordict = {"error": "false",
                            "message": "Payment didn't saved"}
            return HttpResponse(json.dumps(errordict))
        except Scout.DoesNotExist:
            errordict = {"error": "true",
                            "message": "Payment didn't saved"}
            return HttpResponse(json.dumps(errordict))


def limitdate(request):
    if request.method == 'POST':
        season = request.POST.getlist('season')[0]
        datevalue=list(MasterDateLimit.objects.filter(season=season).values())
        return JsonResponse(datevalue[0], safe=False)


def scoutdiscountamount(request):
    if request.method == 'POST':
        typeofdiscount = request.POST.getlist('type')[0]
        course = request.POST.getlist('course')[0]
        courseamount=list(ScoutCourse.objects.filter(id=course ).values())
        if (typeofdiscount == None or typeofdiscount == ""):
            newdict={}
            newdict['amount']=float(courseamount[0]['amount'])
            return JsonResponse(newdict, safe=False)
        else:
            scoutamount=list(ScoutCourseDiscount.objects.filter(type=typeofdiscount,course=course ).values())
            print(float(scoutamount[0]['discount']))
            print(float(courseamount[0]['amount']))
            newdict={}
            newdict['amount']=float(courseamount[0]['amount']) -float(scoutamount[0]['discount'])
            return JsonResponse(newdict, safe=False)



def update_scout_payment_status(request):
    # Define batch size (number of records to process at a time)
    batch_size = 30

    # Define the date filter (replace with your desired date or use a query parameter)
    cutoff_date = timezone.datetime(2024, 8, 18, tzinfo=timezone.get_current_timezone())  # Example: filter scouts after Jan 1, 2024

    # Get all scouts where payment status needs checking, excluding records with more than 3 attempts
    scouts_to_update = Scout.objects.filter(
         Q(status__in=["created", "attempted", '.','']) | Q(status__isnull=True),  # Include created, attempted, empty, and None statuses
         created_at__gte=cutoff_date,  # Add date filter
         order_id__isnull=False
    ).exclude(
        # Exclude scouts with more than 3 attempts by checking the value in Extrafield4
        Q(extrafield4__gte='3') 
    ).order_by("id")
    

    # Paginate the results to handle large numbers of rows
    paginator = Paginator(scouts_to_update, batch_size)
    # return HttpResponse(scouts_to_update.values("first_name","order_id","status"))
    
    # Get page number from query params (default to 1 if not provided)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    processed_count = 0
    
    for scout in page_obj:
        # Parse attempts from Extrafield4
        attempts = int(scout.extrafield4) if scout.extrafield4 and scout.extrafield4.isdigit() else 0

        # Call Razorpay API to check the payment status
        try:
            order_api_url = f"https://api.razorpay.com/v1/orders/{scout.order_id}"
            response = requests.get(order_api_url, auth=("rzp_live_KlzrczXDhMbptD", "VVQDQYdjlQp7LM2f9mouLOwK"))
            response.raise_for_status()  # Raise an exception for non-2xx responses
            order_status = response.json().get('status')

            if order_status in ["paid"]:
                scout.status = "success"

                # Trigger other APIs for successful payments
                t1 = threading.Thread(target=send_whatsapp_public_message,args=(scout.mobile, scout.first_name, scout.last_name, scout))
                
                t2 = threading.Thread(target=interakt_add_user,args=(scout.mobile, scout.first_name, scout.last_name, scout))
                t1.start()
                t2.start()
                t1.join()
                t2.join()

            else:
                scout.status = order_status

            # Update attempts in Extrafield4
            attempts += 1
            scout.extrafield4 = str(attempts)
            scout.save()  # Save updated scout record

            processed_count += 1

        except requests.RequestException as e:
            print(f"Error checking status for {scout.first_name}: {str(e)}")

    return JsonResponse({"message": "Batch processed", "processed_count": processed_count})

        




