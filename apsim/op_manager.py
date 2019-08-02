#!/usr/bin/env Python

import xml.etree.ElementTree
from xml.etree.ElementTree import ElementTree, Element, SubElement

###
def Init_New_Op( date ):
    op_elem = Element( 'operation' )
    op_elem.set( 'condition', 'start_of_day' )
    date_elem = SubElement( op_elem, 'date' )
    date_elem.text = date
    return op_elem

###
def Add_Till_Op( date, type, f_incorp = None, tillage_depth = None ):
    op_elem = Init_New_Op( date )
    if type == 'user_defined':
        action = ( 'SurfaceOrganicMatter tillage type = user_defined, ' +
            'f_incorp = {} (0-1), tillage_depth = {} (mm)' ).format(
            str( f_incorp ), str( tillage_depth ) )
    else:
        action = 'SurfaceOrganicMatter tillage type = ' + type
    act_elem = SubElement( op_elem, 'action' )
    act_elem.text = action
    return op_elem

###
def Add_Fertilizer_Op( date, value, depth, type ):
    op_elem = Init_New_Op( date )
    action = ( 'fertiliser apply ' +
        'ammount = {} (kg/ha), depth = {} (mm), type = {}').format(
        str( value ), str( depth ), type )
    act_elem = SubElement( op_elem, 'action' )
    act_elem.text = action
    return op_elem

###
def Add_Manure_Op( date, type, name, mass, cnr, cpr ):
    op_elem = Init_New_Op( date )
    action = (
        'SurfaceOrganicMatter add_surfaceom ' +
        'type = {}, name = {}, mass = {} (kg/ha), cnr = {}, cpr = {}' ).format(
        type, name, str( mass ), str( cnr ), str( cpr ) )
    act_elem = SubElement( op_elem, 'action' )
    act_elem.text = action
    return op_elem

###
def Add_Planting_Op( date, crop, density, depth, cultivar, spacing ):
    op_elem = Init_New_Op( date )
    action = ( '{} sow plants = {} (plants/m2), sowing_depth = {} (mm), ' +
        'cultivar = {}, row_spacing = {} (mm), crop_class = plant' ).format(
        crop, str( density ), str( depth ), cultivar, str( spacing ) )
    print( action )
    act_elem = SubElement( op_elem, 'action' )
    act_elem.text = action
    return op_elem

###
def Add_Harvest_Op( date, crop ):
    op_elem = Init_New_Op( date )
    action = ( '{} end_crop' ).format( crop )
    act_elem = SubElement( op_elem, 'action' )
    act_elem.text = action
    return op_elem


cal_obj = [
    {
        'date': '1/4/2007',
        'op_class': 'Tillage',
        'type': 'disc',
        'f_incorp': None,
        'depth': None
    },
    {
        'date': '13/4/2007',
        'op_class': 'Tillage',
        'type': 'user_defined',
        'f_incorp': 0.0,
        'depth': 50.0
    },
    {
        'date': '13/4/2007',
        'op_class': 'Fertilizer',
        'type': 'urea_no3',
        'depth': 10,
        'amount': 25
    },
    {
        'date': '15/4/2007',
        'op_class': 'Planting',
        'type': 'urea_no3',
        'depth': 10,
        'amount': 25
    },
]


###
def Add_Management_Oprns( calender ):
    man_xml = Element( 'folder' )
    man_xml.set( 'name', 'Manager folder' )
    oprns = SubElement( man_xml, 'operations' )
    oprns.set( 'name', 'Operations Schedule' )

    # for op in op_cal:
    #     op_cal = SubElement( oprns, 'operation' )
    #     op_cal.set( '')

    return man_xml




Add_Till_Op( '13/4/2007', 'user_defined', 0.0, 50.0 )
Add_Fertilizer_Op( '14/4/2007', 25.0, 10.0, 'urea_no3' )
Add_Planting_Op( '15/4/2007', 'maize', 8, 50.0, 'B_115', 762.0 )
Add_Harvest_Op( '20/10/2010', 'maize' )
Add_Manure_Op( '20/10/2010', 'manure', 'manure_app', 10000.0, 20.0, 50.0 )
