drop table if exists vanloocke.raccoon_clu;
create table vanloocke.raccoon_clu as
select
	t1.clukey,
	t1.state,
	t1.fips,
	t2.huc8,
	t2."name",
	t1.wkb_geometry
from clu.clu_conus t1,
vanloocke.raccoon_watersheds t2
where
	st_intersects( t1.wkb_geometry, t2.wkb_geometry )
