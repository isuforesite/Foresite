#!/usr/bin/env Python

import os
import xml.etree.ElementTree
from xml.etree.ElementTree import ElementTree, Element, SubElement
import pandas as pd
import io
import json

import soils
import wrapper as apsim
import daymet as clim
import database as db
import op_manager as ops

# Connect to database
dbconn = db.ConnectToDB()

# query scenarios to generate inputs
INPUT_QUERY = 'select * from sandbox.huc12_inputs limit 5'
input_tasks = pd.read_sql( INPUT_QUERY, dbconn )

print( input_tasks )

SIM_NAME = 'huc12_test_job'
START_DATE = '01/01/2016'
END_DATE = '31/12/2018'

### constant spin up crops for multi-year rotation
spin_up_corn = json.loads( open( 'crop_jsons/maize.json', 'r' ).read() )
spin_up_soybean = json.loads( open( 'crop_jsons/soybean.json', 'r' ).read() )

def Get_Date( date_str, year ):
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

def Add_Management_Year( oprns, task, year ):
    ### tillage specs
    till_imp = task[ 'implement' ]
    till_depth = task[ 'depth' ]
    till_incorp = task[ 'residue_incorporation' ]
    till_date = Get_Date( task[ 'timing' ], year )
    ops.Add_Till_Op( oprns, till_date, 'user_defined', till_incorp,
        till_depth )

    ### fert specs
    n_rate = task[ 'kg_n_ha' ]
    n_type = task[ 'n_fertilizer' ]
    n_depth = 0.0
    if n_rate != None and n_rate > 0.0:
        n_date = Get_Date( task[ 'fertilize_n_on' ], year )
        ops.Add_Fertilizer_Op( oprns, n_date, n_rate, n_depth, n_type )

    ### planting specs
    crop = task[ 'sow_crop' ]
    cult = task[ 'cultivar' ]
    dens = task[ 'sowing_density' ]
    depth = task[ 'sowing_depth' ]
    space = task[ 'row_spacing' ]

    plant_date = Get_Date( task[ 'planting_dates' ], year )
    ops.Add_Planting_Op( oprns, plant_date, crop, dens, depth, cult, space )

    harvest_crop = task[ 'harvest' ]
    if crop == 'maize':
        harvest_date = str ( '15-oct' )
    elif crop == 'soybean':
        harvest_date = str ( '1-oct' )
    harvest_date = Get_Date( harvest_date, year )
    ops.Add_Harvest_Op( oprns, harvest_date, harvest_crop )

    return

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
        print( 'test')
        clim.GetDaymetData( 1980, 2018, lat, lon, 'apsim_files/' + met_path )

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
    soil_xml = soils.Create_Soil_XML(
        soil_df,
        Run_SWIM = True,
        SaxtonRawls = True )
    area.append( soil_xml )

    ### surface om
    surfom_xml = apsim.Init_SurfaceOM( 'maize', 'maize', 3500, 65, 0.0 )
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
    output_xml = apsim.Set_Output_Variables( uuid + '.out', outvars )
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

    output_xml.append( apsim.Add_XY_Graph( 'Date', graph_no3, 'no3' ) )
    output_xml.append( apsim.Add_XY_Graph( 'Date', graph_yield, 'yield' ) )
    output_xml.append( apsim.Add_XY_Graph( 'Date', graph_all, 'all outputs' ) )

    #Manager and operations folder
    man_xml = Element( 'folder' )
    man_xml.set( 'name', 'Manager folder' )

    man_xml.append( ops.Add_Empty_Manager() )

    oprns = SubElement( man_xml, 'operations' )
    oprns.set( 'name', 'Operations Schedule' )

    Add_Management_Year( oprns, spin_up_corn, 2016 )
    Add_Management_Year( oprns, spin_up_soybean, 2017 )
    Add_Management_Year( oprns, task, 2018 )

    area.append( man_xml )

    outfile = 'apsim_files/{}.apsim'.format( uuid )
    ### management data
    tree = ElementTree()
    tree._setroot( apsim_xml )
    tree.write( outfile )
