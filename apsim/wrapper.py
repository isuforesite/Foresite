#!/usr/bin/env Python

import xml.etree.ElementTree
from xml.etree.ElementTree import ElementTree, Element, SubElement

from soils import *
from database import *

user = 'aepe'
database = 'aepe'
port = 2345
host = '129.186.185.33'
ssurgo_db = ConnectToDB( port, host, user, database )

#####
def Init_Apsim_File( folder_name, sim_name, met_name, met_file, start_date,
    end_date ):
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
def Output_Variables( out_file, var_list, freq ):
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
    const.text = 5

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
    mass_elem.text = mass
    cnr_elem = SubElement( surfom_xml, 'cnr' )
    cnr_elem.set( 'description', 'C:N ratio of initial residue' )
    cnr_elem.set( 'type', 'text' )
    cnr_elem.text = cn_ratio
    sf_elem = SubElement( surfom_xml, 'standing_fraction' )
    sf_elem.set( 'description', 'Fraction of residue standing' )
    sf_elem.set( 'type', 'text' )
    sf_elem.text = stand_frac

    return surfom_xml



#####
mukeys = [ '403351' ]
soils_lyr_df = Get_SSURGO_Soils_Data( mukeys, ssurgo_db )
for mukey in mukeys:
    ### initialize sim
    apsim_xml = Init_Apsim_File()

    ### soil data
    soil_df = soils_lyr_df.loc[ soils_lyr_df[ 'mukey' ] == mukey ]
    soil_xml = Create_Soil_XML( soil_df )
    apsim_xml.append( soil_xml )

    ### surface om
    surfom_xml = Init_SurfaceOM( 'maize', 'maize', 3500, 65, 0.0 )

    ### fertilizer
    fert_xml = SubElement( apsim_xml, 'fertiliser' )

    ### crops
    crop_xml = SubElement( apsim_xml, 'maize' )

    ### output file
    outvars = [ 'dd/mm/yyyy as Date', 'day', 'year', 'yield', 'biomass',
        'fertiliser', 'surfaceom_c', 'n2o_atm()', 'leach_no3' ]
    output_xml = Output_Variables( mukey + '.out', outvars, 'daily' )

    ### management data
    

    tree = ElementTree()
    tree._setroot( apsim_xml )
    tree.write( 'tester.apsim' )
