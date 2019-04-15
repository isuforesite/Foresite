do $$
declare
	stabbr text := null;
begin
-----
--create index ssurgo_mu18_gidx on ssurgo_2018.mupolygon using gist (shape);
--vacuum analyze ssurgo_2018.mupolygon;

-----
drop table if exists clu.clu_mupoly18;
create table clu.clu_mupoly18(
  state char( 2 ),
  fips char( 5 ),
  clukey int4,
  musym text,
  mukey text,
  acres numeric( 10, 5 ),
  clu_pct numeric( 8, 5 ),
	wkb_geometry geometry );

-----
raise notice 'Processing CLU-mupolygon intersection';
--for stabbr in
-- 	select
-- 		distinct( fips ) as fips
-- 	from clu.clu_conus
-- 	where
-- 		state = 'IA'
-- 	order by
-- 		fips asc
--loop
--
raise notice '%', stabbr;
insert into clu.clu_mupoly18
select
  t1.state,
  t1.fips,
  t1.clukey,
  t2.musym,
  t2.mukey,
  st_area( geom_int.geom::geography ) * 0.000247105 as acres,
  st_area( geom_int.geom::geography ) /
    sum( st_area( geom_int.geom::geography ) ) over w as clu_pct,
	geom_int.geom
from clu.clu_conus t1,
  ssurgo_2018.mupolygon t2,
  st_dump( st_intersection( t1.wkb_geometry, t2.shape ) ) geom_int
where
	t1.state = 'IA'
	and st_intersects( t1.wkb_geometry, t2.shape )
  and not st_touches( t1.wkb_geometry, t2.shape )
window w as ( partition by t1.clukey );
--
--end loop;

---
end
$$
language plpgsql;
