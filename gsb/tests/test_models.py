# -*- coding: utf-8 -*
"""
test models
"""
from django.test import TestCase
from mysite.gsb.models import Generalite, Compte, Ope, Tiers, Cat, Moyen, Titre, Banque
from mysite.gsb.models import Compte_titre, Virement, Ope_titre
import datetime, time
import decimal
def strpdate(s):
    return datetime.date(*time.strptime(s, "%Y-%m-%d")[0:3])
class test_models(TestCase):
    fixtures = ['test.json']
    def test_tiers_reaffect(self):
        Tiers.objects.get(nom = "tiers1").fusionne(Tiers.objects.get(nom = "tiers2"))
        self.assertEqual(Tiers.objects.count(), 4)
        self.assertEqual(Ope.objects.get(id = 1).tiers.nom, "tiers2")
        #self.assertEqual(Echeance.objects.get(id=1).tiers.nom,"tiers2")
    def testt_titre_last_cours_et_date(self):
        self.assertEquals(Titre.objects.get(nom = "t1").last_cours, 1)
        self.assertEqual(Titre.objects.get(nom = "t1").last_cours_date, datetime.date(day = 1, month = 1, year = 2010))
    def test_titre_creation(self):
        tiers = Titre.objects.get(nom = "t1").tiers
        self.assertNotEqual(tiers, None)
        self.assertEqual(tiers.nom, 'titre_ t1')
        self.assertEqual(tiers.notes, "1@ACT")
        self.assertEqual(tiers.is_titre, True)
    def test_titre_fusionne(self):
        Titre.objects.get(nom = "t1").fusionne(Titre.objects.get(nom = "t2"))
        self.assertEqual(Titre.objects.count(), 2)
        self.assertEqual(Tiers.objects.count(), 4)#verifie que la fusion des tiers sous jacent
    def test_titre_save_perso(self):
        Titre.objects.create(nom = "t3", isin = "4", type = 'ACT')
        self.assertEqual(Tiers.objects.count(), 6)
        self.assertEqual(Tiers.objects.filter(is_titre = True).count(), 4)
        self.assertEqual(Tiers.objects.get(nom = "titre_ t3").nom, "titre_ t3")
    def test_banque_fusionne(self):
        Banque.objects.get(cib = '99999').fusionne(Banque.objects.get(cib = "10001"))
        self.assertEqual(Banque.objects.count(), 1)
        self.assertEqual(Compte.objects.get(id = 3).banque.id, 1)
    def test_cat_fusionne(self):
        Cat.objects.get(nom = "cat2").fusionne(Cat.objects.get(nom = "cat1"))
        self.assertEqual(Cat.objects.count(), 3)
        self.assertEqual(Ope.objects.filter(cat__nom = "cat1").count(), 2)
    #def test_ib_fusionne(self):
    #def test_exo_fusionne(self):
    def test_compte_solde_normal(self):
        self.assertEqual(Compte.objects.get(id = 1).solde, decimal.Decimal('20'))
    def test_compte_abolute_url(self):
        self.assertEqual(Compte.objects.get(id = 1).get_absolute_url(), '/compte/1/')
    def test_ope_titre_achat_sans_virement(self):
        c = Compte_titre.objects.get(id = 4)
        self.assertEqual(c.nom, u'cpt_titre1')
        t = Titre.objects.get(nom = "t1")
        self.assertEqual(Ope_titre.investi(c, t), 0)
        c.achat(titre = t, nombre = 20, date = '2011-01-01')
        self.assertEqual(Ope_titre.investi(c, t), 20)
        tall = c.titre.all().distinct()
        self.assertEqual(tall.count(), 1)
        self.assertEqual(tall[0].last_cours, 1)
        self.assertEqual(c.solde, 0)
        t.cours_set.create(date = '2011-02-01', valeur = 2)
        self.assertEqual(c.solde, 20)
        c.vente(titre = t, nombre = 10, prix = 3, date = '2011-06-30')
        self.assertEqual(c.solde, 40)
        c.achat(titre = t, nombre = 20, prix = 2, date = '2011-01-01')
        self.assertEqual(c.solde, 60)
    def test_cpt_titre_achat_complet(self):
        c = Compte_titre.objects.get(id = 4)
        t = Titre.objects.get(nom = "t1")
        c.achat(titre = t, nombre = 20, date = '2011-01-01', virement_de = Compte.objects.get(id = 1))
        self.assertEqual(Ope_titre.investi(c, t), 20)
        self.assertEqual(c.solde, 20)
        t.cours_set.create(date = '2011-02-01', valeur = 2)
        c.vente(t, 10, 3, '2011-06-30', virement_vers = Compte.objects.get(id = 1))
        self.assertEqual(Ope_titre.investi(c, t), -10)
        self.assertEqual(c.solde, 30)
    def test_moyen_fusionne(self):
        Moyen.objects.get(id = 2).fusionne(Moyen.objects.get(id = 1))
#    def test_rapp_compte(self):
#    def test_rapp_solde(self):
#    def test_rapp_fusionne(self):
#    def test_echeance_save(self):
    def test_generalite_gen(self):
        self.assertEquals(Generalite.gen().id, 1)
    def test_generalite_dev_g(self):
        self.assertEqual(Generalite.dev_g(), 'EUR')
    def test_ope_absolute_url(self):
        self.assertEqual(0, 0)
    def test_ope_save(self):
        o = Ope.objects.create(compte = Compte.objects.get(id = 1), date = '2010-01-01', montant = 20, tiers = Tiers.objects.get(id = 1))
        self.assertEquals(o.moyen, o.compte.moyen_credit_defaut)
        o = Ope.objects.create(compte = Compte.objects.get(id = 1), date = '2010-01-01', montant = -20, tiers = Tiers.objects.get(id = 1))
        self.assertEquals(o.moyen, o.compte.moyen_debit_defaut)
        o = Ope.objects.create(compte = Compte.objects.get(id = 1), date = '2010-01-01', montant = -20, tiers = Tiers.objects.get(id = 1), moyen = Moyen.objects.get(id = 2))
        self.assertEquals(o.moyen, Moyen.objects.get(id = 2))
    def test_virement_verif_property(self):
        Virement.create(Compte.objects.get(id = 1), Compte.objects.get(id = 2), 20, date = '2010-01-01', notes = 'test_notes')
        v = Virement(Ope.objects.get(id = 3))
        self.assertEquals(v.origine.id, 3)
        self.assertEquals(v.dest.id, 4)
        self.assertEquals(v.origine.compte, Compte.objects.get(nom = 'cpt1'))
        self.assertEquals(v.dest.compte, Compte.objects.get(nom = 'cpt2'))
        self.assertEquals(v.origine.id, 3)
        self.assertEquals(v.date, strpdate('2010-01-01'))
        self.assertEquals(v.montant, v.origine.montant * -1)
        self.assertEquals(v.montant, v.dest.montant)
        self.assertEquals(v.montant, 20)
        v.date_val = '2011-02-01'
        v.save()
        self.assertEquals(Virement(Ope.objects.get(id = 3)).date_val, strpdate('2011-02-01'))
    def test_virement_create(self):
        v = Virement.create(Compte.objects.get(id = 1), Compte.objects.get(id = 2), 20)
        self.assertEqual(Compte.objects.get(id = 1).solde, 0)
        self.assertEquals(v.origine.compte, Compte.objects.get(nom = 'cpt1'))
        self.assertEquals(v.dest.compte, Compte.objects.get(nom = 'cpt2'))
        self.assertEquals(v.origine.id, 3)
        self.assertEquals(v.date, datetime.date.today())
        self.assertEquals(v.montant, v.origine.montant * -1)
        self.assertEquals(v.montant, v.dest.montant)
        self.assertEquals(v.montant, 20)
        v = Virement.create(Compte.objects.get(id = 1), Compte.objects.get(id = 2), 20, '2010-01-01', 'test_notes')
        self.assertEqual(Compte.objects.get(id = 1).solde, -20)
        self.assertEqual(v.date, '2010-01-01')
        self.assertEqual(v.notes, 'test_notes')
    def test_virement_delete(self):
        v = Virement.create(Compte.objects.get(id = 1), Compte.objects.get(id = 2), 20)
        v.delete()
        self.assertEquals(Compte.objects.get(nom = 'cpt1').solde, 20)
        self.assertEquals(Compte.objects.get(nom = 'cpt2').solde, 0)
    def test_virement_init_form(self):
        v = Virement.create(Compte.objects.get(id = 1), Compte.objects.get(id = 2), 20, '2010-01-01', 'test_notes')
        tab = {'compte_origine':1,
               'compte_destination':2,
               'montant':20,
               'date':"2010-01-01",
               'notes':'test_notes',
               'pointe':False,
               'piece_comptable_compte_origine':u'',
               'piece_comptable_compte_destination':u'',
               'moyen_origine':2,
               'moyen_destination':1,
               }
        self.assertEquals(tab, v.init_form())
