import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import database as db
import rasterio as rio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import traceback

#these are just reference for when months end and start in cleaned met csv, including shift for leap years
month_start_end = [
    {'apr_s':91, 'apr_e':120},
    {'may_s':121, 'may_e':151},
    {'jun_s':152, 'jun_e':181},
    {'jul_s':182, 'jul_e':212},
    {'aug_s':213, 'aug_e':243},
    {'sep_s':244, 'sep_e':273}]

month_start_end_leap = [
    {'apr_s':92, 'apr_e':121},
    {'may_s':122, 'may_e':152},
    {'jun_s':153, 'jun_e':182},
    {'jul_s':183, 'jul_e':213},
    {'aug_s':214, 'aug_e':244},
    {'sep_s':245, 'sep_e':274}]

def sum_met_season_col(weather_csv, year, col_index=5):
    """Sums met variable/column for a given year's growing season.
    (growing season = Apr, May, Jun, Jul, Aug, Sep)

    Args:
        weather_csv (.csv): csv file containing weather data
        year (int): year to obtain precipitation data for
        col_indedx (int): index for df column to sum (default 5 = precip)
    Returns:
        [list]: list of cumulative monthly precip
    """
    leap_years = [ yr for yr in range( 1980, 2040, 4 ) ]
    if year in leap_years:
        slices = (92, 121, 122, 152, 153, 182, 183, 213, 214, 244, 245, 274)
    else:
        slices = (91, 120, 121, 151, 152, 181, 182, 212, 213, 243, 244, 273)
    df = pd.read_csv(weather_csv)
    year_df = df.loc[df['year'] == year].reset_index(drop=True)
    #get values between desired sclices for precip column
    apr_sum = sum(year_df.iloc[slices[0]:slices[1], col_index])
    may_sum = sum(year_df.iloc[slices[2]:slices[3], col_index])
    jun_sum = sum(year_df.iloc[slices[4]:slices[5], col_index])
    jul_sum = sum(year_df.iloc[slices[6]:slices[7], col_index])
    aug_sum = sum(year_df.iloc[slices[8]:slices[9], col_index])
    sep_sum = sum(year_df.iloc[slices[10]:slices[11], col_index])
    month_sums = (apr_sum, may_sum, jun_sum, jul_sum, aug_sum, sep_sum)
    return month_sums

def create_summed_met_df (weather_csv, years, col_index):
    """Creates a new pd.df with growing season years as col and months Apr-Sep as rows
    for the summed met variable of interest (eg precip).

    Args:
        weather_csv (str): path to met file csv
        years (list): list of years to analyze
        col_index (int): index of the variable of interest (eg 5 = precip)
    Returns:
        [pd.df]: dataframe with each column being the year and rows being months Apr to Sep
    """
    df = pd.DataFrame()
    for i in years:
        met_sum_list = sum_met_season_col(weather_csv, i, col_index)
        df[f'{i}'] = met_sum_list
    return df

def chart_met_growing_seasons(df, field_name, met_var, var_units, years, plot_style, fig_width=10, fig_height=12, ylim=350, cols=2):
    """Creates bar charts of met variable for N seasons/years.

    Args:
        df (pd.df): dataframe with years as columns
        field_name (str): name of field met file is for
        met_var (str): the variable the df has data for (eg, Precipitation)
        var_units (str): the units the variable is in (eg, mm)
        years (dict): dict containing the years to chart from the df
        plot_style (str): matplotlib style to use
        fig_width (int, optional): [width of figure in inches]. Defaults to 10.
        fig_height (int, optional): [height of figure in inches]. Defaults to 12.

    Returns:
        matplotlib Figure with subplots for each year.
    """
    x = ('Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep')
    tot = len(years)
    tot_range = range(tot)
    rows = tot // cols 
    rows += tot % cols
    position = range(1,tot + 1)
    fig = plt.figure(1, figsize=(fig_width, fig_height))
    for (i, k) in zip(years, tot_range):
        y = df[f'{i}']
        # add every single subplot to the figure with a for loop
        ax = fig.add_subplot(rows,cols,position[k])
        ax.set_ylim(0,ylim)
        ax.bar(x,y)
        ax.set(title=f'{i}', ylabel=met_var)
    fig.suptitle(f'{field_name} Monthly {met_var} ({var_units})', fontsize=14, fontweight='bold', y=1.02)
    fig.tight_layout()
    plt.show()

def get_distinct(dbconn, table, id_column):
    '''
    Returns a list of all unique entries in a database column.
    Args:
        dbconn {database connection} -- connection to postgresql database
        table {str} -- table name
        id_column (str) -- column of interest.
    Returns:
        list of all unique entries in a table column
    '''
    entries = pd.read_sql(f'SELECT DISTINCT {id_column} FROM {table};', dbconn)
    entries = entries[id_column].tolist()
    return entries

def get_county(dbconn, table, fips, geom, limit=False, limit_num=100):
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
    #Get watershed as geopandas df
    if limit:
        query = f'SELECT * FROM {table} WHERE fips = \'{fips}\' LIMIT {limit_num};'
    else:
        query = f'SELECT * FROM {table} WHERE fips = \'{fips}\';'
    county_gpd = gpd.read_postgis(query, dbconn, geom_col=geom)
    return county_gpd


def get_centroid(geodf, id, geometry):
    '''
    Find and return the centroid of a geopandas geometry
    Args: 
        geodf {dataframe} -- geopandas dataframe
        id {string} -- the id of interest in the geodf (e.g., 'fips' for county column)
        geometry (string) - geopd column with geometries

    Returns:
        {np.array} -- lat and longitude of geometry
    '''
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


def get_rotation(df, crop_column):
    """
    Get the crop rotation for each clukey.
    Args:
        df {obj} -- Dataframe that contains individual clukey information.
        crop_column {str} -- Column name that contains the label for what crop is growing for a given year.
    Returns:
        Str of the rotation. e.g., 'cs' = corn-soy
    """
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


def wkb_hexer(line):
    'Converts multipolygon column in gpd to wkb'
    return line.wkb_hex

#TODO munging that still needs implemented
# For re-projecting input vector layer to raster projection
def reproject_vector(vector_gpd, raster):
    proj = raster.crs.to_proj4()
    print("Original vector layer projection: ", vector_gpd.crs)
    reproj = vector_gpd.to_crs(proj)
    print("New vector layer projection (PROJ4): ", reproj.crs)
    return reproj
#stats list: ['min', 'max', 'mean', 'count', 'sum', 'std', 'median', 'majority', 'minority', 'unique', 'range']

def reproject_raster(inpath, outpath, new_crs):
    dst_crs = new_crs # CRS for web meractor 

    with rio.open(inpath) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height
        })

        with rio.open(outpath, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rio.band(src, i),
                    destination=rio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest)

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

def get_top_ten_days(df, year, year_col, precip_col):
    """Gets top 10 precipitation events from pandas df (met csv).

    Args:
        df (pd df): Pandas df read from met csv
        year (int): Year of weather to get top events for
        year_col (str): Years column label.
        precip_col (str): Precip values column label.

    Returns:
        [pd df]: Dataframe with top 10 precip events.
    """
    df = df.loc[df[year_col] == year]
    df = df.nlargest(10, [precip_col])
    return df

def check_adjacent_days(df, day_col, precip_col):
    """Checks for any days in the top 10 precip events df
    that are adjacent to one another. eg., day 110 and day 111

    Args:
        df (pd df): Data frame of top precip events
        day_col (str): Days column label.
        precip_col ([type]): [description]

    Returns:
        [list]: List of lists with days that are adjacent to one another
        eg., [[155,156],[201,202]]
    """
    df_days = df[day_col]
    df_days = sorted(df_days)
    adjacent_days = []
    for x, y in zip(df_days[0::], df_days[1::]): 
        if y - x == 1:
            adjacent_days.append([x, y])
    return adjacent_days

def sum_adjacent_days(df, days_list, day_col, precip_col):
    """Sums precip events for any adjacent days.
    eg., day 155 had 60mm and day 156 had 40mm, returns 100mm

    Args:
        df (pd df): Data frame witht op 10 precip events.
        days_list (list): List of lists containing any adjacent days.
        day_col (str): Df column label with day integers.
        precip_col (str): Df column label with precip values

    Returns:
        [list]: Returns a list of lists containing the adjacent days and
        the summed precip for the days. eg., [[day, day, precip]]; [[155, 156, 97]]
    """
    major_precip_amounts = []
    for i in days_list:
        day1 = df.loc[df[day_col] == i[0]]
        day1_precip = day1.iloc[0][precip_col]
        day2 = df.loc[df[day_col] == i[1]]
        day2_precip = day2.iloc[0][precip_col]
        total_precip = day1_precip + day2_precip
        major_precip_amounts.append([i[0], i[1], total_precip])
    return major_precip_amounts

def get_top2_precip_events(df, days_list, day_col, precip_col):
    """Returns the values for the top 2 precip events in a df based on
    if the precip events are adjacent or not.

    Args:
        df (pd df): Data frame with top precip events.
        days_list (list): List of adjacent days to check.
        day_col (str): Label of day col in pd df.
        precip_col ([type]): Label of precip col in pd df.

    Returns:
        [list]: List of the top 2 precip events.
    """
    if len(days_list) == 1:
        print('one adjacent day of precipitation')
        event1 = sum_adjacent_days(df, days_list, day_col, precip_col)
        event1_precip = event1[0][2]
        df = df[df.day != event1[0][0]]
        df = df[df.day != event1[0][1]]
        df = df.sort_values(precip_col, ascending=False)
        event2_precip = df[precip_col].iloc[0]
        precip_events = [event1_precip, event2_precip]
    elif len(days_list) >= 2:
        print('more than one adjacent day of precipitation')
        events = sum_adjacent_days(df, days_list, day_col, precip_col)
        precip_values = []
        for i in events:
            precip_values.append(i[2])
        precip_values.sort(reverse=True)
        event1_precip = precip_values[0]
        event2_precip = precip_values[1]
        precip_events = [event1_precip, event2_precip]
    else:
        print('no adjacent days of precipitation')
        df = df.sort_values(precip_col, ascending=False)
        event1_precip = df[precip_col].iloc[0]
        event2_precip = df[precip_col].iloc[1]
        precip_events = [event1_precip, event2_precip]
    return precip_events 