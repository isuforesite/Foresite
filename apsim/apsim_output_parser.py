#!/usr/bin/env Python

import os
import sys
#sys.path.append("C:\\Users\\mnowatz\\Documents\\Dev\\aepe")
import pandas as pd
import numpy as np
import glob
import re
import math
import apsim.database as db

def parse_all_output(out_file_dir, db_path, db_schema, db_table):
    dbconn = db.connect_to_db(db_path)
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
        mukey = int(re.search(mukey_pattern, df_header).group(1))
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
            'mukey' : 'int64',
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
        last_year = daily_df['year'].unique()[-1]
        df_year = daily_df.loc[daily_df['year'] == last_year].reset_index(drop=True)
        push_df = push_df.append(df_year)

    push_df.to_sql(
        name = db_table,
        con = dbconn,
        schema = db_schema,
        if_exists = 'replace',
        index = False )

def parse_summary_output(out_file_dir, db_path, db_schema, db_table):
    dbconn = db.connect_to_db(db_path)
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
        mukey = int(re.search(mukey_pattern, df_header).group(1))
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
            'mukey' : 'int64',
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
        last_year = daily_df['year'].unique()[-1]
        df_year = daily_df.loc[daily_df['year'] == last_year].reset_index(drop=True)
        # perform simple analytics at time scale (here we only do year)
        data = {
            'title' : df_year['title'][1],
            'county' : county,
            'fips': fips,
            'mukey' : mukey,
            'rotation' : rotation,
            'year': last_year,
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

    push_df.to_sql(
        name = db_table,
        con = dbconn,
        schema = db_schema,
        if_exists = 'replace',
        index = False )

if __name__ == "__main__":
    out_file_dir = 'C:\\Users\\mnowatz\\Documents\\Dev\\aepe\\analyses\\apsim_files\\Greene'
    db_path = 'database.ini'
    db_schema = 'sandbox'
    db_table = 'apsim_output_summary' 
    parse_summary_output(out_file_dir, db_path, db_schema, db_table)
    db_table = 'apsim_output_all' 
    parse_all_output(out_file_dir, db_path, db_schema, db_table)