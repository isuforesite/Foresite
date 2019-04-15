----
do
$$
declare
	clu_srid int4 := st_srid( wkb_geometry ) from clu.clu_conus limit 1;
  cdl_srid int4 := st_srid( rast ) from cdl.cdl_30m_2018 limit 1;
	cdl_yrs int4[] := array[ 2014, 2015, 2016, 2017, 2018 ];
	cdl_yr int4 := 2018;
	spec_fips char(5) := null;
begin

----
set client_min_messages to warning;
raise warning 'CLU srid: %', clu_srid;
raise warning 'CDL srid: %', cdl_srid;
raise warning 'Processing % CDL', cdl_yr;

---
create table if not exists clu.clu_cdl(
	fips char( 5 ),
	clukey int4,
	years int4,
	crop int4 );

----
for spec_fips in
  select
    distinct( fips ) as fips
  from clu.clu_conus
  where left( fips, 2 ) = 'IA'
  order by fips
loop
raise warning 'Processing: %', spec_fips;

-----
execute 'insert into clu.clu_cdl
select
	t1.fips,
	t1.clukey,
	' || cdl_yr || ' as year,
	t1.value as crop
from(
	select
		t1.fips,
		t1.clukey,
		t1.value,
		t1.count,
		row_number()over(
			partition by t1.fips, t1.clukey
			order by count desc ) as rnk
	from(
		select
			t1.fips,
			t1.clukey,
			( st_valuecount( st_clip( t2.rast, 1, st_transform( t1.wkb_geometry, ' || cdl_srid || ' ), True ) ) ).*
		from clu.clu_conus t1,
			cdl.cdl_30m_' || cdl_yr || ' t2
		where
			st_intersects( st_transform( t1.wkb_geometry, ' || cdl_srid || ' ), t2.rast )
			and t1.fips = ''' || spec_fips || '''
	) t1
) t1
where
	t1.rnk = 1';

---
end loop;

----
end;
$$ language plpgsql;
