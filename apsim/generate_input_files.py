#!/usr/bin/env Python

import os
import xml.etree.ElementTree
from xml.etree.ElementTree import ElementTree, Element, SubElement

from wrapper import *

user = 'aepe'
database = 'aepe'
port = 2345
host = '129.186.185.33'
dbconn = ConnectToDB( port, host, user, database )

#####
inpt_query = 'select * from test20.sample_inputs limit 5'
input_tasks = pd.read_sql( inpt_query, dbconn )

folder_name = 'foresite'
sim_name = 'sample_test'
start_date = '01/01/2019'
end_date = '31/12/2019'

if not os.path.exists('apsim_files'):
    os.makedirs('apsim_files')

if not os.path.exists('apsim_files/met_files'):
    os.makedirs('apsim_files/met_files')

for idx,task in input_tasks.iterrows():
    uuid = str( task[ 'uuid' ] )
    soil_id = task[ 'soil_sample_id' ]
    wth_id = task[ 'weather_sample_id' ]

    met_path = 'met_files/weather_{}.met'.format( wth_id )

    apsim_xml = Element( 'folder' )
    apsim_xml.set( 'version', '36' )
    apsim_xml.set( 'creator', 'Apsim_Wrapper' )
    apsim_xml.set( 'name', 'S1' )
    sim = SubElement( apsim_xml, 'simulation' )
    sim.set( 'name', sim_name )
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
    clock_start.text = start_date
    clock_end = SubElement( clock, 'end_date' )
    clock_end.set( 'type', 'date' )
    clock_end.set( 'description', 'Enter the end date of the simulation' )
    clock_end.text = end_date
    sumfile = SubElement( sim, 'summaryfile' )
    area = SubElement( sim, 'area' )
    area.set( 'name', 'paddock' )

    ### soil data
    soil_query = (
        '''select
            *
        from test20.design_soil
        where soil_sample_id::int4 = ''' + str( soil_id ) )
    soil_df = pd.read_sql( soil_query, dbconn )
    soil_xml = Create_Soil_XML( uuid, soil_df )
    area.append( soil_xml )

    ### generate .met files
    wth_query = (
        '''select
            *
        from test20.design_weather
        where weather_sample_id::int4 = ''' + str( wth_id ) )
    wth_df = pd.read_sql( wth_query, dbconn )
    Create_Met_Files( wth_df )

    ### surface om
    surfom_xml = Init_SurfaceOM( 'maize', 'maize', 3500, 65, 0.0 )
    area.append( surfom_xml )

    ### fertilizer
    fert_xml = SubElement( area, 'fertiliser' )

    ### crops
    crop_xml = SubElement( area, 'maize' )

    ### output file
    outvars = [
        'dd/mm/yyyy as Date',
        'day',
        'year',
        'yield',
        'biomass',
        'fertiliser',
        'surfaceom_c',
        'n2o_atm()',
        'leach_no3' ]
    output_xml = Set_Output_Variables( uuid + '.out', outvars, 'daily' )
    area.append( output_xml )

    month_ids = {
        'jan': 1,
        'feb': 2,
        'mar': 3,
        'apr': 4,
        'may': 5,
        'jun': 6,
        'jul': 7,
        'aug': 8,
        'sep': 9,
        'oct': 10,
        'nov': 11,
        'dec': 12
    }

    man_xml = Element( 'folder' )
    man_xml.set( 'name', 'Manager folder' )
    oprns = SubElement( man_xml, 'operations' )
    oprns.set( 'name', 'Operations Schedule' )

    spec_yr = 2019
    get_date = lambda d : ( [ d.split( '-' )[0], month_ids[ d.split( '-' )[1] ],
        spec_yr ] )

    ### tillage specs
    till_imp = task[ 'implement' ]
    till_depth = task[ 'depth' ]
    till_incorp = task[ 'residue_incorporation' ]
    till_date = get_date( task[ 'timing' ] )
    till_date = '/'.join( [ str( date ) for date in till_date ] )
    oprns.append(
        Add_Till_Op( till_date, 'user_defined', till_incorp, till_depth ) )

    ### fert specs
    n_rate = task[ 'kg_n_ha' ]
    n_type = task[ 'n_fertilizer' ]
    n_depth = 0.0
    n_date = get_date( task[ 'fertilize_n_on' ] )
    n_date = '/'.join( [ str( date ) for date in n_date ] )
    oprns.append( Add_Fertilizer_Op( n_date, n_rate, n_depth, n_type ) )

    ### planting specs
    crop = task[ 'sow_crop' ]
    cult = task[ 'cultivar' ]
    dens = task[ 'sowing_density' ]
    depth = task[ 'sowing_depth' ]
    space = task[ 'row_spacing' ]
    harvest = task[ 'harvest' ]
    plant_date = get_date( task[ 'planting_dates' ] )
    plant_date = '/'.join( [ str( date ) for date in plant_date ] )
    oprns.append(
        Add_Planting_Op( plant_date, crop, dens, depth, cult, space ) )

    area.append( man_xml )

    outfile = 'apsim_files/{}.apsim'.format( uuid )
    ### management data
    tree = ElementTree()
    tree._setroot( apsim_xml )
    tree.write( outfile )
