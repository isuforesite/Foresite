#!/usr/bin/env Python

import os
import sys
import pandas as pd
import glob

import database as db

# directory containing apsim .out files
out_file_dir = 'apsim_files'
#out_file_dir = 'C:\\Users\\mnowatz\\Documents\\Dev\\aepe\\analyses\\apsim_files'

file_list = glob.glob( out_file_dir + '/*.out')

print( file_list )

# database specs
out_schema = 'sandbox'
out_table = 'test_output_table'

push_data = []
for file in file_list:
    # read file
    daily_df = pd.read_csv( file, header = 3, delim_whitespace = True )
    daily_df = daily_df.reset_index( drop = True )

    # drop units row
    daily_df = daily_df.drop( [0] )

    # cast explicit data types for processing
    daily_df = daily_df.astype( {
            'day': 'int64',
            'year': 'int64',
            'yield': 'float64',
            'biomass': 'float64',
            'fertiliser': 'float64',
            #'n2o_atm': 'float64',
            'surfaceom_c': 'float64',
            'subsurface_drain': 'float64',
            'subsurface_drain_no3': 'float64',
            'leach_no3': 'float64'
        } )

    # perform simple analytics at time scale (here we only do year)
    for year in daily_df[ 'year' ].unique():
        print( year )
        yr_df = daily_df.loc[ daily_df[ 'year' ] == year ]
        data = {
            'year': year,
            'yield': yr_df[ 'yield' ].max(),
            'biomass': yr_df[ 'biomass' ].max(),
            'fertiliser': yr_df[ 'fertiliser' ].sum(),
            #'n2o_atm': yr_df[ 'n2o_atm' ].sum(),
            'surfaceom_c_init': yr_df[ 'surfaceom_c' ].values[0],
            'surfaceom_c_end': yr_df[ 'surfaceom_c' ].values[-1],
            'subsurface_drain': yr_df[ 'subsurface_drain' ].sum(),
            'subsurface_drain_no3': yr_df[ 'subsurface_drain_no3' ].sum(),
            'leach_no3': yr_df[ 'leach_no3' ].sum(),
        }
        push_data.append( data )

print( push_data )

push_df = pd.DataFrame( push_data )

dbconn = db.ConnectToDB()
push_df.to_sql(
    name = out_table,
    con = dbconn,
    schema = out_schema,
    if_exists = 'replace',
    index = False )
