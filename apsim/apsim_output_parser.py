#!/usr/bin/env Python

import os
import sys
import pandas as pd
import numpy as np
import glob
import re
#import apsim.database as db

def parse_all_output_county(out_file_dir, year=2019): #, db_path, db_schema, db_table
    """Parses all .out files for a county, gets daily output and returns df for the given year.
    Arguments:
        out_file_dir {str} -- path to folder that contains .out files
        year (int) -- the targeted year of simulation data
    Returns:
        [df object] -- dataframe with daily data for each .out file
    """
    #dbconn = db.connect_to_db(db_path)
    file_list = glob.glob( out_file_dir + '/*.out')
    push_df = pd.DataFrame()
    for file in file_list:
        # read file
        daily_df = pd.read_csv( file, header = 3, delim_whitespace = True )
        daily_df = daily_df.drop( [0] )
        #get the title with mukey, clukey, county info and extract via regex
        df_header = daily_df['title'][1]
        county_pattern = "County_(.*?)_fips"
        county = str(re.search(county_pattern, df_header).group(1))
        mukey_pattern = "mukey_(.*?)_rot"
        mukey = str(re.search(mukey_pattern, df_header).group(1))
        fips_pattern = "fips_(.*?)_mukey"
        fips = re.search(fips_pattern, df_header).group(1)
        rot_pattern = "rot_(.*?)_sim"
        rotation = str(re.search(rot_pattern, df_header).group(1))
        #insert new columns with mukey county fip rot
        daily_df.insert(1, 'county', county)
        daily_df.insert(2, 'fips', fips)
        daily_df.insert(3, 'mukey', mukey)
        daily_df.insert(4, 'rotation', rotation)
        daily_df = daily_df.reset_index( drop = True )
        #replace all ? with NaN
        daily_df = daily_df.replace("?", np.nan)
        daily_df['date'] = pd.to_datetime(daily_df['date']).dt.date

        # cast explicit data types for processing
        daily_df = daily_df.astype( {
            'county' : 'string',
            'fips' : 'string',
            'mukey' : 'string',
            'rotation' : 'string',
            'day': 'int64',
            'year': 'int64',
            'soybean_yield': 'float64',
            'maize_yield': 'float64',
            'soybean_biomass': 'float64',
            'maize_biomass': 'float64',
            'fertiliser': 'float64',
            #'n2o_atm': 'float64',
            'surfaceom_c': 'float64',
            'subsurface_drain': 'float64',
            'subsurface_drain_no3': 'float64',
            'leach_no3': 'float64',
            'corn_buac' : 'float64',
            'soy_buac' : 'float64'
            } )
        df_year = daily_df.loc[daily_df['year'] == year].reset_index(drop=True)
        push_df = push_df.append(df_year)
    return push_df
    # push_df.to_sql(
    #     name = db_table,
    #     con = dbconn,
    #     schema = db_schema,
    #     if_exists = 'replace',
    #     index = False )

def parse_summary_output_county(out_file_dir, year=2019): #, db_path, db_schema, db_table
    """Parses all .out files for a county, does some summary stats, and returns df for last year
    Arguments:
        out_file_dir {str} -- path to folder that contains .out files
        year (int) -- the targeted year of simulation data
    Returns:
        [object] -- df with summary data for each .out file
    """
    #dbconn = db.connect_to_db(db_path)
    file_list = glob.glob( out_file_dir + '/*.out')
    push_data = []
    for file in file_list:
        # read file
        daily_df = pd.read_csv( file, header = 3, delim_whitespace = True )
        daily_df = daily_df.drop( [0] )
        #get the header row with mukey, clukey, county info and extract via regex
        df_header = daily_df['title'][1]
        county_pattern = "County_(.*?)_fips"
        county = str(re.search(county_pattern, df_header).group(1))
        mukey_pattern = "mukey_(.*?)_rot"
        mukey = str(re.search(mukey_pattern, df_header).group(1))
        fips_pattern = "fips_(.*?)_mukey"
        fips = re.search(fips_pattern, df_header).group(1)
        rot_pattern = "rot_(.*?)_sim"
        rotation = re.search(rot_pattern, df_header).group(1)
        #insert new columns with mukey and county fip
        daily_df.insert(1, 'county', county)
        daily_df.insert(2, 'fips', fips)
        daily_df.insert(3, 'mukey', mukey)
        daily_df.insert(4, 'rotation', rotation)
        daily_df = daily_df.reset_index( drop = True )
        #drop first row that has unit names
        #replace all ? with NaN
        daily_df = daily_df.replace("?", np.nan)
        daily_df['date'] = pd.to_datetime(daily_df['date']).dt.date

        # cast explicit data types for processing
        daily_df = daily_df.astype( {
            'title' : 'string',
            'county' : 'string',
            'fips' : 'string',
            'mukey' : 'string',
            'rotation' : 'string',
            'day': 'int64',
            'year': 'int64',
            'soybean_yield': 'float64',
            'maize_yield': 'float64',
            'soybean_biomass': 'float64',
            'maize_biomass': 'float64',
            'fertiliser': 'float64',
            #'n2o_atm': 'float64',
            'surfaceom_c': 'float64',
            'subsurface_drain': 'float64',
            'subsurface_drain_no3': 'float64',
            'leach_no3': 'float64',
            'corn_buac' : 'float64',
            'soy_buac' : 'float64'
            } )
        df_year = daily_df.loc[daily_df['year'] == year].reset_index(drop=True)
        # perform simple analytics at time scale (here we only do year)
        data = {
            'title' : df_year['title'][1],
            'county' : county,
            'fips': fips,
            'mukey' : mukey,
            'rotation' : rotation,
            'year': year,
            'soybean_yield': df_year[ 'soybean_yield' ].max(),
            'maize_yield': df_year[ 'maize_yield' ].max(),
            'corn_buac' : df_year[ 'corn_buac' ].max(),
            'soy_buac' : df_year[ 'soy_buac' ].max(),
            'soybean_biomass': df_year[ 'soybean_biomass' ].max(),
            'maize_biomass': df_year[ 'maize_biomass' ].max(),
            'fertiliser': df_year[ 'fertiliser' ].sum(),
            #'n2o_atm': df_year[ 'n2o_atm' ].sum(),
            'surfaceom_c_init': df_year[ 'surfaceom_c' ].values[0],
            'surfaceom_c_end': df_year[ 'surfaceom_c' ].values[-1],
            #'subsurface_drain': df_year[ 'subsurface_drain' ].sum(),
            #'subsurface_drain_no3': df_year[ 'subsurface_drain_no3' ].sum(),
            'leach_no3': df_year[ 'leach_no3' ].sum()
        }
        push_data.append(data)
    push_df = pd.DataFrame().append(push_data, ignore_index=True)
    return push_df
    # push_df.to_sql(
    #     name = db_table,
    #     con = dbconn,
    #     schema = db_schema,
    #     if_exists = 'replace',
    #     index = False )

def parse_all_output_field(out_file_dir, year=2019): #, db_path, db_schema, db_table
    """Parses all .out files for a county, gets daily output and returns df for the given year.
    Arguments:
        out_file_dir {str} -- path to folder that contains .out files
        year (int) -- the targeted year of simulation data
    Returns:
        [df object] -- dataframe with daily data for each .out file
    """
    #dbconn = db.connect_to_db(db_path)
    file_list = glob.glob( out_file_dir + '/*.out')
    push_df = pd.DataFrame()
    for file in file_list:
        # read file
        daily_df = pd.read_csv( file, header = 3, delim_whitespace = True )
        daily_df = daily_df.drop( [0] )
        #get field name, mukey, and rotation with regex
        df_header = daily_df['title'][1]
        name_pattern = "name_(.*?)_mukey"
        field = str(re.search(name_pattern, df_header).group(1))
        mukey_pattern = "mukey_(.*?)_rot"
        mukey = str(re.search(mukey_pattern, df_header).group(1))
        rot_pattern = "rot_(.*?)_sim"
        rotation = str(re.search(rot_pattern, df_header).group(1))
        #insert new columns with mukey county fip rot
        daily_df.insert(1, 'field', field)
        daily_df.insert(2, 'mukey', mukey)
        daily_df.insert(3, 'rotation', rotation)
        daily_df = daily_df.reset_index( drop = True )
        #replace all ? with NaN
        daily_df = daily_df.replace("?", np.nan)
        daily_df['date'] = pd.to_datetime(daily_df['date']).dt.date

        # cast explicit data types for processing
        daily_df = daily_df.astype( {
            'field' : 'string',
            'mukey' : 'string',
            'rotation' : 'string',
            'day': 'int64',
            'year': 'int64',
            'soybean_yield': 'float64',
            'maize_yield': 'float64',
            'soybean_biomass': 'float64',
            'maize_biomass': 'float64',
            'fertiliser': 'float64',
            #'n2o_atm': 'float64',
            'surfaceom_c': 'float64',
            'subsurface_drain': 'float64',
            'subsurface_drain_no3': 'float64',
            'leach_no3': 'float64',
            'corn_buac' : 'float64',
            'soy_buac' : 'float64'
            } )
        df_year = daily_df.loc[daily_df['year'] == year].reset_index(drop=True)
        push_df = push_df.append(df_year)
    return push_df
    # push_df.to_sql(
    #     name = db_table,
    #     con = dbconn,
    #     schema = db_schema,
    #     if_exists = 'replace',
    #     index = False )

def parse_summary_output_field(out_file_dir, year=2019): #, db_path, db_schema, db_table
    """Parses all .out files for a given field, does some summary stats, and returns df for last year
    Arguments:
        out_file_dir {str} -- path to folder that contains .out files
        year (int) -- the targeted year of simulation data
    Returns:
        [object] -- df with summary data for each .out file
    """
    #dbconn = db.connect_to_db(db_path)
    file_list = glob.glob( out_file_dir + '/*.out')
    push_data = []
    for file in file_list:
        # read file
        daily_df = pd.read_csv( file, header = 3, delim_whitespace = True )
        daily_df = daily_df.drop( [0] )
        #get field name, mukey, and rotation with regex
        df_header = daily_df['title'][1]
        name_pattern = "name_(.*?)_mukey"
        field = str(re.search(name_pattern, df_header).group(1))
        mukey_pattern = "mukey_(.*?)_rot"
        mukey = str(re.search(mukey_pattern, df_header).group(1))
        rot_pattern = "rot_(.*?)_sim"
        rotation = str(re.search(rot_pattern, df_header).group(1))
        #insert new columns with field name, mukey, rot
        daily_df.insert(1, 'field', field)
        daily_df.insert(2, 'mukey', mukey)
        daily_df.insert(3, 'rotation', rotation)
        daily_df = daily_df.reset_index( drop = True )
        #drop first row that has unit names
        #replace all ? with NaN
        daily_df = daily_df.replace("?", np.nan)
        daily_df['date'] = pd.to_datetime(daily_df['date']).dt.date

        # cast explicit data types for processing
        daily_df = daily_df.astype( {
            'title' : 'string',
            'field' : 'string',
            'mukey' : 'string',
            'rotation' : 'string',
            'day': 'int64',
            'year': 'int64',
            'soybean_yield': 'float64',
            'maize_yield': 'float64',
            'soybean_biomass': 'float64',
            'maize_biomass': 'float64',
            'fertiliser': 'float64',
            #'n2o_atm': 'float64',
            'surfaceom_c': 'float64',
            'subsurface_drain': 'float64',
            'subsurface_drain_no3': 'float64',
            'leach_no3': 'float64',
            'corn_buac' : 'float64',
            'soy_buac' : 'float64'
            } )
        df_year = daily_df.loc[daily_df['year'] == year].reset_index(drop=True)
        # perform simple analytics at time scale (here we only do year)
        data = {
            'title' : df_year['title'][1],
            'field' : field,
            'mukey' : mukey,
            'rotation' : rotation,
            'year': year,
            'soybean_yield': df_year[ 'soybean_yield' ].max(),
            'maize_yield': df_year[ 'maize_yield' ].max(),
            'corn_buac' : df_year[ 'corn_buac' ].max(),
            'soy_buac' : df_year[ 'soy_buac' ].max(),
            'soybean_biomass': df_year[ 'soybean_biomass' ].max(),
            'maize_biomass': df_year[ 'maize_biomass' ].max(),
            'fertiliser': df_year[ 'fertiliser' ].sum(),
            #'n2o_atm': df_year[ 'n2o_atm' ].sum(),
            'surfaceom_c_init': df_year[ 'surfaceom_c' ].values[0],
            'surfaceom_c_end': df_year[ 'surfaceom_c' ].values[-1],
            #'subsurface_drain': df_year[ 'subsurface_drain' ].sum(),
            #'subsurface_drain_no3': df_year[ 'subsurface_drain_no3' ].sum(),
            'leach_no3': df_year[ 'leach_no3' ].sum()
        }
        push_data.append(data)
    push_df = pd.DataFrame().append(push_data, ignore_index=True)
    return push_df
    # push_df.to_sql(
    #     name = db_table,
    #     con = dbconn,
    #     schema = db_schema,
    #     if_exists = 'replace',
    #     index = False )

if __name__ == "__main__":
    pass
    # out_file_dir = 'C:\\Users\\mnowatz\\Documents\\Dev\\aepe\\analyses\\apsim_files\\Greene'
    # db_path = 'database.ini'
    # db_schema = 'raccoon'
    # db_table = 'apsim_output_summary' 
    # parse_summary_output(out_file_dir, db_path, db_schema, db_table)
    # db_table = 'apsim_output_all' 
    # parse_all_output(out_file_dir, db_path, db_schema, db_table)