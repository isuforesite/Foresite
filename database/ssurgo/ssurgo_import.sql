--Import ESRI fgdb
--ogr2ogr -s_srs "+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23.0 +lon_0=-96.0 +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83 +towgs84=-0.995600,1.901300,0.521500,0.025915,0.009426,0.011599,-0.000620 +units=m +no_defs" -t_srs EPSG:4326 -f "PostgreSQL" PG:"user=user password=password host=host dbname=dbname" gSSURGO_CONUS.gdb -progress -gt 65536 -lco SCHEMA=ssurgo_fy2018 -lco SPATIAL_INDEX=NO
--The sapolygon and mupolygon tables for FY2018 are actually polygon layers and should be imported as such
--ogr2ogr -s_srs "+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23.0 +lon_0=-96.0 +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83 +towgs84=-0.995600,1.901300,0.521500,0.025915,0.009426,0.011599,-0.000620 +units=m +no_defs" -t_srs EPSG:4326 -f "PostgreSQL" PG:"user=user password=password host=host dbname=dbname" gSSURGO_CONUS.gdb [SA|MU]POLYGON -nlt POLYGON -progress -gt 65536 -lco SCHEMA=ssurgo_fy2018 -lco SPATIAL_INDEX=NO

--
do $$
declare
  fix bool := true;
  oid int := 0;
  mupolys_inv int[];
  sapolys_inv int[];
begin
  --
  --perform api.ssurgo__check( 'ssurgo_2018' );

  --Remove sequences
  --perform api.drop_sequences( 'ssurgo_2018', true );

/*
  --Remove unused tables
  drop table if exists cointerp;
  drop table if exists featline;
  drop table if exists featpoint;
  drop table if exists muline;
  drop table if exists mupoint;
  drop table if exists ten_meter_eliminated_polygons;
  drop table if exists thirty_meter_eliminated_polygon;
  drop table if exists ninety_meter_eliminated_polygon;

  --Remove spatial indicies created by ogr2ogr import
  drop index if exists mupolygon_wkb_geometry_geom_idx;
  drop index if exists sapolygon_wkb_geometry_geom_idx;


  --Try to fix invalid geometry
  if( fix = true ) then
    --sapolygon
    sapolys_inv := array(
      select
        objectid
      from ssurgo_2018.sapolygon
      where
        st_isvalid( wkb_geometry ) = false
      order by
        objectid asc );

    foreach oid in array sapolys_inv
    loop
      raise notice 'Fixing geometry sapolygon %', oid;

      update ssurgo_2018.sapolygon
      set wkb_geometry = st_makevalid( wkb_geometry )
      where
        objectid = oid;
    end loop;

    --mupolygon
    mupolys_inv := array(
      select
        objectid
      from ssurgo_2018.mupolygon
      where
        st_isvalid( wkb_geometry ) = false
      order by
        objectid asc );

    foreach oid in array mupolys_inv
    loop
      raise notice 'Fixing geometry mupolygon %', oid;

      update ssurgo_2018.mupolygon
      set wkb_geometry = st_makevalid( wkb_geometry )
      where
        objectid = oid;
    end loop;
  end if;
*/

/*
  --sacatalog
  raise notice 'Modifying table sacatalog';
  alter table ssurgo_2018.sacatalog
  drop column if exists objectid,
  add constraint sacatalog_pkey
    primary key( sacatalogkey ),
  add constraint sacatalog_akey
    unique( areasymbol );


  --legend
  raise notice 'Modifying table legend';
  alter table ssurgo_2018.legend
  drop column if exists objectid,
  add constraint legend_pkey
    primary key( lkey ),
  add constraint legend_akey
    unique( areasymbol ),
  add constraint legend_lkey_fkey
    foreign key( lkey )
    references ssurgo_2018.sacatalog( sacatalogkey ),
  add constraint legend_areasymbol_fkey
    foreign key( areasymbol )
    references ssurgo_2018.sacatalog( areasymbol );

  --sapolygon
  raise notice 'Modifying table sapolygon';
  alter table ssurgo_2018.sapolygon
  add constraint sapolygon_lkey_fkey
    foreign key( lkey )
    references ssurgo_2018.legend( lkey ),
  add constraint sapolygon_areasymbol_fkey
    foreign key( areasymbol )
    references ssurgo_2018.legend( areasymbol ),
  add constraint sapolygon_wkb_geometry_check
    check( st_isvalid( wkb_geometry ) );
  create index sapolygon_lkey_fidx
    on ssurgo_2018.sapolygon( lkey asc );
  create index sapolygon_areasymbol_fidx
    on ssurgo_2018.sapolygon( areasymbol asc );
  create index sapolygon_wkb_geometry_gist
    on ssurgo_2018.sapolygon
    using gist( wkb_geometry );

  --laoverlap
  raise notice 'Modifying table laoverlap';
  alter table ssurgo_2018.laoverlap
  drop column if exists objectid,
  add constraint laoverlap_pkey
    primary key( lareaovkey ),
  add constraint laoverlap_lkey_fkey
    foreign key( lkey )
    references ssurgo_2018.legend( lkey );
  create index laoverlap_lkey_fidx
    on ssurgo_2018.laoverlap( lkey asc );

  --mapunit
  raise notice 'Modifying table mapunit';
  alter table ssurgo_2018.mapunit
  drop column if exists objectid,
  add constraint mapunit_pkey
    primary key( mukey ),
  add constraint mapunit_lkey_fkey
    foreign key( lkey )
    references ssurgo_2018.legend( lkey );
  create index mapunit_lkey_fidx
    on ssurgo_2018.mapunit( lkey asc );

  --mupolygon
  raise notice 'Modifying table mupolygon';
  alter table ssurgo_2018.mupolygon
  add constraint mupolygon_mukey_fkey
    foreign key( mukey )
    references ssurgo_2018.mapunit( mukey ),
  add constraint mupolygon_wkb_geometry_check
    check( st_isvalid( wkb_geometry ) );
  create index mupolygon_mukey_fidx
    on ssurgo_2018.mupolygon( mukey asc );
  create index mupolygon_wkb_geometry_gist
    on ssurgo_2018.mupolygon
    using gist( wkb_geometry );

  --muaggatt
  raise notice 'Modifying table muaggatt';
  alter table ssurgo_2018.muaggatt
  drop column if exists objectid,
  add constraint muaggatt_pkey
    primary key( mukey ),
  add constraint muaggatt_mukey_fkey
    foreign key( mukey )
    references ssurgo_2018.mapunit( mukey );

  --mucropyld
  raise notice 'Modifying table mucropyld';
  alter table ssurgo_2018.mucropyld
  drop column if exists objectid,
  add constraint mucropyld_pkey
    primary key( mucrpyldkey ),
  add constraint mucropyld_mukey_fkey
    foreign key( mukey )
    references ssurgo_2018.mapunit( mukey );
  create index mucropyld_mukey_fidx
    on ssurgo_2018.mucropyld( mukey asc );

  --muaoverlap
  raise notice 'Modifying table muaoverlap';
  alter table ssurgo_2018.muaoverlap
  drop column if exists objectid,
  add constraint muaoverlap_pkey
    primary key( muareaovkey ),
  add constraint muaoverlap_lareaovkey_fkey
    foreign key( lareaovkey )
    references ssurgo_2018.laoverlap( lareaovkey ),
  add constraint muaoverlap_mukey_fkey
    foreign key( mukey )
    references ssurgo_2018.mapunit( mukey );
  create index muaoverlap_lareaovkey_fidx
    on ssurgo_2018.muaoverlap( lareaovkey asc );
  create index muaoverlap_mukey_fidx
    on ssurgo_2018.muaoverlap( mukey asc );

  --component
  raise notice 'Modifying table component';
  alter table ssurgo_2018.component
  drop column if exists objectid,
  add constraint component_pkey
    primary key( cokey ),
  add constraint component_mukey_fkey
    foreign key( mukey )
    references ssurgo_2018.mapunit( mukey );
  create index component_mukey_fidx
    on ssurgo_2018.component( mukey asc );

  --cocropyld
  raise notice 'Modifying table cocropyld';
  alter table ssurgo_2018.cocropyld
  drop column if exists objectid,
  add constraint cocropyld_pkey
    primary key( cocropyldkey ),
  add constraint cocropyld_cokey_fkey
    foreign key( cokey )
    references ssurgo_2018.component( cokey );
  create index cocropyld_cokey_fidx
    on ssurgo_2018.cocropyld( cokey asc );

  --comonth
  raise notice 'Modifying table comonth';
  alter table ssurgo_2018.comonth
  drop column if exists objectid,
  add constraint comonth_pkey
    primary key( comonthkey ),
  add constraint comonth_cokey_fkey
    foreign key( cokey )
    references ssurgo_2018.component( cokey );
  create index comonth_cokey_fidx
    on ssurgo_2018.comonth( cokey asc );

  --corestrictions
  raise notice 'Modifying table corestrictions';
  alter table ssurgo_2018.corestrictions
  drop column if exists objectid,
  add constraint corestrictions_pkey
    primary key( corestrictkey ),
  add constraint corestrictions_cokey_fkey
    foreign key( cokey )
    references ssurgo_2018.component( cokey );
  create index corestrictions_cokey_fidx
    on ssurgo_2018.corestrictions( cokey asc );

  --chorizon
  raise notice 'Modifying table chorizon';
  alter table ssurgo_2018.chorizon
  drop column if exists objectid,
  add constraint chorizon_pkey
    primary key( chkey ),
  add constraint chorizon_cokey_fkey
    foreign key( cokey )
    references ssurgo_2018.component( cokey );
  create index chorizon_cokey_fidx
    on ssurgo_2018.chorizon( cokey asc );

  --chfrags
  raise notice 'Modifying table chfrags';
  alter table ssurgo_2018.chfrags
  drop column if exists objectid,
  add constraint chfrags_pkey
    primary key( chfragskey ),
  add constraint chfrags_chkey_fkey
    foreign key( chkey )
    references ssurgo_2018.chorizon( chkey );
  create index chfrags_chkey_fidx
    on ssurgo_2018.chfrags( chkey asc );

  --chtexturegrp
  raise notice 'Modifying table chtexturegrp';
  alter table ssurgo_2018.chtexturegrp
  drop column if exists objectid,
  add constraint chtexturegrp_pkey
    primary key( chtgkey ),
  add constraint chtexturegrp_chkey_fkey
    foreign key( chkey )
    references ssurgo_2018.chorizon( chkey );
  create index chtexturegrp_chkey_fidx
    on ssurgo_2018.chtexturegrp( chkey asc );

  --chtexture
  raise notice 'Modifying table chtexture';
  alter table ssurgo_2018.chtexture
  drop column if exists objectid,
  add constraint chtexture_pkey
    primary key( chtkey ),
  add constraint chtexture_chtgkey_fkey
    foreign key( chtgkey )
    references ssurgo_2018.chtexturegrp( chtgkey );
  create index chtexture_chtgkey_fidx
    on ssurgo_2018.chtexture( chtgkey asc );
*/


  --valu1
  --Remove duplicates and nonexistent mukeys...
  --It appears the first objectid row (asc) always contains the most data
  raise notice 'Cleaning table valu1';
  delete from ssurgo_2018.valu1
  where objectid in(
    select
      t1.objectid
    from(
      select
        objectid,
        row_number() over(
          partition by mukey
          order by objectid asc ) as rnk
      from ssurgo_2018.valu1 ) t1
    where
      t1.rnk > 1
    union
    select
      t1.objectid
    from ssurgo_2018.valu1 t1
      left outer join ssurgo_2018.mapunit j1
        on j1.mukey = t1.mukey
    where
      j1.mukey is null );

  --valu1
  raise notice 'Modifying table valu1';
  alter table ssurgo_2018.valu1
  drop column if exists objectid,
  add constraint valu1_pkey
    primary key( mukey ),
  add constraint valu1_mukey_fkey
    foreign key( mukey )
    references ssurgo_2018.mapunit( mukey );


end;
$$ language plpgsql;
