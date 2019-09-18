#!/usr/bin/env Python

import xml.etree.ElementTree
from xml.etree.ElementTree import ElementTree, Element, SubElement

from soils import *
from database import *
from op_manager import *

user = 'aepe'
database = 'aepe'
port = 2345
host = '129.186.185.33'
dbconn = ConnectToDB( port, host, user, database )

#####
def Init_Apsim_File( folder_name, sim_name, met_name, met_file, start_date,
    end_date ):
    'folder_name, sim_name, met_name, met_file, start_date, end_date'
    apsim_xml = Element( 'folder' )
    apsim_xml.set( 'version', '36' )
    apsim_xml.set( 'creator', 'Apsim_Wrapper' )
    apsim_xml.set( 'name', 'S1' )
    simgrp = SubElement( apsim_xml, 'folder' )
    simgrp.set( 'name', folder_name )
    sim = SubElement( simgrp, 'simulation' )
    sim.set( 'name', sim_name )
    metfile = SubElement( sim, 'metfile' )
    metfile.set( 'name', met_name )
    filename = SubElement( metfile, 'filename' )
    filename.set( 'name', 'filename' )
    filename.set( 'input', 'yes' )
    filename.text = met_file
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

    return apsim_xml


###
def Set_Output_Variables( out_file, var_list, freq ):
    output_xml = Element( 'outputfile' )
    filename = SubElement( output_xml, 'filename' )
    filename.set( 'name', 'filename' )
    filename.set( 'output', 'yes' )
    filename.text = out_file
    title = SubElement( output_xml, 'title' )
    title.text = out_file.split( '.' )[0]
    vars = SubElement( output_xml, 'variables' )
    vars.set( 'name', 'Output Variables' )

    for var in var_list:
        var_elem = SubElement( vars, 'variable' )
        var_elem.text = var

    consts = SubElement( vars, 'constants' )
    const = SubElement( consts, 'constant' )
    const.set( 'name', 'precision' )
    const.text = '5'

    evnts = SubElement( output_xml, 'events' )
    evnts.set( 'name', 'Output variable events' )
    evnt = SubElement( evnts, 'event' )
    evnt.text = freq

    return output_xml


###
def Init_SurfaceOM( crop, type, mass, cn_ratio, stand_frac ):
    surfom_xml = Element( 'surfaceom' )
    surfom_xml.set( 'name', 'SurfaceOrganicMatter' )
    pool_elem = SubElement( surfom_xml, 'PoolName' )
    pool_elem.set( 'description', 'Organic Matter pool name' )
    pool_elem.set( 'type', 'text' )
    pool_elem.text = crop
    type_elem = SubElement( surfom_xml, 'type' )
    type_elem.set( 'description', 'Organic Matter type' )
    type_elem.set( 'type', 'text' )
    type_elem.text = crop
    mass_elem = SubElement( surfom_xml, 'mass' )
    mass_elem.set( 'description', 'Initial surface residue (kg/ha)' )
    mass_elem.set( 'type', 'text' )
    mass_elem.text = str( mass )
    cnr_elem = SubElement( surfom_xml, 'cnr' )
    cnr_elem.set( 'description', 'C:N ratio of initial residue' )
    cnr_elem.set( 'type', 'text' )
    cnr_elem.text = str( cn_ratio )
    sf_elem = SubElement( surfom_xml, 'standing_fraction' )
    sf_elem.set( 'description', 'Fraction of residue standing' )
    sf_elem.set( 'type', 'text' )
    sf_elem.text = str( stand_frac )

    return surfom_xml


#####
inpt_query = 'select * from test20.test20_inputs limit 5'
input_tasks = pd.read_sql( inpt_query, dbconn )

for idx,task in input_tasks.iterrows():
    uuid = str( task[ 'uuid' ] )
    soil_id = task[ 'soil_sample_id' ]
    wth_id = task[ 'weather_sample_id' ]

    ### soil data
    soil_query = (
        '''select
            *
        from test20.design_soil
        where soil_sample_id::int4 = ''' + str( soil_id ) )
    soil_df = pd.read_sql( soil_query, dbconn )
    soil_xml = Create_Soil_XML( soil_df )
    apsim_xml.append( soil_xml )

    ### generate .met files
    wth_query = (
        '''select
            *
        from test20.design_weather
        where weather_sample_id = ''' + str( wth_id ) )
    wth_df = pd.read_sql( wth_query, dbconn )
    Create_Met_Files( wth_df )

    apsim_xml = Init_Apsim_File(
        'foresite',
        'test20',
        'test20_wth',
        'wth_file/test20_wth.met',
        '01/01/2018',
        '31/12/2019'
    )

    ### surface om
    surfom_xml = Init_SurfaceOM( 'maize', 'maize', 3500, 65, 0.0 )
    apsim_xml.append( surfom_xml )

    ### fertilizer
    fert_xml = SubElement( apsim_xml, 'fertiliser' )

    ### crops
    crop_xml = SubElement( apsim_xml, 'maize' )

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
    apsim_xml.append( output_xml )

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

    spec_yr = 2018
    get_date = lambda d : ( [ d.split( '-' )[0], month_ids[ d.split( '-' )[1] ],
        spec_yr ] )

    ### tillage specs
    till_imp = task[ 'implement' ]
    till_depth = task[ 'depth' ]
    till_incorp = task[ 'residue_incorporation' ]
    till_date = get_date( task[ 'timing' ] )
    till_date = '/'.join( [ str( date ) for date in till_date ] )
    print( till_date )

    man_xml.append(
        Add_Till_Op( till_date, 'user_defined', till_incorp, till_depth ) )

    ### fert specs
    n_rate = task[ 'kg_n_ha' ]
    n_type = task[ 'n_fertilizer' ]
    n_depth = 0.0
    n_date = get_date( task[ 'fertilize_n_on' ] )
    n_date = '/'.join( [ str( date ) for date in n_date ] )
    man_xml.append( Add_Fertilizer_Op( n_date, n_rate, n_depth, n_type ) )

    apsim_xml.append( man_xml )

    ### planting specs
    crop = task[ 'sow_crop' ]
    cult = task[ 'cultivar' ]
    dens = task[ 'sowing_density' ]
    depth = task[ 'sowing_depth' ]
    space = task[ 'row_spacing' ]
    harvest = task[ 'harvest' ]
    plant_date = get_date( task[ 'planting_dates' ] )
    plant_date = '/'.join( [ str( date ) for date in plant_date ] )
    man_xml.append(
        Add_Planting_Op( plant_date, crop, dens, depth, cult, space ) )

    ### management data
    tree = ElementTree()
    tree._setroot( apsim_xml )
    tree.write( 'tester.apsim' )
