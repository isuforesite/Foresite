drop table if exists sandbox.huc12_soils;
create table sandbox.huc12_soils as
select distinct
	t1.huc12,
	t1.huc12_name,
	t2.state,
	t2.fips,
	t2.mukey,
	t2.musym
from sandbox.huc12_fields t1
left outer join clu.clu_mupoly19 t2
	on t2.clukey = t1.clukey;