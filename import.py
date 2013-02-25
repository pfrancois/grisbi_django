from __future__ import absolute_import
import csv
import os

from gsb import utils
'''___________________ ajout depuis les truc de django'''
class Csv_unicode_reader(object):
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, fich, dialect=utils.Excel_csv, encoding="utf-8", **kwds):  # pylint: disable=W0231
        self.line_num = 1
        fich = utils.UTF8Recoder(fich, encoding)
        self.reader = csv.DictReader(fich, dialect=dialect, **kwds)

    def next(self):
        self.line_num += 1
        self.row = self.reader.next()
        return self

    def __iter__(self):
        return self
'''_____________fin rajout'''

def mot(var):
    return var.partition(' ')[0].strip()
def reste(var):
    return var.partition(' ')[2].strip()
def mots(var):
    tour=var.split(' ')
    tour1=[]
    for i in tour:
        if i.strip() !='':
            tour1.append(i.strip())
    return tour1
    

class csv_sg_reader(Csv_unicode_reader):
    
    @property
    def lib(self):
        return self.row['lib'].strip()
    @property
    def detail(self):
        return self.row['detail'].strip()
    @property
    def det(self):
        tour1=mots(self.detail)
        retour=None
        try:
            if tour1[1]=="EUROPEEN":
                tour1=' '.join(tour1[4:])
                retour=tour1
            if self.moyen=="VIR RECU":
                retour=' '.join(tour1[3:])
            if retour is None:
                retour=' '.join(tour1[2:])
        except IndexError:
            retour=' '.join(tour1[1:])
        return retour.strip()
    
    @property
    def id(self):
        return None

    @property
    def cat(self):
        return None

    @property
    def automatique(self):
        return False

    @property
    def cpt(self):
        return 'SG'

    @property
    def date(self):
        if self.moyen != "visa":
            try:
                if mots(self.detail)[2]=="RETRAIT":
                    annee=utils.to_date(self.row['date'], "%d/%m/%Y").year
                    if mots(self.detail)[4] != "SG":
                        return utils.to_date("%s/%s"%(mots(self.detail)[4],annee), "%d/%m/%Y")
                    else:
                        return utils.to_date("%s/%s"%(mots(self.detail)[5],annee), "%d/%m/%Y")
            except IndexError:
                return utils.to_date(self.row['date'], "%d/%m/%Y")
        else:
            #paiment visa
            annee=utils.to_date(self.row['date'], "%d/%m/%Y").year
            return utils.to_date("%s/%s"%(mots(self.detail)[2],annee), "%d/%m/%Y")
                

    @property
    def date_val(self):
        if self.moyen=="visa":
            return utils.to_date(self.row['date'].strip(), "%d/%m/%Y")
        else:
            return None 

    @property
    def exercice(self):
        return None

    @property
    def ib(self):
        return None

    @property
    def jumelle(self):
        #un retrait
        if self.detail[:19]==u"CARTE X4983 RETRAIT":
            return "caisse"
        if self.det[:14]=="GENERATION VIE":
            return "generation vie"
        if self.det[:16]=="Gr Bque - Banque":
            return "BDF PEE"  
        return None

    @property
    def mere(self):
        return None

    @property
    def mt(self):
        return utils.to_decimal(self.row['montant'])

    @property
    def moyen(self):
        m=mots(self.detail)
        if mots(self.detail)[0]=="CARTE":
            if mots(self.detail)[2] !="RETRAIT":
                moyen="visa" 
            else:
                moyen="virement"
        elif m[0]=="VIR" and m[1]=="RECU":
            moyen="recette"
        elif m[0]=="CHEQUE":
            moyen="cheque"
        else:
            moyen="prelevement"
        return moyen

    @property
    def notes(self):
        return self.detail

    @property
    def num_cheque(self):
        if self.moyen=="CHEQUE":
            return int(self.detail.partition(' ')[2].strip())
        else:
            return None

    @property
    def piece_comptable(self):
        return ''

    @property
    def pointe(self):
        return True

    @property
    def rapp(self):
        return None

    @property
    def tiers(self):
        if self.moyen=="cheque":
            return "inconnu"
        if self.moyen=="virement" and self.mt<0:
            return "%s=>%s"%(self.cpt,self.jumelle)
        if self.moyen=="virement" and self.mt>0:
            return "%s=>%s"%(self.jumelle,self.cpt)
        if self.moyen=="visa":
            return " ".join(mots(self.detail)[3:])
        if "%s %s"%(mots(self.detail)[0],mots(self.detail)[1])=="VIR RECU":
            return " ".join(mots(self.detail)[4:6])
        return self.det.lower()

    @property
    def monnaie(self):
        return self.row['devise']

    @property
    def ope_titre(self):
        return False

    @property
    def ope_pmv(self):
        return False

    @property
    def ligne(self):
        return self.line_num
    
    @property
    def has_fille(self):
        return False

'''prog principal'''
import pprint
PROJECT_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__)))
with open(os.path.join(PROJECT_PATH,"log","00050550715_2013_02_11.csv"), 'rt') as f_non_encode:
    fich = csv_sg_reader(f_non_encode, encoding="iso-8859-1",fieldnames=['date','lib','detail','montant','devise'])
    data=[]
    #on passe trois ligne car elles sont vides
    fich.next()
    fich.next()
    fich.next()
    for row in fich:
        if row.jumelle is None:
            data.append({'initial':[row.lib,row.detail],
                         'date':row.date,
                         'date_val':row.date_val,
                         'compte':row.cpt,
                         'montant':row.mt,
                         'jumelle':row.jumelle, 
                         'moyen':row.moyen,
                         'numcheque':row.num_cheque,
                         'tiers':row.tiers,
                         'ligne':row.ligne,
                         'pointe':True,
                         'notes':row.notes,
                         'jumelle':None})
        else:
            data.append({'initial':[row.lib,row.detail],
                         'date':row.date,
                         'date_val':row.date_val,
                         'compte':row.cpt,
                         'montant':row.mt,
                         'jumelle':row.jumelle, 
                         'moyen':row.moyen,
                         'numcheque':row.num_cheque,
                         'tiers':row.tiers,
                         'ligne':row.ligne,
                         'pointe':True,
                         'notes':row.notes,
                         'jumelle':row.jumelle})
            data.append({'initial':[row.lib,row.detail],
                         'date':row.date,
                         'date_val':row.date_val,
                         'compte':row.jumelle,
                         'montant':row.mt,
                         'jumelle':row.jumelle, 
                         'moyen':row.moyen,
                         'numcheque':row.num_cheque,
                         'tiers':row.tiers,
                         'ligne':row.ligne,
                         'pointe':True,
                         'notes':row.notes,
                         'jumelle':row.jumelle})
    pprint.pprint(data)
