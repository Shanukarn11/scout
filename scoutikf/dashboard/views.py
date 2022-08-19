from itertools import count
# import re

from typing import List
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
# from django.db.models import Count
# from matplotlib import gridspec
# from matplotlib.pyplot import prism

from django.db.models import Count

from registration.models import Player, MasterCity, MasterState, MasterCategory


def home(request):

    # total
    citytext = 'select `id`, `tournament_city_id`,count(*) as c from `registration_player`  '
    cityCount = Player.objects.raw(citytext
                                   )
    for i in cityCount:
        totalcount = i.c
    totaluniqtxt = 'select `id`, `tournament_city_id`,COUNT(DISTINCT  `mobile`) as c from `registration_player`  '
    totalunique = Player.objects.raw(totaluniqtxt)
    for i in totalunique:
        totalunicount = i.c
    s = "'failed'"
    tfailedu = Player.objects.raw(
        'select count(*) as c,`id`   from (select *  from `registration_player` where `status`="failed")  as r  WHERE NOT EXISTS (SELECT * FROM `registration_player`a where  r.`mobile`= a.`mobile` and a.`status`="success")  group by `mobile` ')
    count = 0
    for i in tfailedu:
        count = count+i.c
        tfailedcountunique = i.c
    tfailedcountunique = count
    tfailedtxt = 'select `id`, `tournament_city_id`,count(*) as c from `registration_player` where `status`= {}   '

    tfailed = Player.objects.raw(tfailedtxt.format(s))
    for i in tfailed:
        tfailedcount = i.c
    tnotin = Player.objects.raw(
        'select `id`, `tournament_city_id`,count(*) as c from `registration_player` where `status` IS NULL ')
    for i in tnotin:
        tnotinc = i.c
    tnotinuni = Player.objects.raw(
        'select  count(*) as c,`id` from `registration_player`  as r  WHERE NOT EXISTS (SELECT * FROM `registration_player`a where r.`mobile`= a.`mobile` and (a.`status`="success" or a.`status`="failed" ))group by `mobile`')
    count = 0
    for i in tnotinuni:
        count = count+1
        tnotincunique = i.c
    tnotincunique = count

    # citywise

    txtt = 'select `id`, `tournament_city_id`,COUNT(DISTINCT  `mobile`) as c from `registration_player` group by `tournament_city_id`  '
    mobilecount = Player.objects.raw(txtt
                                     )
    tsucess = Player.objects.raw(
        'select `id`, `tournament_city_id`,count(*) as c from `registration_player` where `status`="success" ')
    for i in tsucess:
        tsucescount = i.c

    txt = 'select `id`, `tournament_city_id`,count(*) as c from `registration_player` group by `tournament_city_id` '
    cityCount = Player.objects.raw(txt
                                   )
    txtt = 'select `id`, `tournament_city_id`,COUNT(*) as c from `registration_player` where `status`="success" group by `tournament_city_id`  '
    mobilecount = Player.objects.raw(txtt
                                     )

    sucess = Player.objects.raw(
        'select `id`, `tournament_city_id`,count(*) as c from `registration_player` where `status`="success"   group by `tournament_city_id` ')
    s = "'failed'"
    txt1 = 'select `id`, `tournament_city_id`,count(*) as c from `registration_player` where `status`= {}   group by `tournament_city_id` '
    # txt2=
    failed = Player.objects.raw(txt1.format(s))

    notin = Player.objects.raw(
        'select `id`, `tournament_city_id`,count(*) as c from `registration_player` where `status` IS NULL group by `tournament_city_id` ')

    dupPhone = Player.objects.raw(
        'select `id`,`mobile` , `tournament_city_id`,count(distinct mobile) as c from `registration_player`  group by `tournament_city_id` ')
    dupPhone2 = Player.objects.raw(
        'select `id`, `tournament_city_id`,`mobile`,count(*) as c from `registration_player` group by `mobile` ')

    cityCount1 = Player.objects.raw(
        'select `id`,  `tournament_city_id`,`group_id`,count(*) as g from `registration_player`  where `status`="success"  group by `group_id`,`tournament_city_id`')
    s = "success"
    f = "failed"
    n = "not_initiated"
    title = " Dashboard"

    return render(request, 'home.html', {'cityCount': cityCount, 'cityCount1': cityCount1, 'sucess': sucess, 'failed': failed, "notin": notin, "mobilecount": mobilecount, "totalcount": totalcount, "totalunicount": totalunicount, "tsucescount": tsucescount, "tfailedcount": tfailedcount, "tnotinc": tnotinc, "s": s, "f": f, "n": n, "title": title, "tfailedcountunique": tfailedcountunique, "tnotincunique": tnotincunique})


def citydetail(request, id):
    idf = id
    cityName = idf
    idd = '"'+idf+'"'
    txtcity = 'select `id`, `city` from `registration_mastercity` where `city`={} '
    city = MasterCity.objects.raw(txtcity.format(idd))
    for c in city:
        id = c.id
        break

    # txt0 = 'select `id`, `tournament_city_id` from `registration_player` where `tournament_city_id`={} '
    # city = Player.objects.raw(txt0.format(id))
    # for c in city:
    #     cityName = c.tournament_city
    #     break
    txt = 'select `id`, `primary_position_id`,count(*) as c from `registration_player` where `tournament_city_id`={} group by `primary_position_id` '

    priPosCount = Player.objects.raw(txt.format(id))
    txt2 = 'select `id`, `secondary_position_id`,count(*) as c from `registration_player` where `tournament_city_id`={} group by `secondary_position_id`'

    secPostCount = Player.objects.raw(txt2.format(id))
    txt3 = 'select `id`, `group_id`,count(*) as c from `registration_player` where `tournament_city_id`={} group by `group_id`'
    grpCount = Player.objects.raw(txt3.format(id))
    count_={}
    totalregi=len(Player.objects.filter(tournament_city_id=id))
    total_suc_regi=len(Player.objects.filter(tournament_city_id=id,status="success"))

    return render(request, 'citydetail.html', {'priPosCount': priPosCount, 'secPostCount': secPostCount, "cityName": cityName, "grpCount": grpCount, 'city': id,"totalregi":totalregi,"total_suc_regi":total_suc_regi})


def group(request, id):
    
    f = id.find('-')

    city = int(id[0:f])

    txt0 = 'select `id`, `city` from `registration_mastercity` where `id`={} '
    city_ = MasterCity.objects.raw(txt0.format(city))
    for c in city_:
        cityName = c.city
        break
    groupid = id[f+1:]
    g = "'"+groupid+"'"

    txt = 'select `id`, `primary_position_id`,`group_id`,count(*) as c from `registration_player` where `group_id`={} and  `tournament_city_id`={} group by `primary_position_id` '

    priPosCount = Player.objects.raw(txt.format(g, city))

    txt1 = 'select `id`, `secondary_position_id`,`group_id`,count(*) as c from `registration_player` where `group_id`={} and  `tournament_city_id`={} group by `secondary_position_id` '

    secPosCount = Player.objects.raw(txt1.format(g, city))
    txt=('select *  from (select *  from `registration_player` where `status`="failed" and `group_id`={} and  `tournament_city_id`={})  as r  WHERE NOT EXISTS (SELECT * FROM `registration_player`a where  r.`mobile`= a.`mobile` and a.`status`="success")  group by `mobile` ')
    failplayers=Player.objects.raw(txt.format(g, city)) 
    
    txt=('select *  from ( select *  from `registration_player` where  `group_id`={} and  `tournament_city_id`={})  as r  WHERE NOT EXISTS (SELECT * FROM `registration_player`a where r.`mobile`= a.`mobile` and (a.`status`="success" or a.`status`="failed" ))group by `mobile`')
    
    not_initiated=Player.objects.raw(txt.format(g, city)) 

    
    

    txt=('select * from `registration_player` where `status`="success" and `group_id`={} and  `tournament_city_id`={} ')
    successplayer=fail=Player.objects.raw(txt.format(g, city)) 
  
    



    return render(request, 'group.html', {"cityName": cityName, "groupid": groupid, "priPosCount": priPosCount, "city": city, "secPosCount": secPosCount,"idd":id,"failplayers":failplayers,"successplayer":successplayer,"not_initiated":not_initiated})


def player(request, id):
    # player/{{city}}-{{pos.group_id}}-{{pos.primary_position_id}}
    
    f = id.find("-")
    cityid = id[0:f]
    txt0 = 'select `id`, `tournament_city_id` from `registration_player` where `tournament_city_id`={} '

    city_ = Player.objects.raw(txt0.format(int(cityid)))
    for c in city_:
        cityName = c.tournament_city

        break
    idd = id[f+1:]
    f1 = idd.find("-")
    groupid = "'"+idd[0:f1]+"'"
    alpha=cityid+"-"+idd[0:f1]
    txt1 = 'select `id`, `tournament_city_id` from `registration_player` where `group_id`={} '

    group_ = Player.objects.raw(txt1.format(groupid))
    for c in group_:

        groupName = c.group
        break
    posid = idd[f1+1:]

    txt = 'select * from`registration_player` where `group_id`={} and  `tournament_city_id`={} and  `primary_position_id`={} '

    players = Player.objects.raw(txt.format(groupid, int(cityid), int(posid)))

    for i in players:
        stateName = i.state
        posName = i.primary_position
        break

    return render(request, "player.html", {"players": players, "city": cityName, "groupName": groupName, "posid": posid, "cityid": cityid, "posName": posName, "stateName": stateName,"idd":alpha})


def playertable(request, id):
    # player/{{city}}-{{pos.group_id}}-{{pos.primary_position_id}}
    f = id.find("-")
    cityid = id[0:f]
    txt0 = 'select `id`, `tournament_city_id` from `registration_player` where `tournament_city_id`={} '

    city_ = Player.objects.raw(txt0.format(int(cityid)))
    for c in city_:
        cityName = c.tournament_city
        break
    idd = id[f+1:]
    f1 = idd.find("-")
    groupid = "'"+idd[0:f1]+"'"
    txt1 = 'select `id`, `tournament_city_id` from `registration_player` where `group_id`={} '

    group_ = Player.objects.raw(txt1.format(groupid))
    for c in group_:
        groupName = c.group
        break
    posid = idd[f1+1:]
    txt = 'select * from`registration_player` where `group_id`={} and  `tournament_city_id`={} and  `primary_position_id`={} '

    players = Player.objects.raw(txt.format(groupid, int(cityid), int(posid)))
    for i in players:
        stateName = i.state
        posName = i.primary_position
        break
    return render(request, "playertable.html", {"players": players, "city": cityName, "groupName": groupName, "posid": posid, "cityid": cityid, "stateName": stateName, "posName": posName,"idd":id})


def playersec(request, id):
    f = id.find("-")
    cityid = id[0:f]
    txt0 = 'select `id`, `tournament_city_id` from `registration_player` where `tournament_city_id`={} '

    city_ = Player.objects.raw(txt0.format(int(cityid)))
    for c in city_:
        cityName = c.tournament_city

        break
    idd = id[f+1:]
    f1 = idd.find("-")
    groupid = "'"+idd[0:f1]+"'"
    alpha=cityid+"-"+idd[0:f1]
    txt1 = 'select `id`, `tournament_city_id` from `registration_player` where `group_id`={} '

    group_ = Player.objects.raw(txt1.format(groupid))
    for c in group_:

        groupName = c.group
        break
    posid = idd[f1+1:]

    txt = 'select * from`registration_player` where `group_id`={} and  `tournament_city_id`={} and  `secondary_position_id`={} '

    players = Player.objects.raw(txt.format(groupid, int(cityid), int(posid)))

    for i in players:
        stateName = i.state
        posName = i.secondary_position
        break

    return render(request, "playersec.html", {"players": players, "city": cityName, "groupName": groupName, "posid": posid, "cityid": cityid, "posName": posName, "stateName": stateName,"idd":alpha})



def playersectable(request, id):
    # player/{{city}}-{{pos.group_id}}-{{pos.primary_position_id}}
    f = id.find("-")
    cityid = id[0:f]
    txt0 = 'select `id`, `tournament_city_id` from `registration_player` where `tournament_city_id`={} '

    city_ = Player.objects.raw(txt0.format(int(cityid)))
    for c in city_:
        cityName = c.tournament_city
        break
    idd = id[f+1:]
    f1 = idd.find("-")
    groupid = "'"+idd[0:f1]+"'"
    txt1 = 'select `id`, `tournament_city_id` from `registration_player` where `group_id`={} '

    group_ = Player.objects.raw(txt1.format(groupid))
    for c in group_:

        groupName = c.group
        break
    posid = idd[f1+1:]
    txt = 'select * from`registration_player` where `group_id`={} and  `tournament_city_id`={} and  `secondary_position_id`={} '

    players = Player.objects.raw(txt.format(groupid, int(cityid), int(posid)))
    for i in players:
        stateName = i.state
        posName = i.secondary_position
        break

    return render(request, "playersectable.html", {"players": players, "city": cityName, "groupName": groupName, "posid": posid, "cityid": cityid, "stateName": stateName, "posName": posName,"idd":id})


def search_city(request):

    render(request, "search_city.html")


def payment_status(request, id):
    f = id.find('-')
    if f == -1:
        if id == "success":
            s = '"'+id+'"'
            players = Player.objects.raw(
                'select * from `registration_player` where `status`="success" ')
            Heading = "Successfully Payments"
            # playersfail = Player.objects.raw(
            # 'SELECT * ,COUNT(*) FROM (SELECT DISTINCT *,COUNT(*) FROM  `registration_player`  ) GROUP BY `mobile`,   HAVING COUNT(*) < 1')
            playersfail = Player.objects.raw(
                'SELECT `mobile`,`id` FROM `registration_player` HAVING COUNT(`mobile`) = 1')
            count = 0

            for p in players:
                count = count+1
            status=""
        elif id == "failed":
            status="failed"
            s = '"'+id+'"'

            players = Player.objects.raw(
                'select *  from (select *  from `registration_player` where `status`="failed")  as r  WHERE NOT EXISTS (SELECT * FROM `registration_player`a where  r.`mobile`= a.`mobile` and a.`status`="success")  group by `mobile` ')

            count = 0
            for p in players:

                count = count+1
            Heading = "Failed Payments"

        elif id == "not_initiated":
            players = Player.objects.raw(
                'select *  from `registration_player`  as r  WHERE NOT EXISTS (SELECT * FROM `registration_player`a where r.`mobile`= a.`mobile` and (a.`status`="success" or a.`status`="failed" ))group by `mobile`')

            Heading = " Payments not initiated"
            count = 0
            for i in players:
                count = count+1
            
        return render(request, "payment_status.html", {"players": players, "Heading": Heading, "id": id, "count": count})

    else:
        cityid = id[0:f]
        count = 0
        id = id[f+1:]

        s = '"'+cityid+'"'
        txt0 = 'select `id`, `city` from `registration_mastercity` where `id`={} '
        city_ = MasterCity.objects.raw(txt0.format(cityid))
        for c in city_:
            cityName = c.city
            break
        if id == "success":

            txt = 'select * from `registration_player` where `status`="success" and `tournament_city_id`={} '
            players = Player.objects.raw(txt.format(s))
            Heading = "Successfully Payments"

            count = 0

            for p in players:
                count = count+1
        elif id == "failed":

            txt = 'select *  from (select *  from `registration_player` where `status`="failed" and `tournament_city_id`={})  as r  WHERE NOT EXISTS (SELECT * FROM `registration_player`a where  r.`mobile`= a.`mobile` and a.`status`="success")  group by `mobile`  '
            players = Player.objects.raw(txt.format(s))

            count = 0
            for p in players:
                count = count+1
            Heading = "Failed Payments"

        elif id == "not_initiated":
            txt = 'select *  from (select * from `registration_player` where `tournament_city_id`={})  as r  WHERE NOT EXISTS (SELECT * FROM `registration_player`a where r.`mobile`= a.`mobile` and (a.`status`="success" or a.`status`="failed" ))group by `mobile`'
            players = Player.objects.raw(txt.format(s))

            Heading = " Payments not initiated"
            count = 0
            for i in players:
                count = count+1

        return render(request, "payment_status.html", {"players": players, "cityName": cityName, "Heading": Heading, "count": count})


def payment_statustable(request, id):
    f = id.find('-')
    pcity = MasterCity.objects.raw('select * from `registration_mastercity` ORDER BY `city`  ASC')

    if f == -1:
        if id == "success":
            s = '"'+id+'"'
            players = Player.objects.raw(
                'select * from `registration_player` where `status`="success" ')
            Heading = "Successfully Payments"
            playersfail = Player.objects.raw(
                'SELECT `mobile`,`id` FROM `registration_player` HAVING COUNT(`mobile`) = 1')
            count = 0

            for p in players:
                count = count+1

        elif id == "failed":
            s = '"'+id+'"'

            players = Player.objects.raw(
                'select *  from (select *  from `registration_player` where `status`="failed")  as r  WHERE NOT EXISTS (SELECT * FROM `registration_player`a where  r.`mobile`= a.`mobile` and a.`status`="success")  group by `mobile` ')

            count = 0
            for p in players:

                count = count+1
            Heading = "Failed Payments"

        elif id == "not_initiated":
            players = Player.objects.raw(
                'select *  from `registration_player`  as r  WHERE NOT EXISTS (SELECT * FROM `registration_player`a where r.`mobile`= a.`mobile` and (a.`status`="success" or a.`status`="failed" ))group by `mobile`')

            Heading = " Payments not initiated"
            count = 0
            for i in players:
                count = count+1

        return render(request, "payment_statustable.html", {"players": players, "Heading": Heading, "count": count, "pcity": pcity, "idd": id})

    else:
        cityid = id[0:f]
        count = 0
        id = id[f+1:]

        s = '"'+cityid+'"'
        txt0 = 'select `id`, `city` from `registration_mastercity` where `id`={} '
        city_ = MasterCity.objects.raw(txt0.format(cityid))
        for c in city_:
            cityName = c.city

            break
        if id == "success":

            txt = 'select * from `registration_player` where `status`="success" and `tournament_city_id`={} '
            players = Player.objects.raw(txt.format(s))
            Heading = "Successfully Payments"

            count = 0

            for p in players:
                count = count+1
        elif id == "failed":

            txt = 'select *  from (select *  from `registration_player` where `status`="failed" and `tournament_city_id`={})  as r  WHERE NOT EXISTS (SELECT * FROM `registration_player`a where  r.`mobile`= a.`mobile` and a.`status`="success")  group by `mobile`  '
            players = Player.objects.raw(txt.format(s))

            count = 0
            for p in players:
                count = count+1
            Heading = "Failed Payments"

        elif id == "not_initiated":
            txt = 'select *  from (select * from `registration_player` where `tournament_city_id`={})  as r  WHERE NOT EXISTS (SELECT * FROM `registration_player`a where r.`mobile`= a.`mobile` and (a.`status`="success" or a.`status`="failed" ))group by `mobile`'
            players = Player.objects.raw(txt.format(s))

            Heading = " Payments not initiated"
            count = 0
            for i in players:
                count = count+1
        
        return render(request, "payment_status.html", {"players": players, "cityName": cityName, "Heading": Heading, "count": count, "pcity": pcity, "id": id})


def payment_citywise_status(request):

    if (request.method == 'POST'):
        city = request.POST.getlist('city')[0]

        txt = 'select *  from (select *  from `registration_player` where `status`="failed" and `tournament_city_id`={})  as r  WHERE NOT EXISTS (SELECT * FROM `registration_player`a where  r.`mobile`= a.`mobile` and a.`status`="success")  group by `mobile`  '
        players = Player.objects.raw(txt.format(city))
        
       
       
        return HttpResponse("")
