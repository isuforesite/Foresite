#!/usr/bin/env Python

import xml.etree.ElementTree
from xml.etree.ElementTree import ElementTree, Element, SubElement

import apsim.apsim.soils as soils
import apsim.apsim.daymet as clim
import apsim.apsim.database as db
import apsim.apsim.op_manager as man

###
def Soil( soil_df, SWIM = False, SaxtonRawls = False ):
    return soils.Soil( soil_df, SWIM, SaxtonRawls )

###
def connect_to_database( filepath ):
    return db.connect_to_db( filepath )

###
def OpManager():
    return man.OpManager()

###
def Weather():
    return clim.Weather()

###
def set_output_variables( out_file, var_list ):
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

    return output_xml

###
def init_surfaceOM( crop, type, mass, cn_ratio, stand_frac ):
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
def add_xy_graph( x_var, y_vars, title ):
    graph = Element( 'Graph' )
    graph.set( 'name', title )
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
