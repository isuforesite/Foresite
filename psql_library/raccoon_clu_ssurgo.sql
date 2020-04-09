drop table if exists raccoon.raccoon_clu_ssurgo_2018;
create table raccoon.raccoon_clu_ssurgo_2018 as
select
    t1.state,
    t1.fips,
    t1.huc8,
    t2.clukey,
    t2.musym,
    t2.mukey,
    t2.acres,
    t2.clu_pct,
	t2.wkb_geometry
from raccoon.raccoon_clu t1
left join clu.clu_mupoly18 t2
on t2.clukey = t1.clukey