# from unicodedata import category
from django import forms
from registration.models import Player, MasterCity, MasterState, MasterCategory,MasterGroup




    
city = MasterCity.objects.raw( 'select `id`, `city` from `registration_mastercity`')
citychoice=[]
for i in city:
    
    l=[]
    l.append(i.id)
    l.append(i.city)
    
    citychoice.append(l)

group=MasterGroup.objects.raw( 'select `id` from `registration_mastergroup`')
group_choice=[]
for i in group:
    
    l=[]
    l.append(i.id)
    l.append(i.id)
    
    group_choice.append(l)

class NameForm(forms.Form):
   
    

    city= forms.CharField(label='City ', widget=forms.Select(choices=citychoice))
    group= forms.CharField(label='Group ', widget=forms.Select(choices=group_choice))
    crete_update= forms.CharField(label='Action ', widget=forms.Select(choices=[["update","Update"],["create","Create"],["download","Download"]]))

class NameForm2(forms.Form):
   
    

    city= forms.CharField(label='City', widget=forms.Select(choices=citychoice))
    group= forms.CharField(label='Group', widget=forms.Select(choices=group_choice))




class playerForm(forms.Form):
   
    

    player= forms.CharField(label='player')
    group= forms.CharField(label='category')
   