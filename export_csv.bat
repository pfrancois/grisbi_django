echo off
ren export.csv export_bak.csv
sqlite3 -csv -header -separator ; grisbi.sqlite ".read export_csv.sql" > export.csv
rem sed -i.bak -s -b -e "s/\"//g" export.csv