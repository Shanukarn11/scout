#coding: utf8
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.urls import path
from registration import coachviews, views
import re


urlpatterns = [
    path("", coachviews.coach, name='coach'),

    path("positiondata", views.positiondata, name='positiondata'),
    path("academypreview", coachviews.academypreview, name='academypreview'),
    path("addplayer", coachviews.addplayer, name='addplayer'),
    path("addcoach", coachviews.addcoach, name='addcoach'),
    path("admitcard", coachviews.admitcard, name='admitcard'),
    path("coachplayer", coachviews.coachplayer, name='coachplayer'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
