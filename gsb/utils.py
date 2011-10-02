# -*- coding: utf-8 -*-
import datetime
import time
import decimal
from django.db.models import Max

class Format:
    """ classe compose de methodes de classes qui permet le formatage des donnees"""
    def date(self, s, defaut = "0/0/0"):
        '''
        fonction qui transforme un object date en une chaine AA/MM/JJJJ
        @param s:objet datetime
        @param defaut: format a transformer, par defaut c'est AA/MM/JJJ
        '''
        if s is None:
            return defaut
        else:
            if isinstance(s, datetime.date):
                s = s.strftime('%d/%m/%Y')
                result = []
                tab = s.split("/")
                for partie in tab:#transform 01/01/2010 en 1/1/2010
                    if partie[0] == '0':
                        partie = partie[1:]
                    result.append(partie)
                return "/".join(result)
            else:
                raise TypeError('attention ce ne peut pas etre qu\'un objet date')

    def bool(self, s, defaut = '0'):
        '''format un bool en 0 ou 1 avec gestion des null
        @param s:objet bool
        @param defaut: format a transformer, par defaut c'est 0

        '''
        if s is None:
            return defaut
        else:
            if isinstance(s, bool):
                return str(int(s))
            else:
                return str(int(bool(s)))

    def float(self, s):
        ''' convertit un float en string 10,7'''
        s = "%10.7f" % s
        return s.replace('.', ',').strip()

    def type(self, liste, s, defaut = '0'):
        '''convertit un indice d'une liste par une string
        @param liste: liste a utiliser
        @param s: string comprenand le truc a chercher dans la liste
        @param defaut: reponse par defaut'''
        liste = [str(b[0]) for b in liste]
        try:
            s = str(liste.index(s))
        except ValueError:##on en un ca par defaut
            s = defaut
        return s

    def max(self, query, defaut = '0', champ = 'id'):
        '''recupere le max d'un queryset'''
        agg = query.aggregate(id = Max(champ))[champ]
        if agg is None:
            return defaut
        else:
            return str(agg)
        
    def str(self, obj, defaut = '0', membre = 'id'):
        '''renvoie id d'un objet avec la gestion des null
        @param obj: l'objet a interroger
        @param defaut: la reponse si neant
        @param membre: l'attribut a demander si pas neant'''
        try:
            return str(getattr(obj, membre))
        except AttributeError:
            return str(defaut)

def validrib(banque, guichet, compte, cle):
    # http://fr.wikipedia.org/wiki/ClĂŠ_RIB#V.C3.A9rifier_un_RIB_avec_une_formule_Excel
    lettres = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    chiffres = "12345678912345678923456789"
    # subst letters if needed
    for char in compte:
        if char in ['abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ']:
            achar = char.upper()
            achiffre = chiffres[lettres.find(achar)]
            compte = compte.replace(char, achiffre)
    reste = (89 * int(banque) + 15 * int(guichet) + 3 * int(compte)) % 97
    ccle = 97 - reste
    return (ccle == int(cle))

def validinsee(insee, cle):
    # http://fr.wikipedia.org/wiki/Numero_de_Securite_sociale#Unicit.C3.A9
    # gestion numeros corses
    insee = insee.replace('A', 0)
    insee = insee.replace('B', 0)
    reste = int(insee) % 97
    return ((97 - reste) == int(cle))

def datefr2datesql(chaine):
    try:
        temps = time.strptime(str(chaine), "%d/%m/%Y")
        return "{annee}-{mois}-{jour}".format(annee = temps[0], mois = temps[1], jour = temps[2])
    except ValueError:
        return None


def fr2decimal(s):
    if s == "0,0000000":
        return decimal.Decimal('0')
    if s is not None:
        return decimal.Decimal(str(s).replace(',', '.'))
    else:
        return None
