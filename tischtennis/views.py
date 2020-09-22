from django.shortcuts import render,redirect
from django.http import HttpResponseRedirect,HttpResponse
from .forms import TurnierForm,SpieleForm
from .models import Turnier,TeilnehmerListe,Turnierspiele
import xmltodict
from operator import itemgetter

def create_turnier(request):
    turniere = Turnier.objects.filter(veranstalter_id=1).values()
    if request.method == 'POST':
        form = TurnierForm(request.POST)
        if form.is_valid():
            try:
                Turnier(veranstalter_id=form.cleaned_data['veranstalter_id'], turnier_id=form.cleaned_data['turnier_id']).save()
            except:
                return render(request,'racesoftware/turnier_erstellen.html',{'form': TurnierForm(initial={'xmldatei': '/home/Afkor/tischtennis/racesoftware/tournamentExport.xml'}), 'error':'Error'})
            file = open('/home/Afkor/tischtennis/racesoftware/tournamentExport.xml')
            data = file.read()
            file.close()
            data = xmltodict.parse(data)
            for x,y in enumerate(data['tournament']['competition']['players']['player']):
                TeilnehmerListe(
                    turnier_id=Turnier.objects.get(turnier_id=form.cleaned_data['turnier_id']),
                    player_id=data['tournament']['competition']['players']['player'][x]['@id'],
                    licence_nr=data['tournament']['competition']['players']['player'][x]['person']['@licence-nr'],
                    lastname=data['tournament']['competition']['players']['player'][x]['person']['@lastname'],
                    club_name=data['tournament']['competition']['players']['player'][x]['person']['@club-name'],
                    sex=data['tournament']['competition']['players']['player'][x]['person']['@sex'],
                    ttr=data['tournament']['competition']['players']['player'][x]['person']['@ttr'],
                    internal_nr=data['tournament']['competition']['players']['player'][x]['person']['@internal-nr'],
                    firstname=data['tournament']['competition']['players']['player'][x]['person']['@firstname'],
                    club_nr=data['tournament']['competition']['players']['player'][x]['person']['@club-nr'],
                    birthyear=data['tournament']['competition']['players']['player'][x]['person']['@birthyear'],
                    verband=data['tournament']['competition']['players']['player'][x]['person']['@club-federation-nickname']
                ).save()
            create_erste_runde(form.cleaned_data['turnier_id'])
            return redirect(request.path_info)
    return render(request,'racesoftware/turnier_erstellen.html',{'form': TurnierForm(initial={'xmldatei': '/home/Afkor/tischtennis/racesoftware/tournamentExport.xml'}),'turniere':turniere})

def delete_turnier(request,tourny_id):
    Turnier.objects.filter(turnier_id=tourny_id).delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def show_teilnehmer(request,tourny_id):
    interne_turnier_id = Turnier.objects.filter(turnier_id=tourny_id)[0]
    teilnehmer = TeilnehmerListe.objects.filter(turnier_id=interne_turnier_id)
    runde = welche_runde(interne_turnier_id) #damit man Spieler in der aktuellen Runde für die nächste ein-/austragen kann
    return render(request,'racesoftware/teilnehmer_zeigen.html',{'teilnehmer': teilnehmer ,'aufgehoert':runde})

def drop_teilnehmer(request,tourny_id,player_id,runde):
    interne_turnier_id = Turnier.objects.filter(turnier_id=tourny_id)[0]
    teilnehmer = TeilnehmerListe.objects.filter(turnier_id=interne_turnier_id,id=player_id)
    aktuelle_runde = welche_runde(interne_turnier_id)
    if aktuelle_runde != runde:
        return HttpResponse("Fehler mit der Runde!")
    if teilnehmer.values()[0]['aufgehoert'] == runde:
        updater={'aufgehoert': None}
        TeilnehmerListe.objects.filter(id=player_id).update(**updater)
    elif teilnehmer.values()[0]['aufgehoert'] == None:
        updater={'aufgehoert': runde}
        TeilnehmerListe.objects.filter(id=player_id).update(**updater)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def create_auslosung(request,tourny_id):
    interne_turnier_id = Turnier.objects.filter(turnier_id=tourny_id)[0]
    try:
        aktuelle_runde = welche_runde(interne_turnier_id)
        stimmtdas = welche_runde(interne_turnier_id,"Letzte abgeschlossene Runde")
        if not aktuelle_runde:
            create_erste_runde(tourny_id)
        if not stimmtdas:
            create_runde(request,tourny_id,aktuelle_runde+1)
    except:
        create_runde(request,tourny_id,0)
    return HttpResponseRedirect(f"/race/{tourny_id}/show/")

def create_runde(request,tourny_id,runde):
    tabelle = calc_platzierung(tourny_id,runde)
    interne_turnier_id = Turnier.objects.filter(turnier_id=tourny_id)[0]
    aktive_spieler = TeilnehmerListe.objects.filter(aufgehoert__lt=runde,turnier_id=interne_turnier_id).values_list(flat=True)
    tabelle = [spieler_daten for spieler_daten in tabelle if spieler_daten['id'] not in aktive_spieler]
    match_try=[]
    try_count=0 # Damit man einen Überblick wie oft Auslosungen failen.
    not_matched=True
    while not_matched == True:
        matchups = []
        siege=[[] for _ in range(runde)]
        for spieler_daten in tabelle:
            if spieler_daten['id'] == tabelle[0]['id']:
                spieler_daten['gegner']=spieler_daten['gegner']+match_try
            siege[spieler_daten['siege']].append([spieler_daten['internal_nr'],spieler_daten['gegner']])
        match_try=[]
        while sum([len(x) for x in siege]) > 1:
            siege,matchups = matchups_finder(siege,matchups)
            if siege=="Fehler":
                match_try.append(matchups)
                break
        if siege!="Fehler":
            not_matched=False
            try_count+=1
        else:
            if matchups == str(99):
                print("Wir haben %s Versuche unternommen"%try_count)
                not_matched=False
    if save_matchup(matchups,tourny_id,runde):
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        return HttpResponse('<h1>Hoppla Fehler irgendwo</h1>')

def delete_runde(request,tourny_id,runde):
    Turnierspiele.objects.filter(turnier_id=Turnier.objects.get(turnier_id=tourny_id).id,runde__gte=runde).delete()
    if runde == 1:
        create_erste_runde(tourny_id)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def welche_runde(interne_turnier_id,satz=None):
    if not satz:
        try:
            return Turnierspiele.objects.filter(turnier_id=interne_turnier_id).order_by('-runde').values()[0]['runde']
        except:
            return None
    else:
        try:
            return Turnierspiele.objects.filter(turnier_id=interne_turnier_id,satz1=None).order_by('-runde').values()[0]['runde']
        except:
            return None

def show_tabelle(request,tourny_id,runde=None):
    if not runde:
        interne_turnier_id = Turnier.objects.filter(turnier_id=tourny_id)[0]
        runde = welche_runde(interne_turnier_id)
    tabelle = calc_platzierung(tourny_id,runde)
    return render(request,'racesoftware/tabelle_anzeigen.html',{'tabelle':tabelle,'runde':runde})

def show_spiele(request,tourny_id,runde=None):
    interne_turnier_id = Turnier.objects.filter(turnier_id=tourny_id)[0]
    preurl= '/'.join(request.path.split("/")[1:4])
    preurl2='/'.join(request.path.split("/")[1:3])
    if not runde:
        # In welcher Runde sind wir?
        runde = welche_runde(interne_turnier_id,"Letzte abgeschlossene Runde")
        if not runde:
            runde = welche_runde(interne_turnier_id)
            return render(request,'racesoftware/runde_eingeben.html',{'naechste_runde':runde,'url':f"{request.META['HTTP_HOST']}/{preurl2}/"})
        if runde == 6:
            #Müsste angepasst werden mit Variable falls Standart 6 Runden
            #geaendert werden soll
            return HttpResponse('Moechten Sie das Turnier abschliessen?')
        #createAuslosung(request,tourny_id)


    platzierung = calc_platzierung(tourny_id,runde-1)

    offene_Partien = Turnierspiele.objects.filter(runde=runde,turnier_id=interne_turnier_id).values()
    count=0
    loopy = {}
    for x in offene_Partien:
        hmhm=offene_Partien[count]['id']
        if offene_Partien[count]['satz1'] == None:
            offen = SpieleForm()
            ein="aus"
            #runde_fertig=0
        else:
            sieg1=0
            sieg2=0
            offen = [offene_Partien[count]['satz1'],offene_Partien[count]['satz2'],offene_Partien[count]['satz3'],offene_Partien[count]['satz4'],offene_Partien[count]['satz5']]
            for bar,foo in enumerate(offen):
                if foo == "-0":
                    sieg2+=1
                    offen[bar] = "0:11"
                elif foo == None:
                    offen[bar] = ""
                else:
                    if int(foo) >= 0:
                        sieg1+=1
                        if int(foo) > 9:
                            offen[bar] = "%s:%s" % (int(foo)+2,foo)
                        else:
                            offen[bar] = "11:%s" % (foo)
                    else:
                        sieg2+=1
                        if int(foo) < -9:
                            offen[bar] = "%s:%s" % (-1*int(foo),int(foo)+2)
                        else:
                            offen[bar] = "%s:11" % (-1*int(foo))
            offen.append("%s:%s"%(sieg1,sieg2))
            ein="ein"
        count+=1
        fields={}
        player1 = TeilnehmerListe.objects.filter(internal_nr=x['player1'],turnier_id=interne_turnier_id).values()[0]
        player2 = TeilnehmerListe.objects.filter(internal_nr=x['player2'],turnier_id=interne_turnier_id).values()[0]
        player1_platzierungs_index = next((index for (index, d) in enumerate(platzierung) if d["lastname"] == player1['lastname']), None)
        player2_platzierungs_index = next((index for (index, d) in enumerate(platzierung) if d["lastname"] == player2['lastname']), None)
        fields['Spieler1'] =  f"{player1['firstname']} {player1['lastname']} ({player1_platzierungs_index+1}. {platzierung[player1_platzierungs_index]['siege']}-{platzierung[player1_platzierungs_index]['niederlage']})"
        fields['Spieler2'] = f"{player2['firstname']} {player2['lastname']} ({player2_platzierungs_index+1}. {platzierung[player2_platzierungs_index]['siege']}-{platzierung[player2_platzierungs_index]['niederlage']})"
        fields['Tisch'] = count
        loopy[hmhm]={'printout':offen ,'printout2':fields,'printout3': ein}
    return render(request,'racesoftware/runde_eingeben.html',{'printout':loopy,'runde':runde,'url':f"{request.META['HTTP_HOST']}/{preurl}/"})

def save_partie(request,tourny_id,game_id):
    sieg1 = 0
    sieg2 = 0
    updater = {}
    if request.method == 'POST':
        for x in request.POST:
            if "satz" in x:
                if request.POST[x] == "":
                    continue
                if request.POST[x] == "-0":
                    sieg2+=2
                    updater[x]=request.POST[x]
                else:
                    if int(request.POST[x]) >= 0:
                        sieg1+=1
                        updater[x]=request.POST[x]
                    elif 0 > int(request.POST[x]):
                        sieg2+=1
                        updater[x]=request.POST[x]
            if (sieg1 > 2) or (sieg2 > 2):
                break
        if (sieg1 < 3) and (sieg2 < 3):
            return HttpResponse("Wir spielen 3 Gewinnsätze")
        try:
            Turnierspiele.objects.filter(id=game_id).update(**updater)
            return redirect(request.path_info[:-len(str(game_id))-1])
        except:
            return HttpResponse('<h1>Hoppla Fehler irgendwo</hr>')

def delete_ergebnis_partie(request,tourny_id,game_id):
    updater = {"satz1":None,"satz2":None,"satz3":None,"satz4":None,"satz5":None}
    Turnierspiele.objects.filter(id=game_id).update(**updater)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def calc_platzierung(tourneyid,runde=None):
    interne_turnier_id = Turnier.objects.filter(turnier_id=tourneyid)[0]
    if runde:
        alle_spiele = Turnierspiele.objects.filter(turnier_id=interne_turnier_id,runde__lte=runde).values()
    else:
        alle_spiele = Turnierspiele.objects.filter(turnier_id=interne_turnier_id).values()
        runde=0
    try:
        if runde == 0:
            alle_teilnehmer = [{'internal_nr':x['internal_nr'],'id':x['id'],'lastname':x['lastname'],'siege':0,'niederlage':0,'siegdif':0,'plussatz':0,'minussatz':0,'satzdif':0,'plusball':0,'minusball':0,'balldif':0,'gegner':[],'buchholz':0,'feinbuchholz':0} for x in TeilnehmerListe.objects.filter(turnier_id=interne_turnier_id).order_by('-ttr').values()]
            return alle_teilnehmer
        alle_teilnehmer = {x['internal_nr']:x['id'] for x in TeilnehmerListe.objects.filter(turnier_id=interne_turnier_id).order_by('-ttr').values()}
        for x,y in alle_teilnehmer.items():
            plusball=0
            minusball=0
            sieg=0
            niederlage=0
            gegner=[]
            plussatz=0
            minussatz=0
            for z in alle_spiele:
                win=0
                loss=0
                for sd in [z['satz1'],z['satz2'],z['satz3'],z['satz4'],z['satz5']]:
                    if x == z['player1']:
                        if sd == None or sd == "":
                            pass
                        elif sd == "-0":
                            loss+=1
                            minusball+=11
                        elif int(sd) >= 0:
                            win+=1
                            if int(sd) >= 9:
                                plusball+=int(sd)+2
                                minusball+=int(sd)
                            else:
                                plusball+=11
                                minusball+=int(sd)
                        elif int(sd) < 0:
                            loss+=1
                            if int(sd) <= -9:
                                minusball+=-1*int(sd)+2
                                plusball+=-1*int(sd)
                            else:
                                minusball+=11
                                plusball+=-1*int(sd)
                    if x == z['player2']:
                        if sd == None or sd == "":
                            pass
                        elif sd == "-0":
                            win+=1
                            plusball+=11
                        elif int(sd) >= 0:
                            loss+=1
                            if int(sd) >= 9:
                                minusball+=int(sd)+2
                                plusball+=int(sd)
                            else:
                                minusball+=11
                                plusball+=int(sd)
                        elif int(sd) < 0:
                            win+=1
                            if int(sd) <= -9:
                                plusball+=-1*int(sd)+2
                                minusball+=-1*int(sd)
                            else:
                                plusball+=11
                                minusball+=-1*int(sd)
                if z['player1'] == x and z['satz1'] !=None:
                    gegner.append(z['player2'])
                if z['player2'] == x and z['satz1'] !=None:
                    gegner.append(z['player1'])
                if win == 3:
                    sieg+=1
                if loss ==3:
                    niederlage+=1
                plussatz+=win
                minussatz+=loss
                alle_teilnehmer[x]={'id':y,'internal_nr':x,'siege':sieg,'niederlage':niederlage,'siegdif':sieg-niederlage,'plussatz':plussatz,'minussatz':minussatz,'satzdif':plussatz-minussatz,'plusball':plusball,'minusball':minusball,'balldif':plusball-minusball,'gegner':gegner}
        for x,y in alle_teilnehmer.items():
            buchholz=0
            for z in y['gegner']:
                buchholz+=alle_teilnehmer[z]['siege']
            alle_teilnehmer[x]['buchholz']=buchholz
        for x,y in alle_teilnehmer.items():
            feinbuchholz=0
            for z in y['gegner']:
                for zz in alle_teilnehmer[z]['gegner']:
                    feinbuchholz+=alle_teilnehmer[zz]['siege']
            row = TeilnehmerListe.objects.filter(id=y['id']).values()[0]
            alle_teilnehmer[x]['lastname']=row['lastname']
            alle_teilnehmer[x]['feinbuchholz']=feinbuchholz
        temp=[]
        for x in alle_teilnehmer.values():
            temp.append(x)
        rankliste = sorted(temp, key= itemgetter('siegdif','buchholz','feinbuchholz','satzdif','balldif'),reverse=True)
        nicht_ausgestiegen = TeilnehmerListe.objects.filter(turnier_id=interne_turnier_id,aufgehoert=None).values()
        for x,y in enumerate(rankliste):
            rankliste[x]['rank']=x
    except:
        return HttpResponse("Fehler im Try")
    return rankliste

def create_erste_runde(tourneyid):
    interne_turnier_id = Turnier.objects.filter(turnier_id=tourneyid)[0]
    aktive_spieler = TeilnehmerListe.objects.filter(aufgehoert=None,turnier_id=interne_turnier_id).order_by('-ttr').values()
    try:
        Turnierspiele.objects.get(turnier_id=interne_turnier_id)
        #####################################################################################
        # Test ob schon Daten zum Turnier vorliegen, da Runde 1 anders gelost wird als Rest #
        #####################################################################################

    except:
        if len(aktive_spieler) < 9 or len(aktive_spieler) > 16:
            return HttpResponse('<h1>Achtung wir haben nicht zwischen 9-16 Teilnehmer</h1>')
            ##############################################################################
            # Muss noch keine Meldung implementiert werden das zuviel/zuwenig Teilnehmer #
            ##############################################################################

        if (len(aktive_spieler)/2) % 2 == 0:
            for i in range(0,int(len(aktive_spieler)/2)):
                Turnierspiele(
                    turnier_id  = interne_turnier_id,
                    player1     = aktive_spieler[i]['internal_nr'],
                    player2     = aktive_spieler[len(aktive_spieler)-i-1]['internal_nr'],
                    runde       = 1
                ).save()
        else:
            for i in range(0,int(len(aktive_spieler)/2)):
                Turnierspiele(
                    turnier_id  = interne_turnier_id,
                    player1     = aktive_spieler[i]['internal_nr'],
                    player2     = aktive_spieler[len(aktive_spieler)-i-1]['internal_nr'],
                    runde       = 1
                ).save()
            Turnierspiele(
                    turnier_id  = interne_turnier_id,
                    player1     = aktive_spieler[int(len(aktive_spieler)/2)]['internal_nr'],
                    player2     = '',
                    runde       = 1
                ).save()

def save_matchup(matchups,tourneyid,runde):
    interne_turnier_id = Turnier.objects.filter(turnier_id=tourneyid)[0]
    runde2 = welche_runde(interne_turnier_id)
    try:
        if runde==runde2+1:
            for x in matchups:
                Turnierspiele(turnier_id=interne_turnier_id,player1=x[1],player2=x[0],runde=runde).save()
            return True
        return False
    except:
        return False

def matchups_finder(siege,matchups):
    for spieler in reversed(range(len(siege))):
        if len(siege[spieler]) == 0:
            del siege[spieler]
            return (siege,matchups)
        if len(siege[spieler]) % 2 == 0:
            for y in reversed(range(len(siege[spieler]))):
                if y == 0:
                    return nicht_aufgegangen(siege,matchups)
                    continue
                if siege[spieler][y][0] not in siege[spieler][0][1]:
                    matchups.append([siege[spieler][y][0],siege[spieler][0][0]])
                    del siege[spieler][y]
                    del siege[spieler][0]
                    return (siege,matchups)
            return nicht_aufgegangen(siege,matchups)
        else:
            return nicht_aufgegangen(siege,matchups)

def nicht_aufgegangen(siege,matchups):
    niedrige_gruppe = len(siege)-1
    for x in reversed(range(len(siege)-1)):
        for y in range(len(siege[x])):
            if siege[x][y][0] not in siege[niedrige_gruppe][0][1]:
                matchups.append([siege[x][y][0],siege[niedrige_gruppe][0][0]])
                del siege[x][y]
                del siege[niedrige_gruppe][0]
                return (siege,matchups)
    try:
        return "Fehler",matchups[0][0]
    except:
        return "Fehler","99"