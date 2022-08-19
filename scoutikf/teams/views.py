from asyncore import loop
# from doctest import ELLIPSIS_MARKER
# from turtle import position
from django.shortcuts import render
from .forms import NameForm, playerForm, NameForm2
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from registration.models import Player, MasterCity, MasterState, MasterCategory, MasterGroup, MasterPosition
import pandas as pd
from django.contrib import messages

# Create your views here.


def team(request):
    # if this is a POST request we need to process the form data
    m = "IKF Team Creator "
    m2=""
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = NameForm(request.POST)
        # form2 = NameForm2(request.POST)

        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required

            city = form.cleaned_data['city']
            group = form.cleaned_data['group']
            player = Player.objects.filter(
                tournament_city_id=city, group=group,status="success")
            
           

            if len(player) > 0:

                idd = city+"-"+group

                if form.cleaned_data['crete_update'] == "create":
                    return redirect('formteam', id=idd)
                    

                elif form.cleaned_data['crete_update'] == "update":
                    return redirect('team_table2', id=idd)
                else:
                    return redirect('download', id=idd)
            else:
                m2 = "No player in this group, Select another city or group"
    else:
        form = NameForm()
        # form2 = NameForm2()

    return render(request, 'team.html', {'form': form, "m": m,"m2":m2})

# functions to be used in teamlist


def get_pos_id(name):
    for j in range(10):
        if positions.loc[j].label == name:
            return positions.loc[j].id


def get_pos_name(id, pos):
    for i, row in pos.iterrows():
        if(row["id"] == id):
            return row["position"]
def get_pos_label(id, pos):
    for i, row in pos.iterrows():
        if(row["id"] == id):
            return row["label"]


def teamlist(request, id):

    id_ = id
    f = id.find('-')

    city = int(id[0:f])
    groupid = id[f+1:]
    city_ = MasterCity.objects.filter(id=city)
    for i in city_:
        cityName = i.city
    # ******************************************************************
    # data from player as dataframe
    player = Player.objects.all()
    for i in player:
        player_obj = Player.objects.get(id=i.id)
        player_obj.team = ""
        player_obj.position1 = ""
        player_obj.save()

    datas = Player.objects.filter(tournament_city_id=city, group=groupid)
    # column_headers = Player._meta.get_fields()
    player = pd.DataFrame(list(datas.values('id', 'userid', 'ikfuniqueid', 'password', 'team', 'position1', 'tournament_city',
                          'tournament_state', 'gender', 'first_name', 'last_name', 'height', 'weight', 'primary_position', 'secondary_position')))
    # player=
    player = player.sort_values(by='id', ascending=1)
    player["team"] = ""
    player["position1"] = ""

    indexx = []
    for i in range(len(player)):
        indexx.append(i)
    indexx = []
    for i in range(len(player)):
        indexx.append(i)
    player["Index"] = indexx
    player["alpha"] = indexx
    player = player.set_index('Index')

    # getting data form postions in dataframe
    # *****************************************************
    positionData = MasterPosition.objects.all()
    positions = pd.DataFrame(
        list(positionData.values('id', 'position', 'label')))
    positions.set_index('id')
    toalcount = len(player)
    no_of_teams = toalcount//11
  
    n = no_of_teams
   
    initial_remaing_players = toalcount % 11
    teams = []
    index = []
    for i in range(1, no_of_teams+1):
        teams.append("team_"+str(i))

    teams = pd.DataFrame(teams, columns=['Team'],)
    pos = []
    for i in positions.position:
        teams[i] = ""

    less = {}
    equal = {}
    more = {}

    for i, row in positions.iterrows():

        try:

            count = player['primary_position'].value_counts()[row["id"]]
            if(count == n):
                equal[row["id"]] = count
            elif(count > n):
                more[row["id"]] = count
            else:
                less[row['id']] = count

        except:
            print(end="")
    lessgetcount = {}
    for i in less:
        lessgetcount[i] = 0
    for key, value in more.items():
        for i, row in player.iterrows():

            if(row['primary_position'] == key):

                if row['secondary_position'] in less:
                    #
                    lessgetcount[row['secondary_position']
                                 ] = lessgetcount[row['secondary_position']]+1
    # *************************************************************

    for lesspos, value in lessgetcount.items():
        if less[lesspos]+value <= n and value > 0:

            for i, row in player.iterrows():

                try:
                    if row['primary_position'] in more:
                        if row['secondary_position'] == lesspos:
                            index = row['alpha']
                            posname = get_pos_name(
                                row['secondary_position'], positions)
                            j = 0
                            while j < n:

                                if teams.at[j, posname] == "":
                                    teams.at[j, posname] = row['id']

                                    player.at[index, 'team'] = j
                                    player.at[index, 'position1'] = posname
                                    player_obj = Player.objects.get(
                                        id=row['id'])
                                    player_obj.team = str(j)
                                    player_obj.position1 = posname
                                    player_obj.save()
                                    

                                    flag = 1
                                    break
                                j = j+1


                except:
    
                   
                    print("",end="")
    # *********************************************************
    data = []
    count = 0

    remain = pd.DataFrame(data, columns=['id', 'name', 'pri_pos', 'sec_pos'])
    for i, row in player.iterrows():
        index = row['alpha']

        try:
            if row['team'] == "":
                posname = get_pos_name(row['primary_position'], positions)

                secposname = get_pos_name(row['secondary_position'], positions)

                j = 0
                flag = 0
                while j < n:

                    if teams.at[j, posname] == "":

                        teams.at[j, posname] = row['id']

                        player.at[index, 'team'] = j
                        player.at[index, 'position1'] = posname
                        player_obj = Player.objects.get(id=row['id'])
                        player_obj.team = str(j)
                        player_obj.position1 = posname
                        player_obj.save()
                        # print("ad2")
                        flag = 1
                        count = +1
                        break

                    if (j == n-1 and flag == 0):
                        k = 0
                        while k < n:
                            if teams.at[k, secposname] == "":

                                teams.at[k, secposname] = row['id']

                                flag = 1
                                player.at[index, 'team'] = k
                                player.at[index, 'position1'] = secposname
                                player_obj = Player.objects.get(id=row['id'])
                                player_obj.team = str(k)
                                player_obj.position1 = secposname
                                player_obj.save()

                                count = +1
                                break
                            k = k+1

                            if flag == 0 and k == n and row['team'] == "":
                                df = pd.DataFrame({"id": [row['id']],
                                                   "name": [str(row['id'])+"-"+row['first_name']+" " + row['last_name']],
                                                  "pri_pos": [row['primary_position']],
                                                   "sec_pos": [row['secondary_position']]})
                                remain = pd.concat([remain, df])

                    j = j+1
        except Exception as e:
            # print("ERROR2 : "+str(e))
            print("",end="")

    dictt = {}
    for i, row in teams.iterrows():
        List = []
        for j in positions.position:

            if row[j] == "":
                List.append(j)

            else:
                print("", end="")
        if len(List) != 0:
            dictt[i] = List

    looplist = []
    for i in range(n):
        looplist.append(i)

    a = ""

    if request.GET.get('name'):
        message = 'You submitted: %r' % request.GET['name']
        # print(request.GET['name'])
        pid = request.GET['name']
        message = request.GET['name']+request.GET['position']

        F = request.GET['position'].find('-')

        player_team = request.GET['position'][0:F]

        position_name = request.GET['position'][F+1:]
        message = "Player added  "
        for i, row in positions.iterrows():
            if row['position'] == position_name:
                positionid = row['label']

        player_obj = Player.objects.get(id=pid)
        player_obj.team = player_team
        player_obj.position1 = posname
        player_obj.save()

    else:
        message = ''

    return render(request, 'teamlist.html', {'id': id, "city": city, "groupid": groupid, "teams": teams, "n": n, "player": player, "looplist": looplist, "positions": positions, "a": a, "cityName": cityName, "message": message, "remain": remain, "dictt": dictt})


def team_table(request, id):
    id_ = id
    f = id.find('-')

    city = int(id[0:f])
    groupid = id[f+1:]
    city_ = MasterCity.objects.filter(id=city)
    for i in city_:
        cityName = i.city
    datas = Player.objects.filter(tournament_city_id=city, group=groupid)
    player = pd.DataFrame(list(datas.values('id', 'userid', 'password', 'tournament_city', 'team', 'ikfuniqueid', 'tournament_state',
                          'position1', 'gender', 'first_name', 'last_name', 'height', 'weight', 'primary_position', 'secondary_position')))
    # player=
    player = player.sort_values(by='id', ascending=1)

    positionData = MasterPosition.objects.all()
    positions = pd.DataFrame(
        list(positionData.values('id', 'position', 'label')))
    # print(positions)
    positions = positions.set_index('id')
    toalcount = len(player)
    no_of_teams = toalcount//11
    n = no_of_teams
    # print("no_of_teams",no_of_teams)
    looplist = []
    for i in range(n):
        looplist.append(str(i))

    a = ""
    remain = pd.DataFrame([], columns=['id', 'name', 'pri_pos', 'sec_pos'])
    for i, row in player.iterrows():
        # print(i,row["team"])
        if not row["team"]:
            df = pd.DataFrame({"id": [row['id']],
                               "name": [str(row['ikfuniqueid'])+"-"+row['first_name']+" " + row['last_name']],
                              "pri_pos": [row['primary_position']],
                               "sec_pos": [row['secondary_position']]})
            remain = pd.concat([remain, df])

    dictt = {}

    for i in range(n):
        List = []
        for j in positions.position:
            found = 0
            for k, row in player.iterrows():
                if(row["position1"] == j and row["team"] == str(i)):
                    found = 1

            if found == 0:
                List.append(j)
                # print(List)
        if len(List) != 0:
            dictt[i] = List
        if request.GET.get('name'):
            message = 'You submitted: %r' % request.GET['name']
            # print(request.GET['name'])
            pid = request.GET['name']
            message = request.GET['name']+request.GET['position']

            F = request.GET['position'].find('-')

            player_team = request.GET['position'][0:F]

            position_name = request.GET['position'][F+1:]
            message = "player added at positon " + \
                str(position_name)+" in team number :"+str(player_team)

            player_obj = Player.objects.get(id=pid)
            player_obj.team = player_team
            player_obj.position1 = position_name
            player_obj.save()

        else:
            message = ''
        teams = []
        index = []
        for i in range(n):
            teams.append(i)

        teams = pd.DataFrame(teams, columns=['Team'],)
        pos = []
        for i in positions.position:
            teams[i] = ""
        teams = teams.set_index("Team")
        # print(teams)
        for i, row in teams.iterrows():
            for p in positions.position:

                try:
                    player_obj = Player.objects.get(
                        team=i, position1=p, tournament_city=city)
                    #  print("adede")
                    teams.at[i, p] = player_obj.ikfuniqueid
                except:
                    teams.at[i, p] = "NOT Assigned"
                    # print("")
        # print(teams)
    Loop = []
    for i in range(n):
        Loop.append(i)
    position_label = []
    position_tag = []

    for ip, r in positions.iterrows():
        position_label.append(r.label)
        position_tag.append(r.position)
    # print(teams.head())

    return render(request, 'team_table.html', {'id': id, "city": city, "groupid": groupid, "n": n, "player": player, "looplist": looplist, "positions": positions, "a": a, "cityName": cityName, "remain": remain, "dictt": dictt, "message": message, "teams": teams, "Loop": Loop, "position_label": position_label, "position_tag": position_tag})


def delete(request, id):
   
    player_obj = Player.objects.get(ikfuniqueid=id)
    print(player_obj.first_name)
    idd = str(player_obj.tournament_city_id)+"-"+str(player_obj.group)
   
   
    player_obj.team = ""
    player_obj.position1 = ""
    player_obj.save()
    
    return redirect('team_table2', id=idd)
  


def download(request, id):
   
    id_ = id
    f = id.find('-')
    positions = MasterPosition.objects.all().order_by('id')
    
    city = int(id[0:f])
    groupid = id[f+1:]
    city_ = MasterCity.objects.filter(id=city)
    for i in city_:
        cityName = i.city
    player = Player.objects.filter(tournament_city_id=city, status="success", group=groupid)

    n = len(player)//11
   
    dict = {}
    pend_dict={}
    for i in range(n+1):
        

        T0 = player = Player.objects.filter(
            tournament_city_id=city, status="success", group=groupid, team=i).order_by('position1')
        if len(T0)>0:
            dict[i] = T0
            posList=[]
            pendList=[]
            for t in T0:
                posList.append(t.position1)
            # print(posList)
            for pos in positions:
                if pos.label not in posList:
                    pendList.append(pos.label)
            if posList.count('Center Back/Stopper')+pendList.count('Center Back/Stopper')<2:
                pendList.append('Center Back/Stopper 2')
            pend_dict[i]=pendList
          
    
    
            
        
        
    

    Heading = id+"All teams"
    if request.GET.get('Team_no'):
        ti = request.GET['Team_no']
        dict = {}
        T0 =  Player.objects.filter(
            tournament_city_id=city, status="success", group=groupid, team=ti)
        dict[int(ti)] = T0
        p=pend_dict
        pend_dict={}
      
        
        pend_dict[int(ti)]=p[int(ti)]

       

        Heading = cityName+"-"+groupid+"-Team-"+ti
    li=[]
    for T in T0:
        li.append(T.position1)
    
    
    if n%11==0:

        x=n
    else:
        x=n+1
  
        
    remain2= len(Player.objects.filter(tournament_city_id=city, status="success", group=groupid,team="-"))
    
    return render(request, "download.html", {"id": id, "cityName": cityName, "dict": dict, "n": n, "Heading": Heading, 'range': range(x),"remain2":remain2,"groupid":groupid,"pend_dict":pend_dict})


def formteam(request, id):
   
    id_ = id
    f = id.find('-')

    city = int(id[0:f])
    groupid = id[f+1:]
  
   
    city_ = MasterCity.objects.filter(id=city)
    for i in city_:
        cityName = i.city
    player = Player.objects.filter(
        tournament_city_id=city, group=groupid,status="success").order_by('id')
    dup_list=[]
    for i in player:
      
        p=Player.objects.filter(mobile=i.mobile,tournament_city_id=city, group=groupid,status="success")
        
       
        if i.mobile not in dup_list:
            
            i.team="-"
         
            i.position1="NOT ASSIGNED"
            player_obj = Player.objects.get(id=i.id)
            player_obj.team = "-"
            player_obj.position1 = "NOT ASSIGNED"
            player_obj.save()
            dup_list.append(i.mobile)
        else:
            i.team="*"
            
            i.position1="*"
            player_obj = Player.objects.get(id=i.id)
            player_obj.team = "*"
            player_obj.position1 = "*"
            player_obj.save()
            dup_list.append(i.mobile)
            

    count=len(player)
    n = (len(player)//11)+1
    # print("n", n)
    positions = MasterPosition.objects.all().order_by('id')
    for team_no in range(n):
        for i in player:
            for j in positions:
                if (i.primary_position_id == j.id):
                    if(j.id != 2):
                        if((len(Player.objects.filter(tournament_city_id=city, group=groupid, status="success", team=str(team_no), position1=j.label)) == 0) and i.position1 == "NOT ASSIGNED"):

                            i.position1 = j.label
                            i.team = str(team_no)

                            player
                            player_obj = Player.objects.get(id=i.id)
                            player_obj.team = str(team_no)
                            player_obj.position1 = j.label
                            player_obj.save()
                            # print(i.id)
                        

                    else:
                        if(len(Player.objects.filter(tournament_city_id=city, group=groupid,  status="success",team=str(team_no), position1=j.label)) <2 and i.position1 == "NOT ASSIGNED"):

                            i.position1 = j.label
                            i.team = str(team_no)
                            player_obj = Player.objects.get(id=i.id)
                            player_obj.team = str(team_no)

                            player_obj.position1 = j.label
                            # print(player_obj)
                            player_obj.save()
                            # print("addded 2")
                if (i.secondary_position_id == j.id): 
                    if(j.id != 2):
                        if((len(Player.objects.filter(tournament_city_id=city,  status="success",group=groupid, team=str(team_no), position1=j.label)) == 0) and i.position1 == "NOT ASSIGNED"):

                            i.position1 = j.label
                            i.team = str(team_no)

                            player
                            player_obj = Player.objects.get(id=i.id)
                            player_obj.team = str(team_no)
                            player_obj.position1 = j.label
                            player_obj.save()
                            # print("added 1")

                    else:
                        if(len(Player.objects.filter(tournament_city_id=city, group=groupid, status="success", team=str(team_no), position1=j.label)) < 2 and i.position1 == "NOT ASSIGNED"):

                            i.position1 = j.label
                            
                            i.team = str(team_no)
                            player_obj = Player.objects.get(id=i.id)
                            player_obj.team = str(team_no)

                            player_obj.position1 = j.label
                            # print(player_obj)
                            player_obj.save()
   

    remain= len(Player.objects.filter(tournament_city_id=city, status="success", group=groupid,team="-"))
    
    dict_round1={}
    dict_round1["Left Mid/Left Winger"]=["Right Mid/Right Winger"]
    dict_round1["Right Mid/Right Winger"]=["Left Mid/Left Winger"]
    dict_round1["Right Back"]=["Left Back","Center Back/Stopper"]
    dict_round1["Left Back"]=["Right Back","Center Back/Stopper"]
   
    dict_round1["Center Back/Stopper"]=["Right Back","Left Back"]


    dict_round1["Attacking Mid"]=["Defensive Mid","Center Mid"]
    dict_round1["Defensive Mid"]=["Attacking Mid","Center Mid"]
    dict_round1["Center Mid"]=["Defensive Mid","Attacking Mid"]



   

    
    posLw=["Right Mid/Right Winger","Attacking Mid","Center Mid","Defensive Mid"]
    for team_no in range(n):

        for i in player:
            for pos , alterList in dict_round1.items():
                if i.position1=="NOT ASSIGNED" and (str(i.primary_position)==pos or(str(i.secondary_position)==pos)):
                
                    # print(i.first_name,i.primary_position)
                     for pos in alterList:
                        if pos!="Center Back/Stopper":
                            if((len(Player.objects.filter(tournament_city_id=city, status="success", group=groupid, team=str(team_no), position1=pos)) == 0) ):
                                i.position1 = pos
                                    
                                i.team = str(team_no)
                                player_obj = Player.objects.get(id=i.id)
                                player_obj.team = str(team_no)

                                player_obj.position1 = pos
                            
                                player_obj.save()
                                # print("round 2-1")
                        else:
                            if(len(Player.objects.filter(tournament_city_id=city, status="success", group=groupid, team=str(team_no), position1=pos)) <= 2 ):

                                i.position1 = pos
                                    
                                i.team = str(team_no)
                                player_obj = Player.objects.get(id=i.id)
                                player_obj.team = str(team_no)

                                player_obj.position1 = pos
                            
                                player_obj.save()
                                # print("round 2-1")

    dict_round2={}
    dict_round2["Left Mid/Left Winger"]=["Striker/Center Forward","Attacking Mid","Center Mid","Defensive Mid",]
    dict_round2["Right Mid/Right Winger"]=["Striker/Center Forward","Attacking Mid","Center Mid","Defensive Mid"]
    dict_round2["Attacking Mid"]=["Left Mid/Left Winger","Right Mid/Right Winger","Center Back/Stopper","Left Back","Right Back"]
    dict_round2["Center Mid"]=["Left Mid/Left Winger","Right Mid/Right Winger","Center Back/Stopper","Left Back","Right Back"]
    dict_round2["Defensive Mid"]=["Left Mid/Left Winger","Right Mid/Right Winger","Center Back/Stopper","Left Back","Right Back"]
    dict_round2["Right Back"]=["Center Mid","Defensive Mid","Attacking Mid"]
    dict_round2["Left Back"]=["Center Mid","Defensive Mid","Attacking Mid"]
    dict_round2["Striker/Center Forward"]=["Left Mid/Left Winger","Right Mid/Right Winger"]

    for team_no in range(n):
        
        for i in player:
            for pos , alterList in dict_round2.items():
               
                if (i.position1=="NOT ASSIGNED" )and ((str(i.primary_position)==pos)or(str(i.secondary_position)==pos)):
                    
                        # print(i.first_name,i.primary_position)
                    for pos in alterList:
                        if((len(Player.objects.filter(tournament_city_id=city, status="success", group=groupid, team=str(team_no), position1=pos)) == 0) ):
                            i.position1 = pos
                                    
                            i.team = str(team_no)
                            player_obj = Player.objects.get(id=i.id)
                            player_obj.team = str(team_no)

                            player_obj.position1 = pos
                            
                            player_obj.save()
                            # print("round 3-1")

                        
                        
                        
                        

    
    


    # print("gsdhkf", str(0))
    v = Player.objects.filter(id="248")


    remain2= len(Player.objects.filter(tournament_city_id=city, status="success", group=groupid,team="-"))
    player=Player.objects.filter(tournament_city_id=city,  status="success",group=groupid).order_by("team")
    teams = []
    index = []
    for i in range(n):
        teams.append(i)
    positionData = MasterPosition.objects.all()
    positions = pd.DataFrame(
        list(positionData.values('id', 'position', 'label')))

    teams = pd.DataFrame(teams, columns=['Team'],)
    pos = []
    for i in positions.position:
        teams[i] = ""
    teams = teams.set_index("Team")
    
   
   

    return redirect('team_table2', id=id_)

   


def team_table2(request, id):
  

    id_ = id
    f = id.find('-')

    city = int(id[0:f])
  

    groupid = id[f+1:]
    city_ = MasterCity.objects.filter(id=city)
    for i in city_:
        cityName = i.city
    datas = Player.objects.filter(tournament_city_id=city, status="success", group=groupid)
    player = pd.DataFrame(list(datas.values('id', 'userid', 'password', 'tournament_city', 'team', 'ikfuniqueid', 'tournament_state',
                          'position1', 'gender', 'first_name', 'last_name', 'height', 'weight', 'primary_position', 'secondary_position')))
    # player=
    player = player.sort_values(by='id', ascending=1)
   
    
    positionData = MasterPosition.objects.all()
    positions = pd.DataFrame(
        list(positionData.values('id', 'position', 'label')))
    # print(positions)
    positions = positions.set_index('id')
    toalcount = len(player)
    no_of_teams = (toalcount//11)+1
    n = no_of_teams
   
    looplist = []
    for i in range(n):
        looplist.append(str(i))

    a = ""
    positionData = MasterPosition.objects.all()
    positions2 = pd.DataFrame(
    list(positionData.values('id', 'position', 'label')))
    positions2.set_index('id')
    remain = pd.DataFrame([], columns=['id', 'name', 'pri_pos', 'sec_pos'])
    for i, row in player.iterrows():
        # print(i,row["team"])
        if  row["team"]=="-" or row["team"]=="":
            df = pd.DataFrame({"id": [row['id']],
                               "name": [str(row['ikfuniqueid'])+"-"+row['first_name']+" " + row['last_name']+"("+get_pos_label(row['primary_position'],positions2)+", "+get_pos_label(row['secondary_position'],positions2)+")"],
                              "pri_pos": [row['primary_position']],
                               "sec_pos": [row['secondary_position']]})
           


            remain = pd.concat([remain, df])

    dictt = {}

    for i in range(n):
        List = []
        for j in positions.label:
            found = 0
            for k, row in player.iterrows():
                if(row["position1"] == j and row["team"] == str(i)):
                        found = 1
                        if(row["position1"] =="Center Back/Stopper" and len(Player.objects.filter(tournament_city=city,group=groupid,status="success",position1="Center Back/Stopper",team=str(i)))<2):
                            found=1
    
            if found == 0:
                List.append(j)
                # print(List)
        if len(List) != 0:
            dictt[i] = List



        if request.GET.get('name'):
            message = 'You submitted: %r' % request.GET['name']
            # print(request.GET['name'])
            pid = request.GET['name']
            message = request.GET['name']+request.GET['position']

            F = request.GET['position'].find('-')

            player_team = request.GET['position'][0:F]

            position_name = request.GET['position'][F+1:]
            message = "player added at positon " + \
                str(position_name)+" in team number :"+str(player_team)

            player_obj = Player.objects.get(id=pid)
            player_obj.team = player_team
            player_obj.position1 = position_name
            player_obj.save()

        else:
            message = ''
        teams = []
        index = []
        for i in range(n):
            teams.append(i)

        teams = pd.DataFrame(teams, columns=['Team'],)
        pos = []
        for i in positions.position:
            teams[i] = ""
            teams[i+"name"]=""
        teams = teams.set_index("Team")
        
      
        for i, row in teams.iterrows():
            for a,p in positions.iterrows():

                try:
                   
                    if(p['label']!="Center Back/Stopper"):
                        player_obj = Player.objects.get(
                            team=i, position1=p['label'], tournament_city=city,group=groupid,status="success")
                    
                        teams.at[i, p['position'] ]= player_obj.ikfuniqueid
                        teams.at[i, p['position']+"name" ]= player_obj.first_name+" "+player_obj.last_name+"("+player_obj.ikfuniqueid+")"

                    else:
                        teams.at[i, p['position'] ]= "NOT Assigned"
                        teams.at[i, p['position']+"name" ]= "NOT Assigned"

                        teams.at[i, "Center_Back_Or_Stopper2" ]= "NOT Assigned"
                        teams.at[i, "Center_Back_Or_Stopper2name" ]= "NOT Assigned"


                        player_obj = Player.objects.filter(
                            team=i, position1=p['label'], status="success", tournament_city=city)
                        c=0
                        for pl in player_obj:
                            if c==0:
                                teams.at[i, p['position'] ]= pl.ikfuniqueid
                             
                                teams.at[i, p['position']+"name" ]= pl.first_name+" "+pl.last_name+"("+pl.ikfuniqueid+")"


                                c=1
                            else:
                                teams.at[i, "Center_Back_Or_Stopper2" ]= pl.ikfuniqueid
                                teams.at[i, "Center_Back_Or_Stopper2name"]= pl.first_name+" "+pl.last_name+"("+pl.ikfuniqueid+")"

                                c=1

                            

                except Exception as e:
                  
                    
                    teams.at[i,  p['position']] = "NOT Assigned"
                    teams.at[i,  p['position']]= "NOT Assigned"


                    # print("")
        # (teams)
    # for i, row in teams.iterrows():
    #         for a,p in positions.iterrows():
    #             try:
    #                 if(p['label']!="Center Back/Stopper"):
    #                     player_obj = Player.objects.get(
    #                         team=i, position1=p['label'],group=group_id, tournament_city=city, status="success")
    #                     teams.at[i, p['position'] ]= player_obj.ikfuniqueid
    #             except Exception as e:
    #                 print("-",p['label'])
    #                 print(e)
    Loop = []
    for i in range(n):
        Loop.append(i)
    position_label = []
    position_tag = []

    for ip, r in positions.iterrows():
        position_label.append(r.label)
        position_tag.append(r.position)
    # print(teams.head())
    dd="dd2"
    remain2= len(Player.objects.filter(tournament_city_id=city, status="success", group=groupid,team="-"))
    
    # print(teams)
    return render(request, 'team_table2.html', {'id': id, "city": city, "groupid": groupid, "n": n, "player": player, "looplist": looplist, "positions": positions, "a": a, "cityName": cityName, "remain": remain, "dictt": dictt, "message": message, "teams": teams, "Loop": Loop, "position_label": position_label, "position_tag": position_tag,"dd":dd,"remain2":remain2})
