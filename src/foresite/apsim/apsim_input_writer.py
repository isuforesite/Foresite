#!/usr/bin/env Python
import sys
import pathlib
import os
import traceback
import fnmatch 
import xml.etree.ElementTree
from xml.etree.ElementTree import ElementTree, Element, SubElement
import pandas as pd
import io
import json
import apsim.wrapper as apsim

###!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!###
#Set all of the json mgmt keys to be parsed over
#tillage keys
tillage_implement_key = 'tillage_implement'
tillage_depth_key = 'tillage_depth'
tillage_f_incorp_key = 'tillage_residue_incorporation'
tillage_date_key = 'tillage_timing'
#fertilizer keys
fert_amount_key = 'kg_n_ha'
fert_date_key = 'fertilize_n_on'
fert_formula_key = 'n_fertilizer'
fert_depth_key = 'fert_depth'
#planting keys
plant_crop_key = 'sow_crop'
cultivar_key = 'cultivar'
planting_date_key = 'planting_date'
sowing_density_key = 'sowing_density'
sowing_depth_key = 'sowing_depth'
row_spacing_key = 'row_spacing'
#harvest keys
harvest_crop_key = 'harvest'
harvest_date_key = 'harvest_date'

def add_crop_ini(crop, crop_xml=None):
    ini_man = SubElement( crop, 'ini')
    filename = SubElement(ini_man, 'filename')
    filename.set('input', 'yes')
    if crop_xml:
        filename.text = crop_xml
    else:
        pass
###
def get_date( date_str, year ):
    """Formats mgmt json date value to dd/mm/yyyy

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


def get_rot_year_one(years):
    return years[::2]

def get_rot_year_two(years):
    return years[1::2]

def create_mukey_runs(soils_list, dbconn, rotation, met_name, field_name='field', tar_folder=None, start_year=2015, end_year=2018, sfc_mgmt=None, cfs_mgmt=None, cc_mgmt=None, swim = False, saxton=False, maize_xml=None, soy_xml=None):
    """Creates APSIM simulation files for desired list of SSURGO mukeys.

    Args:
        tar_folder (str): Target folder to write files to.
        soils_list (list): list of each SSURGO mukey to create APSIM file for
        dbconn (obj): Connections to PostgreSQL server with SSURGO data
        rotation (str): which rotation to create the file for. Currently supports corn following soy (CFS),
        soy following corn (SFC), and continuous corn (CC).
        met_name (str): Met filename
        field_name (str, optional): Name of field files are being created for. Defaults to 'field'.
        start_year (int, optional): Starting year for simulations. Defaults to 2015. NOTE: end_year - start_year must be divisble by 3.
        end_year (int, optional): Ending year for simulations. Defaults to 2018. NOTE: end_year - start_year must be divisble by 3.
        sfc_mgmt (dict, optional): Dictionary (likely a loaded json file) containing management practices for field. Defaults to None.
        cfs_mgmt (dict, optional): Dictionary (likely a loaded json file) containing management practices for field. Defaults to None.
        cc_mgmt (dict, optional): Dictionary (likely a loaded json file) containing management practices for field]. Defaults to None.
        swim (bool, optional): Create water table using the APSIM SWIM module. Defaults to False.
        saxton (bool, optional): Create soil profiles using Saxton-Rawls parameters. Defaults to False.
        maize_xml (str, optional): Path to custom maize XML file. Should be in subfolder of current directory.
        soy_xml (str, optional): Path to custom soybean XML file. Should be in subfolder of current directory.
    Yields:
        None: Creates .apsim files for each SSURGO soil mukey, management, and weather.
    """
    if tar_folder == None:
        tar_folder = os.getcwd()
    runs_folder_path = f'{tar_folder}/apsim_files/{field_name}/{end_year}/{rotation}/'
    if not os.path.exists(runs_folder_path):
        os.makedirs(runs_folder_path)
    if os.path.exists(runs_folder_path):
        num_files_removed = 0
        for filename in os.listdir(runs_folder_path):
            for pattern in ['*.apsim', '*.tmp', '*.out',
                            '*.sim','*.sum']:
                if fnmatch.fnmatch(filename, pattern):
                    os.remove(runs_folder_path + filename)
                    num_files_removed += 1
        print(f"Removed {num_files_removed} old files.")
    start_date = f'01/01/{start_year}'
    end_date = f'31/12/{end_year}'
    #save rotation for clukey to crops list
    #loop through field keys e.g., clukeys
    met_folder_path = f'{tar_folder}/apsim_files/{field_name}/{end_year}/{rotation}/met_files'
    if not os.path.exists(met_folder_path):
        os.makedirs(met_folder_path)
    met_path = f"met_files/{met_name}"
    total_sims = len(soils_list)
    sim_count = 0
    for i in soils_list:
        try:
            soil_id = i
            soil_query = '''select * from api.get_soil_properties( array[{}]::text[] )'''.format( i )
            soil_df = pd.read_sql( soil_query, dbconn )
            if soil_df.empty:
                print(f'Soil {i} not found')
                continue
            #soil_row = soils_df.loc[soils_df[f'{soil_key}'] == i]
            #initialize .apsim xml
            apsim_xml = Element( 'folder' )
            apsim_xml.set( 'version', '36' )
            apsim_xml.set( 'creator', 'C-CHANGE Foresite' )
            apsim_xml.set( 'name', field_name )
            sim = SubElement( apsim_xml, 'simulation' )
            sim.set( 'name', f'name_{field_name}_mukey_{soil_id}_rot_{rotation}_sim' )
            
            #set met file
            metfile = SubElement( sim, 'metfile' )
            metfile.set( 'name', met_name )
            filename = SubElement( metfile, 'filename' )
            filename.set( 'name', 'filename' )
            filename.set( 'input', 'yes' )
            filename.text = met_path

            #set clock
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

            # add soil xml
            soil = apsim.Soil( soil_df, swim, saxton )
            area.append( soil.soil_xml() )
            ### surface om
            if rotation == 'cfs':
                surfom_xml = apsim.init_surfaceOM( 'soybean', 'soybean', 1250, 27, 0.0 )
            else:
                surfom_xml = apsim.init_surfaceOM( 'maize', 'maize', 3500, 65, 0.0 )
            area.append( surfom_xml )
            ### fertilizer
            fert_xml = SubElement( area, 'fertiliser' )
            ### crops
            curr_dir = os.getcwd()
            crop_xml = SubElement( area, 'maize' )
            maize_path = os.path.join(curr_dir, maize_xml)
            add_crop_ini(crop_xml, maize_path)
            crop_xml = SubElement( area, 'soybean' )
            soy_path = os.path.join(curr_dir, soy_xml)
            add_crop_ini(crop_xml, soy_path)
            # crop_xml = SubElement( area, 'maize' )
            # add_crop_ini(crop_xml, maize_xml)
            # crop_xml = SubElement( area, 'soybean' )
            # add_crop_ini(crop_xml, soy_xml)
            #crop_xml = SubElement( area, 'wheat' )

            ### output file
            outvars = [
                'title',
                'dd/mm/yyyy as date',
                'day',
                'year',
                'soybean.yield as soybean_yield',
                'maize.yield as maize_yield',
                'soy_mktyd',
                'maz_mktyd',
                'soy_ymgha',
                'maz_ymgha',
                'soybean.biomass as soybean_biomass',
                'maize.biomass as maize_biomass',
                'corn_buac',
                'soy_buac',
                'fertiliser',
                'surfaceom_c',
                'leach_no3',
                'Rain',
                'drain'
                ]
            swim_outvars = ['subsurface_drain', 'subsurface_drain_no3']
            if swim == True:
                outvars = outvars + swim_outvars
            output_xml = apsim.set_output_variables( f'name_{field_name}_mukey_{soil_id}_rot_{rotation}_sim.out', outvars )
            area.append( output_xml )
            graph_no3 = [
                'Cumulative subsurface_drain',
                'Cumulative subsurface_drain_no3',
                'Cumulative leach_no3',
                'Cumulative Rain',
                'Cumulative drain'
            ]
            graph_yield = [
                'soybean_yield',
                'maize_yield',
                'soybean_biomass',
                'maize_biomass',
                'soy_buac',
                'corn_buac',
                'soy_mktyd',
                'maz_mktyd',
                'soy_ymgha',
                'maz_ymgha'
            ]
            graph_all = [
                'soybean_yield',
                'maize_yield',
                'soybean_biomass',
                'maize_biomass',
                'corn_buac',
                'soy_buac',
                'soy_mktyd',
                'maz_mktyd',
                'soy_ymgha',
                'maz_ymgha',
                'fertiliser',
                'surfaceom_c',
                'subsurface_drain',
                'subsurface_drain_no3',
                'leach_no3',
                'Rain',
                'drain'
            ]

            output_xml.append( apsim.add_xy_graph( 'Date', graph_no3, 'no3' ) )
            output_xml.append( apsim.add_xy_graph( 'Date', graph_yield, 'yield' ) )
            output_xml.append( apsim.add_xy_graph( 'Date', graph_all, 'all outputs' ) )

            op_man = apsim.OpManager()
            op_man.add_empty_manager()
            #get range of years for runs and keep each management year as a list
            num_years = end_year - start_year
            years_range = list(range(start_year, end_year+1))
            rot_years_one = get_rot_year_one(years_range)
            rot_years_two = get_rot_year_two(years_range)
            rot_every_year = years_range[::1]
            if num_years % 3 == 0:
                if rotation == 'cfs':
                    for i in rot_years_one:
                        #--- add ops for soybean in year 1 ---#
                        #add tillage operations
                        sfc_tillage_df = apsim.man.create_tillage_df(sfc_mgmt, tillage_implement_key, tillage_depth_key, tillage_f_incorp_key, tillage_date_key, i)
                        apsim.man.add_tillage_ops(sfc_tillage_df, op_man)
                        #add planting operations
                        sfc_planting_df = apsim.man.create_planting_df(sfc_mgmt, plant_crop_key, cultivar_key, sowing_density_key, sowing_depth_key, row_spacing_key, planting_date_key, i)
                        apsim.man.add_planting_ops(sfc_planting_df, op_man)
                        #add fert operations
                        sfc_fert_df = apsim.man.create_fert_df(sfc_mgmt, fert_amount_key, fert_formula_key, fert_depth_key, fert_date_key, i)
                        apsim.man.add_fert_ops(sfc_fert_df, op_man)
                        #add harvest operations
                        sfc_harvest_df = apsim.man.create_harvest_df(sfc_mgmt, harvest_crop_key, harvest_date_key, i)
                        apsim.man.add_harvest_ops(sfc_harvest_df, op_man)
                    for i in rot_years_two:
                        #--- add ops for corn in year 2 ---#
                        #add tillage operations
                        cfs_tillage_df = apsim.man.create_tillage_df(cfs_mgmt, tillage_implement_key, tillage_depth_key, tillage_f_incorp_key, tillage_date_key, i)
                        apsim.man.add_tillage_ops(cfs_tillage_df, op_man)
                        #add planting operations
                        cfs_planting_df = apsim.man.create_planting_df(cfs_mgmt, plant_crop_key, cultivar_key, sowing_density_key, sowing_depth_key, row_spacing_key, planting_date_key, i)
                        apsim.man.add_planting_ops(cfs_planting_df, op_man)
                        #add fert operations
                        cfs_fert_df = apsim.man.create_fert_df(cfs_mgmt, fert_amount_key, fert_formula_key, fert_depth_key, fert_date_key, i)
                        apsim.man.add_fert_ops(cfs_fert_df, op_man)
                        #add harvest operations
                        cfs_harvest_df = apsim.man.create_harvest_df(cfs_mgmt, harvest_crop_key, harvest_date_key, i)
                        apsim.man.add_harvest_ops(cfs_harvest_df, op_man)
                elif rotation == 'sfc':
                    for i in rot_years_one:
                        #--- add ops for corn in year 1 ---#
                        #add tillage operations
                        cfs_tillage_df = apsim.man.create_tillage_df(cfs_mgmt, tillage_implement_key, tillage_depth_key, tillage_f_incorp_key, tillage_date_key, i)
                        apsim.man.add_tillage_ops(cfs_tillage_df, op_man)
                        #add planting operations
                        cfs_planting_df = apsim.man.create_planting_df(cfs_mgmt, plant_crop_key, cultivar_key, sowing_density_key, sowing_depth_key, row_spacing_key, planting_date_key, i)
                        apsim.man.add_planting_ops(cfs_planting_df, op_man)
                        #add fert operations
                        cfs_fert_df = apsim.man.create_fert_df(cfs_mgmt, fert_amount_key, fert_formula_key, fert_depth_key, fert_date_key, i)
                        apsim.man.add_fert_ops(cfs_fert_df, op_man)
                        #add harvest operations
                        cfs_harvest_df = apsim.man.create_harvest_df(cfs_mgmt, harvest_crop_key, harvest_date_key, i)
                        apsim.man.add_harvest_ops(cfs_harvest_df, op_man)
                    for i in rot_years_two:
                        #--- add ops for soybeans in year 2 ---#
                        #add tillage operations
                        sfc_tillage_df = apsim.man.create_tillage_df(sfc_mgmt, tillage_implement_key, tillage_depth_key, tillage_f_incorp_key, tillage_date_key, i)
                        apsim.man.add_tillage_ops(sfc_tillage_df, op_man)
                        #add planting operations
                        sfc_planting_df = apsim.man.create_planting_df(sfc_mgmt, plant_crop_key, cultivar_key, sowing_density_key, sowing_depth_key, row_spacing_key, planting_date_key, i)
                        apsim.man.add_planting_ops(sfc_planting_df, op_man)
                        #add fert operations
                        sfc_fert_df = apsim.man.create_fert_df(sfc_mgmt, fert_amount_key, fert_formula_key, fert_depth_key, fert_date_key, i)
                        apsim.man.add_fert_ops(sfc_fert_df, op_man)
                        #add harvest operations
                        sfc_harvest_df = apsim.man.create_harvest_df(sfc_mgmt, harvest_crop_key, harvest_date_key, i)
                        apsim.man.add_harvest_ops(sfc_harvest_df, op_man)
                elif rotation == 'cc':
                    for i in rot_every_year:
                        #--- add cc ops every year---#
                        #add tillage operations
                        cc_tillage_df = apsim.man.create_tillage_df(cc_mgmt, tillage_implement_key, tillage_depth_key, tillage_f_incorp_key, tillage_date_key, i)
                        apsim.man.add_tillage_ops(cc_tillage_df, op_man)
                        #add planting operations
                        cc_planting_df = apsim.man.create_planting_df(cc_mgmt, plant_crop_key, cultivar_key, sowing_density_key, sowing_depth_key, row_spacing_key, planting_date_key, i)
                        apsim.man.add_planting_ops(cc_planting_df, op_man)
                        #add fert operations
                        cc_fert_df = apsim.man.create_fert_df(cc_mgmt, fert_amount_key, fert_formula_key, fert_depth_key, fert_date_key, i)
                        apsim.man.add_fert_ops(cc_fert_df, op_man)
                        #add harvest operations
                        cc_harvest_df = apsim.man.create_harvest_df(cc_mgmt, harvest_crop_key, harvest_date_key, i)
                        apsim.man.add_harvest_ops(cc_harvest_df, op_man)
                else:
                    continue
            else:
                print("The total number of simulation years should be divisble by 3.")
                break

            area.append( op_man.man_xml )
            outfile = f'{runs_folder_path}/{field_name}_{soil_id}_{rotation}.apsim'
            ### management data
            tree = ElementTree()
            tree._setroot( apsim_xml )
            tree.write( outfile )
            sim_count += 1
            if (sim_count % 20 == 0):
                print(f'Finished with {sim_count} files.')
            if sim_count == total_sims:
                print(f'Finished! All files created for {field_name}, {rotation}, {end_year}!')
                print(' ')
        except:
            print(f'File creation failed for {field_name}, {rotation}, {end_year}, mukey {soil_id}')
            traceback.print_exc()
            sim_count +=1
            continue

if __name__ == "__main__":
    pass
