#!/usr/bin/env Python

import xml.etree.ElementTree
from xml.etree.ElementTree import ElementTree, Element, SubElement

import apsim.soils as soils
import apsim.daymet as daymet
import apsim.database as db
import apsim.op_manager as man

###
def Create_Soil( soil_df, SWIM = False, SaxtonRawls = False ):
    return soils.Create_Soil_XML( soil_df, Run_SWIM = False, SaxtonRawls = False )

###
def Create_Met_File( filepath, init_yr, end_yr, lat, lon ):
    return daymet.GetDaymetData( init_yr, end_yr, lat, lon, filepath )

def Create_Met_File( filepath, init_yr, end_yr ):
    return daymet.GetDaymetData( init_yr, end_yr, lat, lon, filepath )

###
def Connect_To_Database( filepath ):
    return db.ConnectToDB( filepath )

###
def Create_Op_Manager():
    return man.OpManager()

# ###
# def
#
#     return man.Add_Till_Op( oprns, till_date, 'user_defined', till_incorp,
#     till_depth )

###
def Set_Output_Variables( out_file, var_list ):
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
    evnt.text = 'daily'

    var_list = [ var for var in var_list
        if var not in [ 'dd/mm/yyyy as Date', 'day', 'year' ] ]

    output_xml.append( Add_XY_Graph( 'Date', var_list, 'Outputs' ) )

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

###
def Add_XY_Graph( x_var, y_vars, title ):
    graph = Element( 'Graph' )
    graph.set( 'name', 'Output Plot' )
    legend = SubElement( graph, 'Legend' )
    checked = SubElement( legend, 'CheckedTitles' )
    plot = SubElement( graph, 'Plot' )
    series = SubElement( plot, 'SeriesType' )
    series.text = 'Solid line'
    pt_type = SubElement( plot, 'PointType' )
    pt_type.text = 'Circle'
    col = SubElement( plot, 'colour' )
    xvar = SubElement( plot, 'X' )
    xvar.text = x_var
    for yv in y_vars:
        yvar = SubElement( plot, 'Y' )
        yvar.text = yv

    gdafile = SubElement( plot, 'GDApsimFileReader' )
    gdafile.set( 'name', 'ApsimFileReader' )

    return graph

# ###
# def Add_Soil( )
