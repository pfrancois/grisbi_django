# -*- coding: utf-8 -*-
from __future__ import absolute_import
import datetime
import time
import decimal
import calendar
import csv
import codecs

from django.db.models import Max
from django.core.exceptions import ObjectDoesNotExist


class Format:
    """ classe compose de methodes de classes qui permet le formatage des donnees"""

    @staticmethod
    def date(s, defaut="0/0/0"):
        """
        fonction qui transforme un object date en une chaine AA/MM/JJJJ
        @param s:objet datetime
        @param defaut: format a transformer, par defaut c'est AA/MM/JJJ
        """
        if s is None:
            return defaut
        else:
            if isinstance(s, datetime.date):
                s = s.strftime('%d/%m/%Y')
                result = []
                tab = s.split("/")
                for partie in tab:
                    if partie[0] == '0':  # transform 01/01/2010 en 1/1/2010
                        partie = partie[1:]
                    result.append(partie)
                return "/".join(result)
            else:
                raise TypeError('attention ce ne peut pas etre qu\'un objet date')

    @staticmethod
    def bool(s, defaut='0'):
        """format un bool en 0 ou 1 avec gestion des null et gestion des 0 sous forme de chaine de caractere
        @param s:objet bool
        @param defaut: format a transformer, par defaut c'est 0
        """
        if s is None:
            return defaut
        else:
            if isinstance(s, bool):
                # c'est ici le principe
                return str(int(s))
            try:
                i = int("%s" % s)
                if not i:
                    return '0'
                else:
                    return '1'
            except ValueError:
                return str(int(bool(s)))

    @staticmethod
    def float(s):
        """ convertit un float en string 10,7"""
        s = "%10.7f" % s
        return s.replace('.', ',').strip()

    @staticmethod
    def type(liste, s, defaut='0'):
        """convertit un indice d'une liste par une string
        @param liste: liste a utiliser
        @param s: string comprenand le truc a chercher dans la liste
        @param defaut: reponse par defaut"""
        liste = [str(b[0]) for b in liste]
        try:
            s = str(liste.index(s) + 1)
        except ValueError:  # on en un ca par defaut
            s = defaut
        return s

    @staticmethod
    def max(query, defaut='0', champ='id'):
        """recupere le max d'un queryset"""
        agg = query.aggregate(id=Max(champ))['id']
        if agg is None:
            return defaut
        else:
            return str(agg)

    @staticmethod
    def str(obj, defaut='0', membre='id'):
        """renvoie id d'un objet avec la gestion des null
        @param obj: l'objet a interroger
        @param defaut: la reponse si neant ou inexistant
        @param membre: l'attribut a demander si pas neant"""
        try:
            retour = unicode(getattr(obj, membre))
            if retour[-1] == ":":
                retour = retour[0:-1]
        except (AttributeError, ObjectDoesNotExist):
            retour = unicode(defaut)
        retour = retour.strip()
        return retour


def validrib(banque, guichet, compte, cle):
    """fonction qui verifie la validite de la cle rib
        @return bool """
    # http://fr.wikipedia.org/wiki/Clé_RIB#V.C3.A9rifier_un_RIB_avec_une_formule_Excel
    lettres = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    chiffres = "12345678912345678923456789"
    # subst letters if needed
    banque = unicode(banque)
    guichet = unicode(guichet)
    compte = unicode(compte)
    cle = unicode(cle)
    if len(banque) > 5 or len(guichet) > 5 or len(compte) > 11 or len(cle) > 2:
        raise ValueError
    for char in compte:
        if char in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ':
            achar = char.upper()
            achiffre = chiffres[lettres.find(achar)]
            compte = compte.replace(char, achiffre)
    reste = (89 * int(banque) + 15 * int(guichet) + 3 * int(compte)) % 97
    ccle = 97 - reste
    return ccle == int(cle)


def validinsee(insee, cle):
    """fonction qui verifie la valide de la cle insee
    @return bool"""
    # http://fr.wikipedia.org/wiki/Numero_de_Securite_sociale#Unicit.C3.A9
    # gestion numeros corses
    insee = str(insee)
    insee = insee.replace('A', '0')
    insee = insee.replace('B', '0')
    reste = int(insee) % 97
    return (97 - reste) == int(cle)


def datefr2datesql(chaine):
    """fonction qui transforme une date fr en date sql
    si la date est invalide renvoie none
    """
    temps = time.strptime(str(chaine), "%d/%m/%Y")
    return "{annee}-{mois}-{jour}".format(annee=temps[0], mois=temps[1], jour=temps[2])

def is_number(s):
    """fonction qui verifie si ca a l'apparence d'un nombre"""
    try:
        n = float(s)  # for int, long and float
        if n == "nan" or n == "inf" or n == "-inf" :
            return False
    except ValueError:
        try:
            complex(s)  # for complex
        except ValueError:
            return False
    return True

def fr2decimal(s):
    """fonction qui renvoie un decimal en partant d'un nombre francais"""
    s = str(s)
    s = s.replace(',', '.')
    s = s.replace(' ', '')
    return decimal.Decimal(s)

def strpdate(end_date, fmt="%Y-%m-%d"):
    """@param s: YYYY-MM-DD
    attention si s est None ou impossible renvoie None"""
    if end_date is not None:
        end_date = time.strptime(end_date, fmt)
        return datetime.date(*end_date[0:3])
    else:
        return datetime.date(1, 1, 1)

# utilise pour mock et les test
def today():
    return datetime.date.today()

# utilise pour mock et les test
def now():
    return datetime.datetime.now()


def addmonths(sourcedate, months, last=False, first=False):
    """renvoie le premier jour du mois ou le dernier si option"""
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month / 12
    month = month % 12 + 1
    if last:
        day = calendar.monthrange(year, month)[1]
    elif first:
        day = 1
    else:
        day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)


class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """

    def __init__(self, fich, encoding):
        self.reader = codecs.getreader(encoding)(fich)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")


class Excel_csv(csv.Dialect):
    """Describe the usual properties of Excel-generated CSV files."""
    delimiter = ';'
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = "\r\n"
    quoting = csv.QUOTE_MINIMAL

csv.register_dialect("excel_csv", Excel_csv)


    
