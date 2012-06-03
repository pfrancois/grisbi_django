#!/usr/bin/python
"""
A simple class to represent a Quicken (QIF) file, and a parser to
load a QIF file into a sequence of those classes.
It's enough to be useful for writing conversions.
version SG:
    importe au niveau des tiers , laisse tomber le P
    si carte
        met a la place le tiers a parti du 20
        choisi la date a la position 14
    gestion des virements !!
    en gros se faire un beau dictionnaire avec tous les trucs speciaux.
    voir si l'operation n'existe pas deja a la date du jour ou a +- 2 jour
"""

import sys
import decimal
from .utils import datefr2datesql, fr2decimal, strpdate
#definition
#expression reg
#id des moyens,tiers,cat et ib, si None, on ne change pas
#int de la colonne a commencer pour le tiers
tiers_perso = (
        {"reg":r"PRELEVEMENT \d*  TRESOR PUBLIC", "def":{"moyen":4, "tiers":15, "cat":24, "ib":None}, "decal":None, "date":false},
        {"reg":r"CARTE X\d* (\d\d/\d\d)", "def":{"moyen":3, "tiers":None, "cat":None, "ib":None}, "decal":None, "date":True},
        {"reg":r"CARTE X\d* (\d\d/\d\d)", "def":{"moyen":3, "tiers":None, "cat":None, "ib":None}, "decal":20, "date":True},
    )

class QifItem:
    def __init__(self):
        self.order = ['date', 'amount', 'cleared', 'num', 'payee', 'memo', 'address', 'category', 'categoryInSplit',
                      'memoInSplit', 'amountOfSplit']
        self.date = None
        self.amount = None
        self.cleared = None
        self.num = None
        self.payee = None
        self.memo = None
        self.address = None
        self.category = None
        self.categoryInSplit = None
        self.memoInSplit = None
        self.amountOfSplit = None

    def show(self):
        pass

    def __unicode__(self):
        titles = ','.join(self.order)
        tmpstring = ','.join([str(self.__dict__[field]) for field in self.order])
        tmpstring = tmpstring.replace('None', '')
        return titles + "," + tmpstring

    def dataString(self):
        """
        Returns the data of this QIF without a header row
        """
        tmpstring = ','.join([str(self.__dict__[field]) for field in self.order])
        tmpstring = tmpstring.replace('None', '')
        return tmpstring


def parseQif(infile):
    """
    Parse a qif file and return a list of entries.
    infile should be open file-like object (supporting readline() ).
    """

    inItem = False #@UnusedVariable

    items = []
    curItem = QifItem()
    line = infile.readline()
    while line != '':
        if line[0] == '\n': # blank line
            pass
        elif line[0] == '^': # end of item
            # save the item
            items.append(curItem)
            curItem = QifItem()
        elif line[0] == 'D':
            curItem.date = strpdate(datefr2datesql(line[1:-1]))
        elif line[0] == 'T':
            curItem.amount = decimal.Decimal(str(line[1:-1]))
        elif line[0] == 'C':
            curItem.cleared = line[1:-1]
        elif line[0] == 'P':
            pass#on n'en a pas besoin
        elif line[0] == 'M':
            payeur = line[1:-1]
        elif line[0] == 'A':#inutile mais bon
            curItem.address = line[1:-1]
        elif line[0] == 'L':
            curItem.category = line[1:-1]
        elif line[0] == 'S':
            try:
                curItem.categoryInSplit.append(";" + line[1:-1])
            except AttributeError:
                curItem.categoryInSplit = line[1:-1]
        elif line[0] == 'E':
            try:
                curItem.memoInSplit.append(";" + line[1:-1])
            except AttributeError:
                curItem.memoInSplit = line[1:-1]
        elif line[0] == '$':
            try:
                curItem.amountInSplit.append(";" + line[1:-1])
            except AttributeError:
                curItem.amountInSplit = line[1:-1]
        else:
            # don't recognise this line; ignore it
            print >> sys.stderr, "Skipping unknown line:\n", line

        line = infile.readline()
    return items

if __name__ == "__main__":
    # read from stdin and write CSV to stdout
    import os

    nomfich = "%s/../perso.qif" % (os.path.dirname(os.path.abspath(__file__)))
    nomfich = os.path.normpath(nomfich)
    qiffile = open(nomfich)
    items = parseQif(qiffile)
    qiffile.close()
    print repr(items[0])
    for item in items[1:]:
        print item.dataString()
