# -*- coding: utf-8 -*-
import datetime
from django.db.models import Max
from models import Gsb_exc

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
                raise Gsb_exc('attention ce ne peut pas etre qu\'un objet date')

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

    def max(self, o, defaut = '0', champ = 'id'):
        '''recupere le max d'un queryset'''
        q = o.aggregate(id = Max(champ))[champ]
        if q is None:
            return defaut
        else:
            return str(q)
    def str(self, o, defaut = '0', membre = 'id'):
        '''renvoie id d'un objet avec la gestion des null
        @param defaut: la reponse si neant
        @param membre: l'attribut a demander si pas neant'''
        if o:
            return str(o.id)
        else:
            return str(defaut)
