do $$
declare
	spec_table text := null;
	stabbr text := null;
begin
-----
-----
drop table if exists clu.clu_conus;
create table clu.clu_conus(
  clukey serial primary key,
  uuid uuid default uuid_generate_v4() not null,
  state char( 2 ) not null,
  fips char( 5 ) not null,
  calcacres numeric( 10, 2 ) not null,
  ogc_fid_orig text,
  wkb_geometry public.geometry( MULTIPOLYGON, 4326 ) not null );

-----
for spec_table in
	select
		table_name,
		upper( left( split_part( table_name, '_', 4 ), 2 ) ) as state,
		upper( split_part( table_name, '_', 4 ) ) as fips
	from information_schema.tables
	where
		table_name ~ 'clu_public_a_[a-z]{2}'
		and table_schema = 'clu_onboard'
		and table_type = 'BASE TABLE'
	order by
		table_name
loop
raise notice 'Inserting data %', spec_table;

execute
	'delete from clu_onboard.' || spec_table || ' where wkb_geometry is null;';

execute
	'insert into clu.clu_conus( state, fips, calcacres, ogc_fid_orig, wkb_geometry )
	select
		upper( left( split_part( ''' || spec_table || '''::text, ''_'', 4 ), 2 ) ) as state,
		upper( split_part( ''' || spec_table || '''::text, ''_'', 4 ) ) as fips,
		calcacres,
		ogc_fid,
		wkb_geometry
	from clu_onboard.' || spec_table;

end loop;


----- fix invalid polygons
for stabbr in
select
	distinct( state )
from clu.clu_conus
order by
	state
loop
	raise notice 'Fixing invalid polygons: %', stabbr;
	update clu.clu_conus
	set wkb_geometry = st_makevalid( wkb_geometry )
	where state = stabbr;
end loop;

----- add constraint for valid polygons
raise notice 'Adding valid geometry constraint';
alter table clu.clu_conus
add constraint clu_wkb_geometry_check
check( st_isvalid( wkb_geometry ) );

----- ensure unique clukey
raise notice 'Adding unique clukey';
alter table clu.clu_conus
add unique( clukey );

---- add gist index to the spatial polygon data
raise notice 'Adding gist index';
create index clu_wkb_geometry_idx on clu.clu_conus using gist( wkb_geometry );

---
end
$$
language plpgsql
