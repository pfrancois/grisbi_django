# -*- coding: utf-8 -*-
from __future__ import absolute_import
import datetime
import time
import decimal
import csv
import codecs
import math
import os
import fnmatch
from django.utils import timezone

#from inspector_panel.panels.inspector import debug
import locale
from django.db.models import Max
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import force_unicode
from uuid import uuid4

__all__ = ['FormatException', 'validrib', 'validinsee', 'datefr2datesql', 'is_number', 'fr2decimal',
           'strpdate', 'today', 'now', 'timestamp', 'to_unicode', 'to_id', 'to_bool', 'to_decimal',
           'to_date', 'datetostr', 'booltostr', 'floattostr', 'typetostr', 'idtostr', 'UTF8Recoder', 'Excel_csv',
           'Csv_unicode_reader', 'uuid', 'Excel_csv', 'nulltostr', 'is_onexist', 'switch', 'Compfr',
           'find_files']


class FormatException(Exception):
    """une classe exception qui permet d'affcher tranquillement ce que l'on veut"""
    def __init__(self, message):
        super(FormatException, self).__init__(message)
        self.msg = message

    def __str__(self):
        return self.msg


def uuid():
    """raccourci vers uuid4"""
    return str(uuid4())


class Compfr(object):
    """operateur de comparaison avec un alphabet francais afin de pouvoir trier selon la norme francaise
       que cela soit texte ou unicode"""
    def __init__(self, decod='utf-8'):
        self.decod = decod
        self.loc = locale.getlocale()  # stocker la locale courante
        self.espinsec = u'\xA0'  # espace insécable

    def __call__(self, v1, v2):
        """appel effectif de l'operateur"""
        if isinstance(v1, str) or isinstance(v2, str) or isinstance(v1, unicode) or isinstance(v2, unicode):
            # on convertit en unicode si nécessaire
            if not(isinstance(v1, unicode)):
                if isinstance(v1, str):
                    v1 = v1.decode(self.decod)
                else:
                    v1 = "%s"%v1
                    v1 = v1.decode(self.decod)
            if not(isinstance(v2, unicode)):
                if isinstance(v2, str):
                    v2 = v2.decode(self.decod)
                else:
                    v2 = "%s"%v2
                    v2 = v2.decode(self.decod)

            # on retire les tirets et les blancs insécables
            v1 = v1.replace(u'-', u'')
            v1 = v1.replace(self.espinsec, u'')
            v2 = v2.replace(u'-', '')
            v2 = v2.replace(self.espinsec, u'')

            # on retourne le résultat de la comparaison
            locale.setlocale(locale.LC_ALL, '')
            comp = locale.strcoll(v1, v2)
            locale.setlocale(locale.LC_ALL, self.loc)  # retour à la locale courante

            return comp  # retour du résultat de la comparaison
        else:
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
            else:
                return 0


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
    si la date est invalide renvoie None
    """
    try:
        temps = time.strptime(str(chaine), "%d/%m/%Y")
        return "{annee}-{mois}-{jour}".format(annee=temps[0], mois=temps[1], jour=temps[2])
    except ValueError:
        return None


def is_number(s):
    """fonction qui verifie si ca a l'apparence d'un nombre"""
    try:
        n = float(s)  # for int, long and float
        if math.isnan(n) or math.isinf(n):
            return False
    except ValueError:
        try:
            complex(s)  # for complex
        except ValueError:
            return False
    return True


def fr2decimal(s):
    """fonction qui renvoie un decimal en partant d'un nombre francais"""
    s = force_unicode(s).strip()
    s = s.replace(',', '.')
    s = s.replace(' ', '')
    return decimal.Decimal(s)


def strpdate(end_date, fmt="%Y-%m-%d"):
    """@param end_date: date
        @param fmt: format de la date
    attention si s est None ou impossible renvoie None"""
    if isinstance(end_date, datetime.date) or isinstance(end_date, datetime.datetime):
        end_date = end_date.strftime(fmt)
    if end_date is not None:
        end_date = time.strptime(end_date, fmt)
        return datetime.date(*end_date[0:3])
    else:
        return datetime.date(1, 1, 1)


def now(utc=True):
    """ now utilise pour mock dans les tests """
    if utc:
        return timezone.now()
    else:
        return timezone.localtime(timezone.now())


def today():
    """date utilise pour mock et les test
    """
    return now().date()

def timestamp():
    """ le timestamp de now utilise pour mock dans les tests """
    return dt2timestamp(now())


def dt2timestamp(date):
    """renvoi le timestamp d'une datetime"""
    return time.mktime(date.timetuple())


#------------------------------------format d'entree---------------------------------
def to_unicode(var, defaut=''):
    """a partir d'une unicode"""
    if var is None:
        return defaut
    var = force_unicode(var).strip()
    if var == "":
        return defaut
    try:
        if float(var) == 0:
            return defaut
        else:
            return var
    except ValueError:
        return var


def to_id(var):
    """renvoie un entier positif"""
    if var is None:
        return None
    var = force_unicode(var).strip()
    try:
        if var == "" or int(var) == 0 or var == "False":
            return None
        else:
            return int(var)
    except ValueError:
        raise FormatException('probleme: "%s" n\'est pas un nombre entier' % var)


def to_bool(var):
    """renvoie un bool"""
    if var is None:
        return False
    if var is True or var is False:
        return var

    var = force_unicode(var).strip()
    if var == "" or var == 0 or var == "0" or bool(var) is False:
        return False
    else:
        return True


def to_decimal(var):
    """renvoie un decimal"""
    if var is None:
        return 0
    var = force_unicode(var).strip()
    try:
        return fr2decimal(var)  # si il y a une exception il est renvoyé 0
    except decimal.InvalidOperation:
        return 0


def to_date(var, format_date="%d/%m/%Y"):
    """renvoie une date"""
    try:
        return strpdate(var, format_date)
    except ValueError:
        raise FormatException('"%s" n\'en pas est une date' % var)


#-------------------------------format de sortie-----------------------------
def datetostr(s, defaut="0/0/0", param='%d/%m/%Y', gsb=False):
    """
    fonction qui transforme un object date en une chaine AA/MM/JJJJ
    @param s:objet datetime
    @param defaut: format a transformer, par defaut c'est AA/MM/JJJJ
    """
    if s is None:
        return defaut
    else:
        if isinstance(s, datetime.date):
            s = s.strftime(param)
            if gsb:
                result = []
                tab = s.split("/")
                for partie in tab:
                    if partie[0] == '0':  # transform 01/01/2010 en 1/1/2010
                        partie = partie[1:]
                    result.append(partie)
                return "/".join(result)
            else:
                return s
        else:
            raise FormatException(u"attention ce ne peut pas etre qu'un objet date et c'est un %s (%s)" % (type(s), s))


def booltostr(s, defaut='0'):
    """format un bool en 0 ou 1 avec gestion des null et gestion des 0 sous forme de chaine de caractere
    @param s:objet bool
    @param defaut: format a transformer, par defaut c'est 0
    """
    if s is None:
        return defaut
    else:
        if isinstance(s, bool):
            # c'est ici le principe
            return force_unicode(int(s))
        try:
            i = int("%s" % s)
            if not i:
                return '0'
            else:
                return '1'
        except ValueError:
            return force_unicode(int(bool(s)))


def floattostr(s, nb_digit=7):
    """ convertit un float en string 10,7"""
    s = "{0:0.{1}f}".format(s, nb_digit)
    return s.replace('.', ',').strip()


def typetostr(liste, s, defaut='0'):
    """convertit un indice d'une liste par une string
    @param liste: liste a utiliser
    @param s: string comprenand le truc a chercher dans la liste
    @param defaut: reponse par defaut"""
    liste = [force_unicode(b[0]) for b in liste]
    try:
        s = force_unicode(liste.index(s) + 1)
    except ValueError:  # on a un cas à defaut
        s = defaut
    return s


def maxtostr(query, defaut='0', champ='id'):
    """recupere le max d'un queryset"""
    agg = query.aggregate(id=Max(champ))['id']
    if agg is None:
        return defaut
    else:
        return str(agg)


def idtostr(obj, membre='id', defaut='0'):
    """renvoie id d'un objet avec la gestion des null
    @param obj: l'objet a interroger
    @param defaut: la reponse si neant ou inexistant
    @param membre: l'attribut a demander si pas neant"""
    try:
        if getattr(obj, membre) is not None:
            retour = unicode(getattr(obj, membre))
            if retour != '':
                if retour[-1] == ":":#cas des categories
                    retour = retour[0:-1]
        else:
            retour = unicode(defaut)
    except (AttributeError, ObjectDoesNotExist):
        retour = unicode(defaut)

    retour = retour.strip()
    return retour


def nulltostr(s):
    if s == '':
        return 'NULL'
    else:
        return s


#------------------fonction basiques pour lecture ecriture------"""
class UTF8Recoder(object):
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """

    def __init__(self, fich, encoding):
        self.reader = codecs.getreader(encoding)(fich)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class Excel_csv(object, csv.Dialect):
    """Describe the usual properties of Excel-generated CSV files."""
    delimiter = ';'
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = "\r\n"
    quoting = csv.QUOTE_MINIMAL


csv.register_dialect("excel_csv", Excel_csv)


class Csv_unicode_reader(object):
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """
    champs = None

    def __init__(self, fich, dialect=Excel_csv, encoding="utf-8", **kwds):  # pylint: disable=W0231
        self.line_num = 0
        fich = UTF8Recoder(fich, encoding)
        self.reader = csv.DictReader(fich, dialect=dialect, fieldnames=self.champs, **kwds)

    def next(self):
        self.line_num += 1
        self.row = self.reader.next()
        return self

    def __iter__(self):
        return self


def is_onexist(objet, attribut):
    try:
        if getattr(objet, attribut, None) is not None:
            return True
        else:
            return False
    except ObjectDoesNotExist:
        return False


    # switch http://code.activestate.com/recipes/410692/"""
def find_files(path, recherche='*.*'):
    """trouve recursivement les fichiers voulus"""
    for root, dirs, files in os.walk(path):
        for basename in files:
            if fnmatch.fnmatch(basename, recherche):
                filename = os.path.join(root, basename)
                yield filename

