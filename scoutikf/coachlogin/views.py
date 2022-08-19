#coding: utf8



import json
from django.core import serializers

from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse, Http404, JsonResponse

from django.views.static import serve

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from numpy import equal
import razorpay
from registration.coach_models import CoachModel, MasterCoachLabels



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

OSS_ACCESS_KEY_ID = "LTAI5tJoy1BhmrzS6vWDM73F"
OSS_ACCESS_KEY_SECRET = "WUEAB6baG5LI17dLy3vkGfAi9pVwlS"
OSS_BUCKET_NAME = "ikfseason2"
OSS_BUCKET_ACL = "public-read"  # private, public-read, public-read-write


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
    #print('this is coach login')
    return render(request, 'coachlogin.html', dict)

def verifylogin(request):
    if request.method == 'POST':
        coach_id = request.POST.get('coach_id')
        mobile = request.POST.get('mobile')
        #print(coach_id, mobile)
        coach=list(CoachModel.objects.filter(coach_id=coach_id,coach_mobile=mobile).values())
        if coach:
            dictdata=dict()
            dictdata['error']="false"
            dictdata['login']="success"
            dictdata['coach_id']=coach[0]['coach_id']
            dictdata['coach_name']=coach[0]['coach_name']
            dictdata['coach_mobile']=coach[0]['coach_mobile']
            dictdata['coach_email']=coach[0]['coach_email']
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

def coachdashboard(request):
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
    return render(request, 'addplayer.html', dict)

def coachdatalogin(request):
    if request.method == 'POST':
        
        ikfid = request.POST.get('coach_id')
        coachdata = list(Player.objects.filter(coach_id=ikfid).values())
        #print(coachdata)
        
    return JsonResponse(coachdata[0], safe=False)

def amount(request):
    if request.method == "POST":
        coach_id = request.POST['coach_id']

        player_list=list(Player.objects.filter(Q(coach_id=coach_id)).filter(Q(status='failed')|Q(status=None)).values())
        #print(player_list)
        amount=0
        for player in player_list:
            amount+=int(player['amount'])
        return HttpResponse(amount)



def order(request):
    if request.method == "POST":
        coach_id = request.POST.getlist('coach_id')[0]
        player_list=list(Player.objects.filter(Q(coach_id=coach_id)).filter(Q(status='failed')|Q(status=None)).values())
        # #print(request.POST.getlist('amount'))
        amount=0
        for player in player_list:
            obj=Player.objects.get(id=player['id'])
            entry_fee=int(MasterAmount.objects.filter(group=player['group_id'],city_id=player['tournament_city_id']).values()[0]['amount'])
            obj.amount=entry_fee
            obj.save(update_fields=['amount'])
            amount=amount+entry_fee
        # data['city']
        # data['season']
        # data['category']
        # data['']
        amount*=100
        client = razorpay.Client(
            auth=("rzp_test_ahDEPkxQSa6Ykb", "wtkc1kSruJq0bAjevDepqbjJ"))
        DATA = {
            "amount": amount,
            "currency": "INR",
            "receipt": coach_id,
            "notes": {"id": str(id), "key2": "value2d"
                      }}
        response = client.order.create(data=DATA)
        ##printresponse)
        if response:
                try:
                    for player in player_list:
                        obj=Player.objects.get(id=player['id'])
                        obj.order_id=response["id"]

                        obj.save()
                    errordict = {"error": "false",
                                "message": "order generated successfully", "order_id":response["id"]}
                    return HttpResponse(json.dumps(errordict))
                except Player.DoesNotExist:
                    errordict = {"error": "true",
                                "message": "erro in order id"}
                    return HttpResponse(json.dumps(errordict))
        
        js_state = json.dumps(response)
        return HttpResponse(js_state)


@cache_control(no_cache=True, must_revalidate=True)
def payment(request):
    lang = "en"
    langqueryset = MasterLabels.objects.filter().values('keydata', lang)
    dict = {}
    for item in langqueryset:
        dict[item['keydata']] = item[lang]

    return render(request, 'coach_payment.html', dict)


def paymentstatus(request):
    if request.method == 'POST':
        coach_id = request.POST.getlist('coach_id')[0]
        ##printikfuniqueid)
        ##printplayeruploadid)
        try:
            coach = CoachModel.objects.get(
                coach_id=coach_id),
            try:
                ##print"gettig data")
                player_list=list(Player.objects.filter(Q(coach_id=coach_id)).filter(Q(status='failed')|Q(status=None)).values())
                for player in player_list:
                    obj=Player.objects.get(id=player['id'])
                    obj.status=request.POST.getlist('status')[0]
                    obj.razorpay_payment_id=request.POST.getlist('razorpay_payment_id')[0]
                    obj.razorpay_order_id=request.POST.getlist('razorpay_order_id')[0]
                    obj.razorpay_signature=request.POST.getlist('razorpay_signature')[0]
                    ##print"in between")
                    obj.error_code=request.POST.getlist('error_code')[0]
                    obj.error_description=request.POST.getlist('error_description')[0]
                    obj.error_source=request.POST.getlist('error_source')[0]
                    obj.error_reason=request.POST.getlist('error_reason')[0]
                    obj.error_meta_order_id=request.POST.getlist('error_meta_order_id')[0]
                    obj.error_meta_payment_id=request.POST.getlist('error_meta_payment_id')[0]
                    obj.save()
                    payment=Payment(
                    ikfuniqueid=obj.ikfuniqueid,
                    playeruploadid=obj.playeruploadid,
                    status=request.POST.getlist('status')[0],
                    razorpay_payment_id=request.POST.getlist('razorpay_payment_id')[0],
                    razorpay_order_id=request.POST.getlist('razorpay_order_id')[0],
                    razorpay_signature=request.POST.getlist('razorpay_signature')[0],

                    error_code=request.POST.getlist('error_code')[0],
                    error_description=request.POST.getlist('error_description')[0],
                    error_source=request.POST.getlist('error_source')[0],
                    error_reason=request.POST.getlist('error_reason')[0],
                    error_meta_order_id=request.POST.getlist('error_meta_order_id')[0],
                    error_meta_payment_id=request.POST.getlist('error_meta_payment_id')[0],
                    amount=request.POST.getlist('amount')[0]
                    )
                    payment.save()
                errordict = {"error": "false",
                                "message": "Saved Successfully"}
                return HttpResponse(json.dumps(errordict))
            except:
                errordict = {"error": "true",
                                "message": "error in payment"}
                return HttpResponse(json.dumps(errordict))
        except CoachModel.DoesNotExist:
            errordict = {"error": "true",
                            "message": "Payment didn't saved"}
            return HttpResponse(json.dumps(errordict))


def reciept(request):
    lang="en"
    langqueryset = MasterCoachLabels.objects.filter(keydata__in=['pass_message','reciept_heading']).values('keydata', lang)
    message={}
    for item in langqueryset:
        message[item['keydata']] = item[lang]
    #print(message)
    if request.method == 'POST':
        #print(request.POST)
        coach_id=request.POST['coach_id']
        #print(coach_id,'coach_id')
        player_list=list(Player.objects.filter(coach_id=coach_id,status='success').values())
        dict_list=[]
        for player in player_list:
            dict={}
            dict['name']=player['first_name']+' '+player['last_name']
            dict['ikfuniqueid']=player['ikfuniqueid']
            dict['gender']=player['gender']
            dict['amount']=player['amount']
            dict['phone']=player['mobile']
            dict_list.append(dict)
        return JsonResponse(dict_list,safe=False)
    return render(request,'receipt.html',message)
    


def documentid(request):
    if request.method=="GET":
        try:
            doucuments=MasterDocument.objects.all()
            #print(doucuments)
            data={}
            for document in doucuments:
                data[document.id]=document.en
            #print(data)
            return JsonResponse(data,safe=False)
        except Exception as e:
            #print(e)
            errorResponse = JsonResponse({"success": "false","message": "Uncessfull"})
            errorResponse.status_code = 400
            return errorResponse

def getcity(request):
    if request.method=="POST":
        try:
            city_id=request.POST['city_id']
            city=MasterCity.objects.get(id=city_id).city
            #print(city)
            success=JsonResponse({"success": "true","city_name":city})
            success.status_code = 200
            return success
        except Exception as e:
            #print(e)
            errorResponse = JsonResponse({"success": "false","message": "Uncessfull"})
            errorResponse.status_code = 400
            return errorResponse

def getstate(request):
    if request.method=="POST":
        try:
            state_id=request.POST['state_id']
            state=MasterState.objects.get(id=state_id).name
            #print(state)
            success=JsonResponse({"success": "true","state_name":state})
            success.status_code = 200
            return success
        except Exception as e:
            #print(e)
            errorResponse = JsonResponse({"success": "false","message": "Uncessfull"})
            errorResponse.status_code = 400
            return errorResponse
