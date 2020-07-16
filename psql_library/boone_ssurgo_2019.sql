drop table if exists "public".boone_ssurgo_mupolygon_2019;
create table "public".boone_ssurgo_mupolygon_2019 as
select *
from ssurgo_2019.mupolygon
WHERE areasymbol = 'IA015';