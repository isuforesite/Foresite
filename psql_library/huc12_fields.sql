drop table if exists sandbox.huc12_fields;
create table sandbox.huc12_fields as
select
	t1.huc12,
	t1.name as huc12_name,
	t2.clukey
from public.us_huc12 t1,
	clu.clu_conus t2
where
	st_intersects( t2.wkb_geometry, t1.shape )
	and t2."state" = 'IA'
	and t1.name = 'Middle Squaw Creek';
	