from django.urls import path
from . import views
from django.db.models import Q
urlpatterns = [
    path('', views.team, name='team'),
    path('teamslist/<str:id>', views.teamlist, name='teamlist'),

    path('team_table/<str:id>', views.team_table, name='team_table'),
    path('team_table2/<str:id>', views.team_table2, name='team_table2'),

    path('delete/<str:id>', views.delete, name='delete'),
    path('download/<str:id>', views.download, name='download'),
    path('formteam/<str:id>', views.formteam, name='formteam'),


]