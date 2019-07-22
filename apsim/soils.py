#!/usr/bin/env Python

from xml.etree.ElementTree import ElementTree, Element, SubElement
import pandas as pd

###
APSIM_Soil_Layers = [
    ( 0.0, 2.0 ),
    ( 2.0, 4.0 ),
    ( 4.0, 6.0 ),
    ( 6.0, 8.0 ),
    ( 8.0, 10.0 ),
    ( 10.0, 15.0 ),
    ( 15.0, 20.0 ),
    ( 20.0, 25.0 ),
    ( 25.0, 30.0 ),
    ( 30.0, 35.0 ),
    ( 35.0, 40.0 ),
    ( 40.0, 50.0 ),
    ( 50.0, 75.0 ),
    ( 75.0, 100.0 ),
    ( 100.0, 150.0 ),
    ( 150.0, 200.0 )
]

###
def Get_SSURGO_Soils_Data( mukeys, db_conn ):
    mukeystr = ','.join( mukeys )
    query = (
        '''select
            *
        from api.get_soil_properties( \'{''' + mukeystr + '}\'::text[] )' )
    soils_df = pd.read_sql( query, db_conn )

    return soils_df

###
def Create_Layer_XML( parent, name, eqn ):
    for lyr in APSIM_Soil_Layers:
        subelem = SubElement( parent, name )
        subelem.text = str( eqn( lyr ) )
    return

###
def Get_Depth_Weighted( horizon_df ):
    for lyr in APSIM_Soil_Layers:
        top = lyr[0]
        bttm = lyr[1]
        print( apsim_top, apsim_bttm )
        lyrs = horizon_df.loc[
            ( ( horizon_df['hzdept'] >= apsim_top ) & ( horizon_df['hzdepb'] <= apsim_bttm ) )
        ]


            ( ( horizon_df['hzdept'] <= apsim_top ) & ( horizon_df['hzdepb'] >= apsim_bttm ) ) |
            ( ( horizon_df['hzdept'] > apsim_top ) & ( horizon_df['hzdepb'] >= apsim_bttm ) ) |
            ( ( horizon_df['hzdept'] <= apsim_top ) & ( horizon_df['hzdepb'] <= apsim_bttm ) ) |
            ( ( horizon_df['hzdept'] > apsim_top ) & ( horizon_df['hzdepb'] < apsim_bttm ) ) ]

        print( lyrs[ 'hzdept' ] )
    return

###
def Create_Soil_XML( hrzn_df ):

    # base specs
    muname = hrzn_df[ 'muname' ][0]
    texture = hrzn_df[ 'texdesc' ][0]
    mukey = hrzn_df[ 'mukey' ][0]
    musym = hrzn_df[ 'musym' ][0]
    cokey = hrzn_df[ 'cokey' ][0]
    area_sym = hrzn_df[ 'areasymbol' ][0]

    soil_xml = Element( 'Soil' )
    soil_xml.set( 'name', muname )
    rec_id = SubElement( soil_xml, 'RecordNumber' )
    rec_id.text = mukey
    lname = SubElement( soil_xml, 'LocalName' )
    lname = '_'.join( [ str( musym ), str( mukey ), str( cokey ) ] )
    site = SubElement( soil_xml, 'Site' )
    site.text = area_sym
    region = SubElement( soil_xml, 'Region' )
    region.text = area_sym
    state = SubElement( soil_xml, 'State' )
    state.text = area_sym[2:]
    cntry = SubElement( soil_xml, 'Country' )
    cntry.text = 'U.S.'
    lat = SubElement( soil_xml, 'Latitude' )
    lat.text = ''
    lon = SubElement( soil_xml, 'Longitude' )
    lon.text = ''
    sample_yr = SubElement( soil_xml, 'YearOfSampling' )
    sample_yr.text = '2019'
    datasrc = SubElement( soil_xml, 'DataSource' )
    datasrc.text = 'SSURGO 2019'
    comment = SubElement( soil_xml, 'Comment' )
    comment.text = 'Iowa State University AEPE Framework'
    water = SubElement( soil_xml, 'Water' )

    thickness = SubElement( water, 'Thickness' )
    eqn = lambda x: 10 * ( x[1] - x[0] )
    Create_Layer_XML( thickness, 'double', eqn )

    Get_Depth_Weighted( hrzn_df )





    xmltree = ElementTree( soil_xml )
    xmltree.write( mukey + '.apsim' )

    return soil_xml
