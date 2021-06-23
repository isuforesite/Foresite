#!/usr/bin/env Python

import pandas as pd
import xml.etree.ElementTree
from xml.etree.ElementTree import ElementTree, Element, SubElement

###
def init_new_op( date ):
    """creates new xml operation on specified date

    Args:
        date (str): date on which to apply operation

    Returns:
        [xml]: xml containing the new operation
    """
    op_elem = Element( 'operation' )
    op_elem.set( 'condition', 'start_of_day' )
    date_elem = SubElement( op_elem, 'date' )
    date_elem.text = date

    return op_elem

def get_date( date_str, year ):
    """Formats dd-mmm (eg 23-apr) date value to dd/mm/yyyy (eg 23/4/2018)

    Args:
        date_str (str): dict date string
        year (str): year to add ops for

    Returns:
        [str]: reformatted date string
    """
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

def get_mgmt_values( mgmt_dict, mgmt_key ):
    """Loop through the mgmt dict and return all instances of desired mgmt as list

    Args:
        mgmt_dict (dict): the dict to get whatever mgmt info from
        mgmt_key (str): the key to search for and get value from

    Returns:
        [list]: list containing all values for instances of desired key
    """
    values = [val for key, val in mgmt_dict.items() if mgmt_key in key]
    if values == None:
        pass
    else:
        return values

def create_fert_df(mgmt_dict, amount_key, formula_key, depth_key, date_key, year):
    """creates a new dataframe for fertilizer operations

    Args:
        mgmt_dict (dict): dict containing fertiliser mgmt data
        amount_key (str): key for amount of fertiliser to apply
        formula_key (str): key for what type/formulation of fert to apply
        depth_key (str): key for depth to apply fertiliser (eg. 0 surface or 50 knife)
        date_key (str): key for date to apply fertiliser (eg. 15-oct, 23-sep)
        year (int): year to conduct operations

    Returns:
        [pd.df]: dataframe with fertiliser information
    """
    #get all fertilizer keys for mgmt ops
    fert_amount_values = get_mgmt_values(mgmt_dict, amount_key)
    fert_date_values = get_mgmt_values(mgmt_dict, date_key)
    #convert dates
    fert_date_values = [get_date(date, year) for date in fert_date_values]
    fert_formula_values = get_mgmt_values(mgmt_dict, formula_key)
    fert_depth_values = get_mgmt_values(mgmt_dict, depth_key)
    #convert to df
    fert_df = pd.DataFrame(list(zip(fert_amount_values, fert_date_values, fert_formula_values, fert_depth_values)),
    columns=['fert_amount', 'fert_date', 'fert_formula', 'fert_depth'])
    return fert_df

def add_fert_ops(df, mgmt_obj):
    '''
    loop through df and add an fert op to operations obj. for each instance of fertilizer mgmt
    '''
    #unzip dataframe values for each row
    for amount, date, formula, depth in zip(df['fert_amount'], df['fert_date'], df['fert_formula'], df['fert_depth']):
        if amount != None and amount > 0.0:
            mgmt_obj.add_fert_op(date, amount, depth, formula)
    return mgmt_obj

def create_tillage_df(mgmt_dict, implement_key, depth_key, f_incorp_key, date_key, year):
    """creates a new df for tillage operations from mgmt dict/dict

    Args:
        mgmt_dict (dict): dict with management data
        implement_key (str): key for which implement/machinery to till with
        depth_key (str): key for depth to till
        f_incorp_key (str): key for % of residue ot incorporate
        date_key (str): key for date to apply tillage (eg. 15-oct, 23-sep)
        year (int): year to conduct operations

    Returns:
        [pd.df]: dataframe with all tillage operations to conduct
    """
    #get all tillage keys for mgmt ops
    implement_values = get_mgmt_values(mgmt_dict, implement_key)
    depth_values = get_mgmt_values(mgmt_dict, depth_key)
    f_incorp_values = get_mgmt_values(mgmt_dict, f_incorp_key)
    date_values = get_mgmt_values(mgmt_dict, date_key)
    #convert dates
    date_values = [get_date(date, year) for date in date_values]
    #convert to df
    tillage_df = pd.DataFrame(list(zip(implement_values, depth_values, f_incorp_values, date_values)),
    columns=['tillage_implement', 'tillage_depth', 'fract_residue_incorp', 'tillage_date'])
    return tillage_df

def add_tillage_ops(df, mgmt_obj):
    '''
    loop through df and add tillage op to operations obj. for each instance of tillage mgmt
    '''
    for implement, depth, f_incorp, date in zip(df['tillage_implement'], df['tillage_depth'], df['fract_residue_incorp'], df['tillage_date']):
        if f_incorp != None and f_incorp > 0.0:
            mgmt_obj.add_till_op(date, implement, f_incorp, depth)
    return mgmt_obj

def create_planting_df(mgmt_dict, crop_key, cultivar_key, density_key, depth_key, spacing_key, date_key, year):
    """creates dataframe with planting operations from management dict/dictionary

    Args:
        mgmt_dict (dict): dict containing planting mgmt operations
        crop_key (): key for which crop to plant (e.g., maize, soybean)
        cultivar_key (str): key for which cultivar/hybrid to plant
        density_key (str): key for planting density per m2
        depth_key (str): key for planting depth in mm
        spacing_key (str): key for row spacing in mm
        date_key (str): key for date to plant (eg. 15-oct, 23-sep)
        year (int): year to parse data for

    Returns:
        [pd.df]: df with planting information/management
    """
    #get all planting keys for mgmt
    crop_values = get_mgmt_values(mgmt_dict, crop_key)
    cultivar_values = get_mgmt_values(mgmt_dict, cultivar_key)
    density_values = get_mgmt_values(mgmt_dict, density_key)
    depth_values = get_mgmt_values(mgmt_dict, depth_key)
    spacing_values = get_mgmt_values(mgmt_dict, spacing_key)
    date_values = get_mgmt_values(mgmt_dict, date_key)
    #convert dates
    date_values = [get_date(date, year) for date in date_values]
    #convert to df
    planting_df = pd.DataFrame(list(zip(crop_values, cultivar_values, density_values, depth_values, spacing_values, date_values)),
    columns=['crop', 'cultivar', 'sowing_density', 'sowing_depth', 'row_spacing', 'date'])
    return planting_df

def add_planting_ops(df, mgmt_obj):
    '''
    loop through dataframe and add each planting op to Operations object
    '''
    for crop, cultivar, density, depth, spacing, date in zip(df['crop'], df['cultivar'], df['sowing_density'], df['sowing_depth'], df['row_spacing'], df['date']):
        if cultivar != None:
            mgmt_obj.add_plant_op(date, crop, density, depth, cultivar, spacing)
        else:
            print('Cultivar missing.')
    return mgmt_obj

def create_harvest_df(mgmt_dict, crop_key, date_key, year):
    """creates dataframe with harvest operations from management dict

    Args:
        mgmt_dict (dict): dict with harvest management data
        crop_key (str): key with name of crop to harvest (e.g., maize, soybean)
        date_key (str): str with date to havrest (eg. 15-oct, 23-sep)
        year (int): year to harvest on

    Returns:
        [pd.df]: pandas dataframe with each harvest operation
    """
    #get all planting keys for mgmt
    crop_values = get_mgmt_values(mgmt_dict, crop_key)
    date_values = get_mgmt_values(mgmt_dict, date_key)
    #convert dates
    date_values = [get_date(date, year) for date in date_values]
    #convert to df
    harvest_df = pd.DataFrame(list(zip(crop_values, date_values)),
    columns=['crop', 'date'])
    return harvest_df

def add_harvest_ops(df, mgmt_obj):
    '''
    loop through dataframe and add each harvest op to Operations object
    '''
    for crop, date in zip(df['crop'], df['date']):
        if crop != None:
            mgmt_obj.add_harvest_op(date, crop)
        else:
            print('Crop to harvest not specified.')
    return mgmt_obj

class OpManager:

    ###
    def __init__( self ):
        self.man_xml = Element( 'folder' )
        self.man_xml.set( 'name', 'Manager folder' )
        self.ops_xml = SubElement( self.man_xml, 'operations' )
        self.ops_xml.set( 'name', 'Operations Schedule' )

    ###
    def add_till_op( self, date, implement, f_incorp, tillage_depth):
        op_elem = init_new_op( date )
        action = ( f'SurfaceOrganicMatter tillage type = {str(implement)}, f_incorp = {f_incorp} (0-1), tillage_depth = {tillage_depth} (mm)' )
        act_elem = SubElement( op_elem, 'action' )
        act_elem.text = action
        self.ops_xml.append( op_elem )

    ###
    def add_fert_op( self, date, value, depth, type ):
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
    def add_plant_op( self, date, crop, density, depth, cultivar, spacing ):
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

        gradient_script_txt.text = """
        corn_buac   = maize.yield * 0.0159 * 1.155  ! corn yield in bu/ac @ 15.5% moisture
        soy_buac   = soybean.yield * 0.0149 * 1.13  !  soybean yield in bu/ac @ 13% moisture
        soy_mktyd  = soybean.yield * 1.13 ! soybean yield in kg/ha @ 13% moisture
        maz_mktyd  = maize.yield * 1.155 ! maize yield in kg/ha @ 15.5% moisture
        soy_ymgha = soybean.yield * 1.13 / 1000 ! soybean yield in Mg/ha @ 13% moisture
        maz_ymgha = maize.yield * 1.155 / 1000 ! maize yield in Mg/ha @ 15.5% moisture
        !bbc_gradient = -1
        !bbc_potential = {} - {}
        """.format(bbc_potential[0],bbc_potential[1])
        gradient_event = SubElement( gradient_script, 'event' ).text = 'start_of_day'

        end_script = SubElement( empty_man, 'script' )
        end_script_text = SubElement( end_script, 'text' )
        end_event = SubElement( end_script, 'event' ).text = 'end_of_day'
