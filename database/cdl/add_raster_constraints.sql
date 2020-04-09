-----
--create index "2009_st_convexhull_idx" on cdl."2009" using gist( st_convexhull( rast ) );

-----
select addrasterconstraints(
	'cdl'::name, --rastschema
	'cdl_30m_2019'::name, --rasttable
	'rast'::name, --rastcolumn
	true, --srid
	true, --scale_x
	true, --scale_y
	true, --blocksize_x
	true, --blocksize_y
	true, --same_alignment
	true, --regular_blocking
	true, --num_bands
	true, --pixel_types
	true, --nodata_values
	true, --out_db
	true ); --extent*/