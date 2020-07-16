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

'Converts multipolygon column to wkb'
def wkb_hexer(line):
    return line.wkb_hex

#TODO munging that still needs implemented
# For re-projecting input vector layer to raster projection
def reproject(vector_gpd, raster):
    proj = raster.crs.to_proj4()
    print("Original vector layer projection: ", vector_gpd.crs)
    reproj = vector_gpd.to_crs(proj)
    print("New vector layer projection (PROJ4): ", reproj.crs)
    return reproj
#stats list: ['min', 'max', 'mean', 'count', 'sum', 'std', 'median', 'majority', 'minority', 'unique', 'range']

def get_zonal_stats(vector, raster, stats):
    # Run zonal statistics, store result in geopandas dataframe
    result = zonal_stats(vector, raster, stats=stats, geojson_out=True)
    geostats = gpd.GeoDataFrame.from_features(result)
    return geostats
    # For generating raster from zonal statistics result
    
def stats_to_raster(zdf, raster, stats, out_raster, no_data='y'):
    meta = raster.meta.copy()
    out_shape = raster.shape
    transform = raster.transform
    dtype = raster.dtypes[0]
    field_list = list_columns(stats)
    index = int(input("Rasterize by which field? "))
    zone = zdf[field_list[index]]
    shapes = ((geom,value) for geom, value in zip(zdf.geometry, zone))
    burned = rasterize(shapes=shapes, fill=0, out_shape=out_shape, transform=transform)
    show(burned)
    meta.update(dtype=rio.float32, nodata=0)
    # Optional to set nodata values to min of stat
    if no_data == 'y':
        cutoff = min(zone.values)
        print("Setting nodata cutoff to: ", cutoff)
        burned[burned < cutoff] = 0 
    with rio.open(out_raster, 'w', **meta) as out:
        out.write_band(1, burned)
    print("Zonal Statistics Raster generated")


