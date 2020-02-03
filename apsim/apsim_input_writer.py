#!/usr/bin/env Python

import os
import xml.etree.ElementTree
from xml.etree.ElementTree import ElementTree, Element, SubElement
import pandas as pd
import io
import json

import apsim.wrapper as apsim

# Connect to database
dbconn = apsim.connect_to_database( 'database.ini' )

# query scenarios to generate inputs
SIM_NAME = 'huc12_test_job'
START_DATE = '01/01/2016'
END_DATE = '31/12/2018'
INPUT_QUERY = 'select * from sandbox.huc12_inputs limit 5'
input_tasks = pd.read_sql( INPUT_QUERY, dbconn )

# constant spin up crops for multi-year rotation
spin_up_corn = json.loads( open( 'crop_jsons/maize.json', 'r' ).read() )
spin_up_soybean = json.loads( open( 'crop_jsons/soybean.json', 'r' ).read() )

###
def get_date( date_str, year ):
    month_ids = {
        'jan': 1, 'feb': 2, 'mar': 3,
        'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9,
        'oct': 10, 'nov': 11, 'dec': 12
    }
    date = [ date_str.split( '-' )[0],
        month_ids[ date_str.split( '-' )[1] ],
        year ]
    date = '/'.join( [ str( d ) for d in date ] )

    return date

###
def add_management_year( man_ops, task, year ):
    ### tillage specs
    till_imp = task[ 'implement' ]
    till_depth = task[ 'depth' ]
    till_incorp = task[ 'residue_incorporation' ]
    till_date = get_date( task[ 'timing' ], year )
    man_ops.add_till_op( till_date, 'user_defined', till_incorp, till_depth )

    ### fert specs
    n_rate = task[ 'kg_n_ha' ]
    n_type = task[ 'n_fertilizer' ]
    n_depth = 0.0
    if n_rate != None and n_rate > 0.0:
        n_date = get_date( task[ 'fertilize_n_on' ], year )
        man_ops.add_fert_op( n_date, n_rate, n_depth, n_type )

    ### planting specs
    crop = task[ 'sow_crop' ]
    cult = task[ 'cultivar' ]
    dens = task[ 'sowing_density' ]
    depth = task[ 'sowing_depth' ]
    space = task[ 'row_spacing' ]

    plant_date = get_date( task[ 'planting_dates' ], year )
    man_ops.add_plant_op( plant_date, crop, dens, depth, cult, space )

    harvest_crop = task[ 'harvest' ]
    if crop == 'maize':
        harvest_date = str ( '15-oct' )
    elif crop == 'soybean':
        harvest_date = str ( '1-oct' )
    harvest_date = get_date( harvest_date, year )
    man_ops.add_harvest_op( harvest_date, harvest_crop )

    return

################################################################################
# create directories for dumping .apsim and .met files
if not os.path.exists( 'apsim_files' ):
    os.makedirs( 'apsim_files' )
if not os.path.exists( 'apsim_files/met_files' ):
    os.makedirs( 'apsim_files/met_files' )

# loop of tasks
for idx,task in input_tasks.iterrows():
    uuid = str( task[ 'uuid' ] )
    mukey = task[ 'mukey' ]
    fips = task[ 'fips' ]
    lat = task[ 'wth_lat' ]
    lon = task[ 'wth_lon' ]

    # get soils data
    soil_query = '''select * from
        api.get_soil_properties( array[{}]::text[] )'''.format( mukey )
    soil_df = pd.read_sql( soil_query, dbconn )
    if soil_df.empty:
        continue

    # generate .met files
    met_path = 'met_files/weather_{}.met'.format( fips )
    if not os.path.exists( 'apsim_files/' + met_path ):
        wth_obj = apsim.Weather().from_daymet( lat, lon, 1980, 2018 )
        wth_obj.write_met_file( 'apsim_files/{}'.format( met_path ) )

    # initialize .apsim xml
    apsim_xml = Element( 'folder' )
    apsim_xml.set( 'version', '36' )
    apsim_xml.set( 'creator', 'Apsim_Wrapper' )
    apsim_xml.set( 'name', 'S1' )
    sim = SubElement( apsim_xml, 'simulation' )

    sim.set( 'name', SIM_NAME )

    metfile = SubElement( sim, 'metfile' )
    metfile.set( 'name', 'foresite_weather' )
    filename = SubElement( metfile, 'filename' )
    filename.set( 'name', 'filename' )
    filename.set( 'input', 'yes' )
    filename.text = met_path
    clock = SubElement( sim, 'clock' )
    clock_start = SubElement( clock, 'start_date' )
    clock_start.set( 'type', 'date' )
    clock_start.set( 'description', 'Enter the start date of the simulation' )
    clock_start.text = START_DATE
    clock_end = SubElement( clock, 'end_date' )
    clock_end.set( 'type', 'date' )
    clock_end.set( 'description', 'Enter the end date of the simulation' )
    clock_end.text = END_DATE
    sumfile = SubElement( sim, 'summaryfile' )
    area = SubElement( sim, 'area' )
    area.set( 'name', 'paddock' )

    # add soil xml
    soil = apsim.Soil(
        soil_df,
        SWIM = False,
        SaxtonRawls = True )

    area.append( soil.soil_xml() )

    ### surface om
    surfom_xml = apsim.init_surfaceOM( 'maize', 'maize', 3500, 65, 0.0 )
    area.append( surfom_xml )

    ### fertilizer
    fert_xml = SubElement( area, 'fertiliser' )

    ### crops
    crop_xml = SubElement( area, 'maize' )
    crop_xml = SubElement( area, 'soybean' )
    crop_xml = SubElement( area, 'wheat' )

    ### output file
    outvars = [
        'dd/mm/yyyy as Date', 'day', 'year',
        'yield', 'biomass', 'fertiliser',
        'surfaceom_c', 'subsurface_drain',
        'subsurface_drain_no3', 'leach_no3',
        'corn_buac', 'soy_buac' ]
    output_xml = apsim.set_output_variables( uuid + '.out', outvars )
    area.append( output_xml )

    graph_no3 = [
        'Cumulative subsurface_drain',
        'Cumulative subsurface_drain_no3',
        'Cumulative leach_no3'
    ]
    graph_yield = [
        'yield',
        'biomass',
        'corn_buac'
    ]
    graph_all = [
        'yield', 'biomass', 'fertiliser',
        'surfaceom_c', 'Cumulative subsurface_drain',
        'Cumulative subsurface_drain_no3',
        'Cumulative leach_no3', 'corn_buac',
        'soy_buac'
    ]

    output_xml.append( apsim.add_xy_graph( 'Date', graph_no3, 'no3' ) )
    output_xml.append( apsim.add_xy_graph( 'Date', graph_yield, 'yield' ) )
    output_xml.append( apsim.add_xy_graph( 'Date', graph_all, 'all outputs' ) )

    op_man = apsim.OpManager()
    op_man.add_empty_manager()

    add_management_year( op_man, spin_up_corn, 2016 )
    add_management_year( op_man, spin_up_soybean, 2017 )
    add_management_year( op_man, task, 2018 )

    area.append( op_man.man_xml )

    outfile = 'apsim_files/{}.apsim'.format( uuid )
    ### management data
    tree = ElementTree()
    tree._setroot( apsim_xml )
    tree.write( outfile )
