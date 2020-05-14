import geopandas as gpd
import pandas as pd
import numpy as np
import database as db
import traceback

'''
Returns a list of all unique entries in a database column.
Args:
    dbconn {database connection} -- connection to postgresql database
    table {str} -- table name
    id_column (str) -- column of interest.
Returns:
    list of all unique entries in a table column
'''
def get_distinct(dbconn, table, id_column):
    entries = pd.read_sql(f'SELECT DISTINCT {id_column} FROM {table};', dbconn)
    entries = entries[id_column].tolist()
    return entries

'''
Get info for a county of interest from a geopandas df
Args:
    dbconn {database connection} -- connection to postgresql database
    table {str} -- name of geopd table
    fips {str} -- fips id of the desired county eg. 'IA021'
    geom {str} -- column name that contains shape geometry
Returns:
    geopandas dataframe with county info
'''
def get_county(dbconn, table, fips, geom, limit=False, limit_num=100):
    #Get watershed as geopandas df
    if limit:
        query = f'SELECT * FROM {table} WHERE fips = \'{fips}\' LIMIT {limit_num};'
    else:
        query = f'SELECT * FROM {table} WHERE fips = \'{fips}\';'
    county_gpd = gpd.read_postgis(query, dbconn, geom_col=geom)
    return county_gpd

'''
Find and return the centroid of a geopandas geometry
Args: 
    geodf {dataframe} -- geopandas dataframe
    id {string} -- the id of interest in the geodf (e.g., 'fips' for county column)
    geometry (string) - geopd column with geometries

Returns:
    {np.array} -- lat and longitude of geometry
'''
def get_centroid(geodf, id, geometry):
    #get the geometry of interest by id - 'fips' for a county
    geom = geodf[[id, geometry]]
    #dissolve geometries to make one big geometry
    dissolved_geom = geom.dissolve(by=id)
    #find the centroid of the dissolved geometry and return its long, lat
    centroid = dissolved_geom[geometry].centroid
    coords = np.vstack([centroid.x, centroid.y]).T
    #change to array and lat, long
    centroid_coords = np.array([coords[0][1], coords[0][0]])
    return centroid_coords

"""
Get the crop rotation for each clukey.
Args:
    df {obj} -- Dataframe that contains individual clukey information.
    crop_column {str} -- Column name that contains the label for what crop is growing for a given year.
Returns:
    Str of the rotation. e.g., 'cs' = corn-soy
"""
def get_rotation(df, crop_column):
    #save rotation for clukey to crops list
    try:
        df = df.sort_values(by=['years'], ascending=True)
        years = list(df['years'])
        last_year = years[-1]
        last_crop = df.loc[df['years'] == last_year, 'crop'].item()
        crops = []
        for i in df.index:
            val = df.loc[i, crop_column]
            if val == 'Corn' or val == 'Soybean':
                crops.append(val)
            else:
                crops.append('other')
        #evaluate crops list and return a rotation
        if all(x in crops for x in ['Corn', 'Soybean']) and last_crop == 'Soybean':
            rotation = 'sfc'
        elif all(x in crops for x in ['Corn', 'Soybean']) and last_crop == 'Corn':
            rotation = 'cfs'
        elif all(x in crops for x in ['Corn']):
            rotation = 'cc'
        else:
            rotation = 'other'
        return rotation
    except Exception:
        print('Something went wrong')
        traceback.print_exc()