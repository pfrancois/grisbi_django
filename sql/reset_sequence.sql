BEGIN;
SELECT setval(pg_get_serial_sequence('"gsb_tiers"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "gsb_tiers";
SELECT setval(pg_get_serial_sequence('"gsb_titre"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "gsb_titre";
SELECT setval(pg_get_serial_sequence('"gsb_cours"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "gsb_cours";
SELECT setval(pg_get_serial_sequence('"gsb_banque"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "gsb_banque";
SELECT setval(pg_get_serial_sequence('"gsb_cat"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "gsb_cat";
SELECT setval(pg_get_serial_sequence('"gsb_ib"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "gsb_ib";
SELECT setval(pg_get_serial_sequence('"gsb_exercice"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "gsb_exercice";
SELECT setval(pg_get_serial_sequence('"gsb_compte"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "gsb_compte";
SELECT setval(pg_get_serial_sequence('"gsb_ope_titre"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "gsb_ope_titre";
SELECT setval(pg_get_serial_sequence('"gsb_moyen"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "gsb_moyen";
SELECT setval(pg_get_serial_sequence('"gsb_rapp"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "gsb_rapp";
SELECT setval(pg_get_serial_sequence('"gsb_echeance"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "gsb_echeance";
SELECT setval(pg_get_serial_sequence('"gsb_ope"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "gsb_ope";
SELECT setval(pg_get_serial_sequence('"auth_permission"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "auth_permission";
SELECT setval(pg_get_serial_sequence('"auth_group_permissions"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "auth_group_permissions";
SELECT setval(pg_get_serial_sequence('"auth_group"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "auth_group";
SELECT setval(pg_get_serial_sequence('"auth_user_user_permissions"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "auth_user_user_permissions";
SELECT setval(pg_get_serial_sequence('"auth_user_groups"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "auth_user_groups";
SELECT setval(pg_get_serial_sequence('"auth_user"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "auth_user";
COMMIT;


SELECT strftime('%Y', ope2.date) as annee, strftime('%m', ope2.date) as mois,
       (SELECT SUM(ope.MONTANT)
        FROM   gsb_ope AS ope
        WHERE  strftime('%Y', ope.date) = strftime('%Y', ope2.date)
          AND  strftime('%m', ope.date) <= strftime('%m', ope2.date)) AS CUMUL_AN_MOIS
FROM   gsb_ope AS ope2
where strftime('%Y', ope2.date) >= '2014'
group by mois
ORDER BY ope2.date;

SELECT strftime('%Y', ope2.date) as annee, strftime('%m', ope2.date) as mois,ope2.cat_id
       (SELECT SUM(ope.MONTANT)
        FROM   gsb_ope AS ope
        WHERE  strftime('%Y', ope.date) = strftime('%Y', ope2.date)
          AND  strftime('%m', ope.date) <= strftime('%m', ope2.date)
          AND ope.cat_id=ope2.cat_id) AS CUMUL_AN_MOIS
FROM   gsb_ope AS ope2
where strftime('%Y', ope2.date) >= '2014'
group by mois, cat_id
ORDER BY ope2.date;