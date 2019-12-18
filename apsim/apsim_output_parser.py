#!/usr/bin/env Python

import os
import sys
import pandas as pd
import glob

import database as db

# directory containing apsim .out files
out_file_dir = sys.argv[1]

file_list = glob.glob( out_file_dir + '/*.out')

print( file_list )

# database table name
out_table = 'test_output_table'

for file in file_list:
    # read file
    daily_df = pd.read_csv( file, header = 3, delim_whitespace = True )
    daily_df = daily_df.reset_index( drop = True )

    #group data by year
    data = []
    for year in data[ 'year' ].unique():
        yr_df = data.loc[ data[ 'year' ] == year ]

        print( year )

# drop units
data = data.drop( [0] )

dbconn = db.ConnectToDB()

data.to_sql(
    name = out_table,
    con = dbconn,
    schema = 'sandbox',
    if_exists = 'replace',
    index = False )
