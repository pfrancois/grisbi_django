# -*- coding: utf-8
from mysite.gsb.models import *
import datetime
import decimal

class Ex_jumelle_neant(Exception): pass
class gsb_exc(Exception): pass

class Virement(object):
    def __init__(self, ope=None):
        if ope:
            self.origine = ope
            self.dest = self.origine.jumelle
            if not isinstance(self.dest, Ope):
                raise Ex_jumelle_neant(self.origine.id)
            self._init = True
        else:
            self._init = False
    def setdate(self, date):
        self.origine.date = date
        self.dest.date = date
    def getdate(self):
        return self.origine.date
    date = property(getdate, setdate)

    def setdate_val(self, date):
        self.origine.date_val = date
        self.dest.date_val = date
    def getdate_val(self):
        return self.origine.date_val
    date_val = property(getdate_val, setdate_val)

    def setmontant(self, montant):
        self.origine.montant = montant
        self.dest.montant = montant
    def getmontant(self):
        return self.origine.montant
    montant = property(getmontant, setmontant)

    def setnotes(self, notes):
        self.origine.notes = notes
        self.dest.notes = notes
    def getnotes(self):
        return self.origine.notes
    notes = property(getnotes, setnotes)

    def setpointe(self, p):
        self.origine.pointe = p
        self.dest.pointe = p
    def getpointe(self):
        return self.origine.pointe
    pointe = property(getpointe, setpointe)

    def setrapp(self, r):
        self.origine.rapp = r
        self.dest.rapp = r
    def getrapp(self):
        return self.origine

    def save(self):
        nom_tiers = "%s => %s" % (self.origine.compte.nom, self.dest.compte.nom)
        t, created = Tiers.objects.get_or_create(nom=nom_tiers, defaults={'nom':nom_tiers})
        self.origine.tiers = t
        self.origine.tiers = t
        self.origine.save()
        self.dest.save()

    def create(self, compte_origine, compte_dest, montant, date, notes=""):
        self.origine = Ope()
        self.dest = Ope()
        self.origine.compte = compte_origine
        self.dest.compte = compte_dest
        self.montant = montant
        self.date = date
        self.notes = notes
        self.save()
        self.origine.jumelle = self.dest
        self.dest.jumelle = self.origine
        self.save()

    def delete(self):
        self.origine.jumelle = None
        self.dest.jumelle = None
        self.origine.delete()
        self.dest.delete()

    def init_form(self):
        """renvoit les donnnés afin d'intialiser virementform"""
        if self._init:
            t = {'compte_origine':self.origine.compte.id,
               'compte_destination':self.dest.compte.id,
               'montant':self.montant,
               'date':self.date,
               'notes':self.notes,
               'pointe':self.pointe,
               'piece_comptable_compte_origine':self.origine.piece_comptable,
               'piece_comptable_compte_destination':self.dest.piece_comptable}
            if self.origine.moyen:
                t['moyen_origine'] = self.origine.moyen.id
            else:
                t['moyen_origine'] = None
            if self.dest.moyen:
                t['moyen_destination'] = self.dest.moyen.id
            else:
                t['moyen_destination'] = None
            if self.origine.rapp:
                t['rapp_origine'] = self.origine.rapp.id
            else:
                t['rapp_origine'] = None
            if self.dest.rapp:
                t['rapp_destination'] = self.dest.rapp.id
            else:
                t['rapp_destination'] = None

        else:
            raise Exception('attention, on ne peut intialiser un form que si virement est bound')
        return t
