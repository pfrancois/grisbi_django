SELECT   ope.id,  c.nom as compte,   strftime('%d/%m/%Y',ope.date) as date,   ope.montant,  rapp.nom as R,  ope.pointe as P,  cat.nom as categorie,  tiers.nom as tiers,  ope.notes,   ib.nom as projet,  ope.num_cheque,   ope.jumelle_id,   ope.mere_id ,strftime('%Y_%m',ope.date) as mois,strftime('%Y',ope.date) as annee, case cat.id when 46 then "mere" else "" end as ope_mere
FROM 
 gsb_ope ope   left outer join gsb_compte c  on ope.compte_id=c.id
  left outer join gsb_cat cat  on ope.cat_id=cat.id
  left outer join gsb_ib ib on ope.ib_id=ib.id
  left outer join gsb_moyen moyen on ope.moyen_id=moyen.id
  left outer join gsb_rapp rapp on ope.rapp_id=rapp.id
  left outer join gsb_tiers tiers on ope.tiers_id=tiers.id order by ope.date desc;
