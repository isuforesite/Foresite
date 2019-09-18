do $$
declare
  spec_state text := null;
  spec_states text[] := array[ 'IA' ];
begin
-----

-----
drop table if exists clu.clu_mupoly19;
create table clu.clu_mupoly19(
  state char( 2 ),
  fips char( 5 ),
  clukey int4,
  musym text,
  mukey text,
  acres numeric( 10, 5 ),
  clu_pct numeric( 8, 5 ),
  wkb_geometry geometry );

-----
for spec_state in
  select
    *
  from unnest( spec_states )
loop

raise notice 'Processing CLU-mupolygon intersection: %', spec_state;
insert into clu.clu_mupoly19
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
  ssurgo_2019.mupolygon t2,
  st_dump( st_intersection( t1.wkb_geometry, t2.shape ) ) geom_int
where
  t1.state = spec_state
  and st_intersects( t1.wkb_geometry, t2.shape )
  and not st_touches( t1.wkb_geometry, t2.shape )
window w as ( partition by t1.clukey );

end loop;

---
end
$$
language plpgsql;
