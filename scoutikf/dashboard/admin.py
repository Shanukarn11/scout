from atexit import register
from sre_parse import State
from django.contrib import admin
from django.contrib import messages

from registration.modelhome import  SocialMediaLink
from registration.models import MasterAmount, MasterCategory, MasterRoles, MasterSeason, MasterState, MasterCity, MasterGroup, MasterPosition, MasterLabels, Payment, Scout, MasterGroupCity, Upload, Uploadfile, MasterDocument

admin.register(Scout)
admin.register(MasterCity)
admin.register(MasterState)
