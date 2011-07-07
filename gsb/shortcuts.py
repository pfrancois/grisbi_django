# -*- coding: utf-8
from mysite.gsb.models import *
import datetime
import decimal

class Ex_jumelle_neant(Exception): pass

class Virement(object):
    def __init(self,ope_id=None):
        if ope:
            self.origine=Ope.objects.get(id=ope_id)
            self.destination=self.origine.jumelle
            if not isintance(self.destination,Ope):
                raise Ex_jumelle_neant(self.origine.id)
        else:
            pass
    def setdate(self,date):
        self.origine.date=date
        self.dest.date=date
    def getdate(self):
        return self.origine.date
    date=property(getdate,setdate)

    def setdate_val(self,date):
        self.origine.date_val=date
        self.dest.date_val=date
    def getdate_val(self):
        return self.origine.date_val
    date_val=property(getdate_val,setdate_val)

    def setmontant(self,montant):
        self.origine.montant=montant
        self.dest.montant=montant
    def getmontant(self):
        return self.origine.montant
    montant=property(getmontant,setmontant)

    def setnotes(self,notes):
        self.origine.notes=notes
        self.dest.notes=notes
    def getnotes(self):
        return self.origine.notes
    notes=property(getnotes,setnotes)

    def setpointe(self,p):
        self.origine.pointe=p
        self.dest.pointe=p
    def getpointe(self):
        return self.origine.pointe
    pointe=property(getpointe,setpointe)

    def save(self):
        self.origine.save()
        self.dest.save()

    def setrapp(self,p):
        self.origine.rapp=p
        self.dest.rapp=p
    def getrapp(self):
        return self.origine.rapp
    rapp=property(getrapp,setrapp)

    def create(self,compte_origine, compte_dest, montant, date, notes=""):
        self.origine=Ope()
        self.dest=Ope()
        self.origine.compte=compte_origine
        self.dest.compte=compte_dest
        self.montant=montant
        self.date=date
        self.notes=notes
        self.save()
        self.origine.jumelle=self.dest
        self.dest.jumelle=self.origine
        self.save()

    def delete(self):
        self.origine.jumelle=None
        self.dest.jumelle=None
        self.origine.delete()
        self.dest.delete()

