# -*- coding: utf-8 -*-

from django.utils import timezone
import datetime
import time
import decimal
import csv
import unicodedata
import math
import os
import fnmatch


from django.db.models import Max
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import force_text, smart_text
from uuid import uuid4


class utils_Exception(Exception):
    """une classe exception qui permet d'affcher tranquillement ce que l'on veut"""

    def __init__(self, message):
        super(utils_Exception, self).__init__(message)
        self.msg = smart_text(message)

    def __str__(self):
        return self.msg


class FormatException(utils_Exception):
    pass


def uuid():
    """raccourci vers uuid4"""
    return str(uuid4())


def validrib(banque, guichet, compte, cle):
    """fonction qui verifie la validite de la cle rib
        @return bool """
    # http://fr.wikipedia.org/wiki/Clé_RIB#V.C3.A9rifier_un_RIB_avec_une_formule_Excel
    lettres = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    chiffres = "12345678912345678923456789"
    # subst letters if needed
    banque = str(banque)
    guichet = str(guichet)
    compte = str(compte)
    cle = str(cle)
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
    """fonction qui verifie la validite de la cle insee
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
    s = force_text(s).strip()
    s = s.replace(',', '.')
    s = s.replace(' ', '')
    return decimal.Decimal(s)


def strpdate(end_date, fmt="%Y-%m-%d"):
    """ renvoie la date
        @param end_date: date
        @param fmt: format de la date
    attention si s est None ou impossible renvoie None"""
    if isinstance(end_date, datetime.date) or isinstance(end_date, datetime.datetime):
        end_date = end_date.strftime(fmt)
    if end_date is not None:
        end_date = time.strptime(end_date, fmt)
        return datetime.date(*end_date[0:3])
    else:
        return datetime.date(1, 1, 1)


def now():
    """ now utilise pour mock dans les tests """
    dt = timezone.now()
    return dt


def today():
    """date utilise pour mock et les test
    """
    return now().date()


def utctime(t):
    if timezone.is_aware(t):
        return timezone.localtime(t, timezone=timezone.utc)
    else:
        return timezone.localtime(timezone.make_aware(t), timezone=timezone.utc)


def sort_fr(t):
    chnorm = unicodedata.normalize('NFKD', str(t))
    return "".join([c for c in chnorm if not unicodedata.combining(c)])


#------------------------------------format d'entree---------------------------------
def to_unicode(var, defaut=''):
    """a partir d'une unicode"""
    if var is None:
        return defaut
    var = force_text(var).strip()
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
    var = force_text(var).strip()
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
    var = force_text(var).strip()
    if var == "" or var == 0 or var == "0" or bool(var) is False:
        return False
    else:
        return True


def to_decimal(var):
    """renvoie un decimal"""
    if var is None:
        return 0
    var = force_text(var).strip()
    try:
        return fr2decimal(var)  # si il y a une exception il est renvoyé 0
    except decimal.InvalidOperation:
        return 0


def to_date(var, format_date="%d/%m/%Y"):
    """renvoie une date"""
    try:
        return strpdate(var, format_date)
    except ValueError:
        raise FormatException('"%s" n\'est pas est une date' % var)


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
            raise FormatException("attention ce ne peut pas etre qu'un objet date et c'est un %s (%s)" % (type(s), s))


def datetotimestamp(d):
    if not isinstance(d, datetime.datetime) and isinstance(d, datetime.date):
        return datetime.datetime.combine(d, datetime.datetime.min.time()).timestamp()
    if isinstance(d, datetime.datetime):
        if timezone.is_aware(d):
            return timezone.localtime(d, timezone=timezone.utc).timestamp()
        else:
            return d.timestamp()
    else:
        return 0


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
            return force_text(int(s))
        try:
            i = int("%s" % s)
            if not i:
                return '0'
            else:
                return '1'
        except ValueError:
            return force_text(int(bool(s)))


def floattostr(s, nb_digit=7):
    """ convertit un float en string 10,7"""
    s = "{0:0.{1}f}".format(s, nb_digit)
    return s.replace('.', ',').strip()


def typetostr(liste, s, defaut='0'):
    """convertit un indice d'une liste par une string
    @param liste: liste a utiliser
    @param s: string comprenand le truc a chercher dans la liste
    @param defaut: reponse par defaut"""
    liste = [force_text(b[0]) for b in liste]
    try:
        s = force_text(liste.index(s) + 1)
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
            retour = str(getattr(obj, membre))
            if retour != '':
                if retour[-1] == ":":  # cas des categories
                    retour = retour[0:-1]
        else:
            retour = str(defaut)
    except (AttributeError, ObjectDoesNotExist):
        retour = str(defaut)
    retour = retour.strip()
    return retour


def nulltostr(s):
    if s == '':
        return 'NULL'
    else:
        return s


#------------------fonction basiques pour lecture ecriture------"""
class Excel_csv(csv.Dialect):

    """Describe the usual properties of Excel-generated CSV files."""
    delimiter = ';'
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = "\r\n"
    quoting = csv.QUOTE_MINIMAL


csv.register_dialect("excel_csv", Excel_csv)


class Csv_unicode_reader():

    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """
    champs = None

    def __init__(self, fich, dialect=Excel_csv, **kwds):  # pylint: disable=W0231
        self.line_num = 0
        self.reader = csv.DictReader(fich, dialect=dialect, fieldnames=self.champs, **kwds)

    def __next__(self):
        self.line_num += 1
        self.row = next(self.reader)
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
        for base_name in files:
            if fnmatch.fnmatch(base_name, recherche):
                yield os.path.join(root, base_name)


class AttrDict(dict):
    """http://stackoverflow.com/questions/4984647/accessing-dict-keys-like-an-attribute-in-python"""

    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
