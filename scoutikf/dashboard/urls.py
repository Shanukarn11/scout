from django.urls import path
from . import views
from django.db.models import Q
urlpatterns = [
    path('', views.home, name='home'),
    path('search_city', views.search_city, name='search_city'),


    path('payment_status/<str:id>', views.payment_status, name='payment_status'),
    path('payment_citywise_status', views.payment_citywise_status, name='payment_citywise_status'),

    path('payment_status/payment_statustable/<str:id>',
         views.payment_statustable, name='payment_statustable'),



    path('citydetail/<str:id>', views.citydetail, name='citydetail'),
    path('citydetail/group/<str:id>', views.group, name='group'),
    path('citydetail/group/player/<str:id>', views.player, name='player'),
    path('citydetail/group/playersec/<str:id>',
         views.playersec, name='playersec'),

    path('citydetail/group/player/playertable/<str:id>',
         views.playertable, name='playertable'),
    path('citydetail/group/playersec/playersectable/<str:id>',
         views.playersectable, name='playersectable'),



    # path('citydetail/group/player/<str:id>', views.group, name='group'),




]
