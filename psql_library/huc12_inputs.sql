drop table if exists sandbox.huc12_inputs;
create table sandbox.huc12_inputs as
select
	uuid_generate_v4() as uuid,
	t1.huc12,
	t1.huc12_name,
	t1.state,
	t1.fips,
	st_y( st_centroid( t3.wkb_geometry ) ) as wth_lat,
	st_x( st_centroid( t3.wkb_geometry ) ) as wth_lon,
	t1.mukey,
	t1.musym,
	t2.implement,
	t2.depth,
	t2.residue_incorporation,
	t2.timing,
	t2.kg_n_ha,
	t2.fertilize_n_on,
	t2.n_fertilizer,
	t2.sow_crop,
	t2.cultivar,
	t2.planting_dates,
	t2.sowing_density,
	t2.sowing_depth,
	t2.row_spacing,
	t2.harvest
from sandbox.huc12_soils t1
inner join public.us_county t3
	on t3.fips = t1.fips
cross join(
	select
		*
	from test20.sample_inputs
	limit 1 ) t2;