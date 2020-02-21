----
drop function if exists api.soil_layer_properties( mukey_array text[] );
create or replace function api.soil_layer_properties( mukey_array text[] )
returns table(
	areasymbol text,
	areaname text,
	mukey text,
	musym text,
	muname text,
	cokey text,
	comppct int4,
	slope int4, --percent
	slopelenusle int4, --m
	hzdept int4, --cm
	hzdepb int4, --cm
	kffact varchar,
	dbthirdbar numeric( 10,5 ), --g/cm3
	ph1to1h2o numeric( 10,5 ),
	wthirdbar numeric( 10,5 ), --percent
	wfifteenbar numeric( 10,5 ), --percent
	awc numeric( 10,5 ), --cm/cm
  claytotal numeric( 10,5 ), --percent
	sandtotal numeric( 10,5 ), --percent
	ksat numeric( 10,5 ), --um/s
	om numeric( 10,5 ), --percent
	ll numeric( 10,5 ), --percent
	texdesc text
) as
$$
declare
begin

	--get soils data for apsim
	return query
	select
		t1.areasymbol::text,
		t1.areaname::text,
		t1.mukey::text,
		t1.musym::text,
		t1.muname::text,
		t1.cokey::text,
		t1.comppct::int4,
		t1.slope::int4, --percent
		t1.slopelenusle::int4, --m
		t2.hzdept_r::int4 as depth_top, --cm
		t2.hzdepb_r::int4 as depth_bottom, --cm
		t2.kffact::varchar as kffact, --
		t2.dbthirdbar_r::numeric( 10,3 ) as bulk_density, --g/cm3
		t2.ph1to1h2o_r::numeric( 10,3 ) as ph,
		t2.wthirdbar_r::numeric( 10,3 ), --percent
		t2.wfifteenbar_r::numeric( 10,3 ), --percent
		t2.awc_r::numeric( 10,3 ), --cm/cm
		t2.claytotal_r::numeric( 10,3 ), --percent
		t2.sandtotal_r::numeric( 10,3 ), --percent
		t2.ksat_r::numeric( 10,3 ), --um/s
		t2.om_r::numeric( 10,3 ), --percent
		t2.ll_r::numeric( 10,3 ), --percent
		t3.texdesc::text
	from(
	select
		t5.areasymbol,
		t5.areaname,
		t1.mukey,
		t2.musym,
		t2.muname,
		t3.slope_r as slope,
		t3.slopelenusle_r as slopelenusle,
		t3.cokey,
		t3.comppct_r as comppct,
		row_number()over(
			partition by t3.mukey
			order by t3.comppct_r desc, t3.cokey )::int4 as rnk
	from(
		select
			*
		from unnest( mukey_array ) as mukey ) t1
	left outer join ssurgo_2018.mapunit t2
		on t2.mukey = t1.mukey
	left outer join ssurgo_2018.component t3
		on t3.mukey = t2.mukey
	left outer join ssurgo_2018.legend t4
		on t4.lkey = t2.lkey
	left outer join ssurgo_2018.laoverlap t5
		on t5.lkey = t4.lkey
	where t5.areatypename = 'County or Parish' ) t1
left outer join ssurgo_2018.chorizon t2
	on t2.cokey = t1.cokey
left outer join ssurgo_2018.chtexturegrp t3
	on t3.chkey = t2.chkey
where t1.rnk = 1
and rvindicator = 'Yes'
window wdw as ( partition by t1.mukey )
order by t1.mukey, depth_top asc;
		
end;
$$
language plpgsql;