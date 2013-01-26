SELECT 
  ope.id,
  c.nom as compte, 
  ope.date, 
  ope.montant,
  rapp.nom as r,
  ope.pointe as p,
  cat.nom as categ,
  tiers.nom as tiers,
  ope.notes, 
  ib.nom as projet,
  ope.num_cheque,
  ope.pointe, 
  ope.jumelle_id, 
  ope.mere_id
FROM 
  public.gsb_ope ope 
  left outer join public.gsb_compte c  on ope.compte_id=c.id
  left outer join public.gsb_cat cat  on ope.cat_id=cat.id
  left outer join public.gsb_ib ib on ope.ib_id=ib.id
  left outer join public.gsb_moyen moyen on ope.moyen_id=moyen.id
  left outer join public.gsb_rapp rapp on ope.rapp_id=rapp.id
  left outer join public.gsb_tiers tiers on ope.tiers_id=tiers.id;
