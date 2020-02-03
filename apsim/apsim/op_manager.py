#!/usr/bin/env Python

import xml.etree.ElementTree
from xml.etree.ElementTree import ElementTree, Element, SubElement

###
def init_new_op( date ):
    op_elem = Element( 'operation' )
    op_elem.set( 'condition', 'start_of_day' )
    date_elem = SubElement( op_elem, 'date' )
    date_elem.text = date

    return op_elem

class OpManager:

    ###
    def __init__( self ):
        self.man_xml = Element( 'folder' )
        self.man_xml.set( 'name', 'Manager folder' )
        self.ops_xml = SubElement( self.man_xml, 'operations' )
        self.ops_xml.set( 'name', 'Operations Schedule' )

    ###
    def add_till_op( self, date, type, f_incorp = None, tillage_depth = None ):
        op_elem = init_new_op( date )
        if type == 'user_defined':
            action = ( 'SurfaceOrganicMatter tillage type = user_defined, ' +
                'f_incorp = {} (0-1), tillage_depth = {} (mm)' ).format(
                str( f_incorp ), str( tillage_depth ) )
        else:
            action = 'SurfaceOrganicMatter tillage type = ' + type
        act_elem = SubElement( op_elem, 'action' )
        act_elem.text = action
        self.ops_xml.append( op_elem )

    ###
    def add_fertilizer_op( self, date, value, depth, type ):
        op_elem = init_new_op( date )
        action = ( 'Fertiliser apply ' +
            'amount = {} (kg/ha), depth = {} (mm), type = {} ()').format(
            str( value ), str( depth ), type )
        act_elem = SubElement( op_elem, 'action' )
        act_elem.text = action
        self.ops_xml.append( op_elem )

    ###
    def add_manure_op( self, date, type, name, mass, cnr, cpr ):
        op_elem = init_new_op( date )
        action = (
            'SurfaceOrganicMatter add_surfaceom ' +
            'type = {}, name = {}, mass = {} (kg/ha), cnr = {}, cpr = {}' ).format(
            type, name, str( mass ), str( cnr ), str( cpr ) )
        act_elem = SubElement( op_elem, 'action' )
        act_elem.text = action
        self.ops_xml.append( op_elem )

    ###
    def add_planting_op( self, date, crop, density, depth, cultivar, spacing ):
        op_elem = init_new_op( date )
        action = ( '{} sow plants = {} (plants/m2), sowing_depth = {} (mm), ' +
            'cultivar = {}, row_spacing = {} (mm), crop_class = plant' ).format(
            crop, str( density ), str( depth ), cultivar, str( spacing ) )
        act_elem = SubElement( op_elem, 'action' )
        act_elem.text = action
        self.ops_xml.append( op_elem )

    ###
    def add_harvest_op( self, date, crop ):
        op_elem = init_new_op( date )
        action = ( '{} end_crop' ).format( crop )
        act_elem = SubElement( op_elem, 'action' )
        act_elem.text = action
        self.ops_xml.append( op_elem )

    #Add empty manager with bu/ac for corn/soy and the gradient for SWIM to work.
    def add_empty_manager( self, bbc_potential = [ 200, 100 ] ):
        """
        Creates an empty APSIM 'Manager' folder to hold bu/ac calculationg and
        SWIM bbc_potential = profile depth - tile/water table depth
        without the gradient set.

        Returns:
            [xml] -- [XML for an empty manager]
        """
        empty_man = SubElement( self.man_xml, 'manager' )
        empty_man.set( 'name', 'Empty manager' )
        init_script = SubElement( empty_man, 'script' )
        init_script_text = SubElement( init_script, 'text' )
        init_event = SubElement( init_script, 'event' ).text = 'init'

        gradient_script = SubElement( empty_man, 'script' )
        gradient_script_txt = SubElement( gradient_script, 'text' )

        #!!!!IMPORTANT!!!!!
        #subsurface_drain and subsurface_drain_no3 won't work unless bbc_potential is se
        #!!!!!!!!!!!!!!!!!!

        gradient_script_txt.text = """corn_buac   = maize.yield * 0.0159/0.85  ! corn yield in bushels/acre@15% moisture
        !soy_buac   = soybean.yield * 0.0149/0.87  !  soybean yield in bushels/acre

        !bbc_gradient = -1
        bbc_potential = {} - {}
        """.format(bbc_potential[0],bbc_potential[1])
        gradient_event = SubElement( gradient_script, 'event' ).text = 'start_of_day'

        end_script = SubElement( empty_man, 'script' )
        end_script_text = SubElement( end_script, 'text' )
        end_event = SubElement( end_script, 'event' ).text = 'end_of_day'
