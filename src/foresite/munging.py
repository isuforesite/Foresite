import csv
import fnmatch
import json
import os
import shutil
import sys
import traceback
from datetime import datetime
from glob import glob
from zipfile import ZipFile

import apsim.run_apsim
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio as rio
import rasterstats as rs
from apsim.apsim_input_writer import create_mukey_runs
from apsim.apsim_output_parser import parse_summary_output_field
from rasterio.mask import mask
from rasterio.warp import Resampling, calculate_default_transform, reproject

###---------------------------------------------------------###
###                     Helper functions                    ###
###---------------------------------------------------------###


def get_management_file(in_path, mgmt_file):
    full_path = os.path.join(in_path, mgmt_file)
    mgmt_ops = json.loads(open(full_path, "r").read())
    return mgmt_ops


def copy_met_file(src, dst):
    if not os.path.exists(dst):
        print("Target directory does not exist, creating directory now.")
        os.mkdir(dst)
    shutil.copy(src, dst)


def create_apsim_files_from_dict(
    dbconn,
    runs_dict,
    met_folder,
    swim=False,
    saxton=False,
    maize_xml=None,
    soy_xml=None,
    tar_folder=None,
):
    for i in runs_dict:
        rotation = runs_dict[i][0]
        runs_folder = runs_dict[i][1]
        field_prefix = runs_dict[i][2]
        met_file = runs_dict[i][3]
        end_year = runs_dict[i][4]
        mgmt_folder = os.path.join(tar_folder, runs_dict[i][7])
        start_year = end_year - 3
        prior_year = end_year - 1
        ssurgo_file = os.path.join(tar_folder, "ssurgo", runs_dict[i][5])
        ssurgo_gdf = gpd.read_file(ssurgo_file)
        mukeys = list(np.unique(ssurgo_gdf["mukey"]))
        out_path = os.path.join(
            tar_folder,
            "apsim_files",
            runs_folder,
            str(end_year),
            rotation,
            "met_files",
        )
        if not os.path.exists(out_path):
            os.makedirs(out_path)
        if rotation == "cfs":
            corn_mgmt = get_management_file(mgmt_folder, f"{field_prefix}_{rotation}_{end_year}.json")
            soy_mgmt = get_management_file(mgmt_folder, f"{field_prefix}_sfc_{prior_year}.json")
            # print(json.dumps(corn_mgmt, indent=1))
            # print(json.dumps(soy_mgmt, indent=1))
        elif rotation == "sfc":
            soy_mgmt = get_management_file(mgmt_folder, f"{field_prefix}_{rotation}_{end_year}.json")
            corn_mgmt = get_management_file(mgmt_folder, f"{field_prefix}_cfs_{prior_year}.json")
            # print(json.dumps(soy_mgmt, indent=1))
            # print(json.dumps(corn_mgmt, indent=1))
        create_mukey_runs(
            mukeys,
            dbconn,
            rotation,
            met_file,
            field_name=runs_folder,
            tar_folder=tar_folder,
            start_year=start_year,
            end_year=end_year,
            sfc_mgmt=soy_mgmt,
            cfs_mgmt=corn_mgmt,
            swim=swim,
            saxton=saxton,
            maize_xml=maize_xml,
            soy_xml=soy_xml,
        )
        met_src_path = os.path.join(tar_folder, "met_files", met_folder, runs_dict[i][3])
        met_tar_path = os.path.join(
            tar_folder,
            "apsim_files",
            runs_folder,
            str(end_year),
            rotation,
            "met_files",
        )
        copy_met_file(met_src_path, met_tar_path)


def run_apsim_files_from_dict(runs_dict, tar_folder):
    for i in runs_dict:
        runs_folder = runs_dict[i][1]
        end_year = runs_dict[i][4]
        rotation = runs_dict[i][0]
        tar_apsim_files_path = os.path.join(tar_folder, "apsim_files", runs_folder, str(end_year), rotation)
        apsim.run_apsim.run_all_simulations(apsim_files_path=tar_apsim_files_path)
        print(f"Finished running files in {runs_folder}, {end_year}, {rotation}")
        print(" ")


###---------------------------------------------------------###
###           General munging to create APSIM files         ###
###---------------------------------------------------------###


def get_distinct(dbconn, table, id_column):
    """
    Returns a list of all unique entries in a database column.
    Args:
        dbconn {database connection} -- connection to postgresql database
        table {str} -- table name
        id_column (str) -- column of interest.
    Returns:
        list of all unique entries in a table column
    """
    entries = pd.read_sql(f"SELECT DISTINCT {id_column} FROM {table};", dbconn)
    entries = entries[id_column].tolist()
    return entries


def get_county(dbconn, table, fips, geom, limit=False, limit_num=100):
    """
    Get info for a county of interest from a geopandas df
    Args:
        dbconn {database connection} -- connection to postgresql database
        table {str} -- name of geopd table
        fips {str} -- fips id of the desired county eg. 'IA021'
        geom {str} -- column name that contains shape geometry
    Returns:
        geopandas dataframe with county info
    """
    # Get watershed as geopandas df
    if limit:
        query = f"SELECT * FROM {table} WHERE fips = '{fips}' LIMIT {limit_num};"
    else:
        query = f"SELECT * FROM {table} WHERE fips = '{fips}';"
    county_gpd = gpd.read_postgis(query, dbconn, geom_col=geom)
    return county_gpd


def get_centroid(geodf, id, geometry):
    """
    Find and return the centroid of a geopandas geometry
    Args:
        geodf {dataframe} -- geopandas dataframe
        id {string} -- the id of interest in the geodf (e.g., 'fips' for county column)
        geometry (string) - geopd column with geometries

    Returns:
        {np.array} -- lat and longitude of geometry
    """
    # get the geometry of interest by id - 'fips' for a county
    geom = geodf[[id, geometry]]
    # dissolve geometries to make one big geometry
    dissolved_geom = geom.dissolve(by=id)
    # find the centroid of the dissolved geometry and return its long, lat
    centroid = dissolved_geom[geometry].centroid
    coords = np.vstack([centroid.x, centroid.y]).T
    # change to array and lat, long
    centroid_coords = np.array([coords[0][1], coords[0][0]])
    return centroid_coords


def get_rotation(df, crop_column):
    """
    Get the crop rotation
    Args:
        df {obj} -- Dataframe that contains individual clukey information.
        crop_column {str} -- Column name that contains the label for what crop is growing for a given year.
    Returns:
        Str of the rotation. e.g., 'cs' = corn-soy
    """
    # save rotation for clukey to crops list
    try:
        df = df.sort_values(by=["years"], ascending=True)
        years = list(df["years"])
        last_year = years[-1]
        last_crop = df.loc[df["years"] == last_year, "crop"].item()
        crops = []
        for i in df.index:
            val = df.loc[i, crop_column]
            if val == "Corn" or val == "Soybean":
                crops.append(val)
            else:
                crops.append("other")
        # evaluate crops list and return a rotation
        if all(x in crops for x in ["Corn", "Soybean"]) and last_crop == "Soybean":
            rotation = "sfc"
        elif all(x in crops for x in ["Corn", "Soybean"]) and last_crop == "Corn":
            rotation = "cfs"
        elif all(x in crops for x in ["Corn"]):
            rotation = "cc"
        else:
            rotation = "other"
        return rotation
    except Exception:
        print("Something went wrong")
        traceback.print_exc()


###---------------------------------------------------------###
###                    General geo munging                  ###
###---------------------------------------------------------###


def wkb_hexer(line):
    "Converts multipolygon column in gpd to wkb"
    return line.wkb_hex


def reproject_vector(in_path, out_path, target_crs):
    """Reprojects vector file (eg, shapefile) to target CRS.

    Args:
        in_path (str): Path to file to reproject
        out_path (str): Path and name for new, reprojected file.
        target_crs (str, gpd_df.crs): String or use gpd_df.crs to input target CRS.

    Returns:
        [str]: Path to newly written geojson file.
    """
    try:
        gpd_df = gpd.read_file(in_path)
        if gpd_df.crs == target_crs:
            print("File is already in target CRS.")
            return in_path
        elif gpd_df.crs != target_crs:
            new_file = gpd_df.to_crs(target_crs)
            print(f"Dataframe reprojected to {target_crs}.")
            new_file.to_file(out_path, driver="GeoJSON")
            print(f"File re-written to {out_path}")
            return out_path
    except:
        print("Something went wrong.")
        traceback.print_exc()


def reproject_raster(inpath, outpath, target_crs):
    """Reprojects raster file (.tiff) to new crs.

    Args:
        inpath (str): Path to raster file.
        outpath (str): Path to output the reprojected raster file.
        target_crs (str): CRS to reproject to e.g., epsg:26915

    Returns:
        [str]: Path to newly projected tif file.
    """
    dst_crs = target_crs  # CRS for web meractor
    with rio.open(inpath) as src:
        transform, width, height = calculate_default_transform(src.crs, dst_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update(
            {
                "crs": dst_crs,
                "transform": transform,
                "width": width,
                "height": height,
            }
        )

        with rio.open(outpath, "w", **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rio.band(src, i),
                    destination=rio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest,
                )
        return outpath


def get_zonal_stats(vector, raster, stats):
    # Run zonal statistics, store result in geopandas dataframe
    result = zonal_stats(vector, raster, stats=stats, geojson_out=True)
    geostats = gpd.GeoDataFrame.from_features(result)
    return geostats
    # For generating raster from zonal statistics result


def stats_to_raster(zdf, raster, stats, out_raster, no_data="y"):
    meta = raster.meta.copy()
    out_shape = raster.shape
    transform = raster.transform
    dtype = raster.dtypes[0]
    field_list = list_columns(stats)
    index = int(input("Rasterize by which field? "))
    zone = zdf[field_list[index]]
    shapes = ((geom, value) for geom, value in zip(zdf.geometry, zone))
    burned = rasterize(shapes=shapes, fill=0, out_shape=out_shape, transform=transform)
    show(burned)
    meta.update(dtype=rio.float32, nodata=0)
    # Optional to set nodata values to min of stat
    if no_data == "y":
        cutoff = min(zone.values)
        print("Setting nodata cutoff to: ", cutoff)
        burned[burned < cutoff] = 0
    with rio.open(out_raster, "w", **meta) as out:
        out.write_band(1, burned)
    print("Zonal Statistics Raster generated")


###---------------------------------------------------------###
###                 Parse precip from met CSV               ###
###---------------------------------------------------------###

# these are just reference for when months end and start in cleaned met csv, including shift for leap years
month_start_end = [
    {"apr_s": 91, "apr_e": 120},
    {"may_s": 121, "may_e": 151},
    {"jun_s": 152, "jun_e": 181},
    {"jul_s": 182, "jul_e": 212},
    {"aug_s": 213, "aug_e": 243},
    {"sep_s": 244, "sep_e": 273},
]

month_start_end_leap = [
    {"apr_s": 92, "apr_e": 121},
    {"may_s": 122, "may_e": 152},
    {"jun_s": 153, "jun_e": 182},
    {"jul_s": 183, "jul_e": 213},
    {"aug_s": 214, "aug_e": 244},
    {"sep_s": 245, "sep_e": 274},
]


def sum_met_precip(df, year, precip_col="rain (mm)"):
    """Sums met file's total precip for target year.

    Args:
        met_path (str): path to target met .csv file.
        year (int): Year to sum weather for.
        precip_col (str, optional): Name of precipitation column in met csv. Defaults to 'rain (mm)'.

    Returns:
        [int]: Returns total precip for given year.
    """
    # df = pd.read_csv(met_path)
    set_type = {precip_col: float}
    df = df.astype(set_type)
    year_df = df.loc[df["year"] == year].reset_index(drop=True)
    total_precip = year_df[precip_col].sum()
    return total_precip


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
    leap_years = [yr for yr in range(1980, 2040, 4)]
    if year in leap_years:
        slices = (92, 121, 122, 152, 153, 182, 183, 213, 214, 244, 245, 274)
    else:
        slices = (91, 120, 121, 151, 152, 181, 182, 212, 213, 243, 244, 273)
    df = pd.read_csv(weather_csv)
    year_df = df.loc[df["year"] == year].reset_index(drop=True)
    # get values between desired sclices for precip column
    apr_sum = sum(year_df.iloc[slices[0] : slices[1], col_index])
    may_sum = sum(year_df.iloc[slices[2] : slices[3], col_index])
    jun_sum = sum(year_df.iloc[slices[4] : slices[5], col_index])
    jul_sum = sum(year_df.iloc[slices[6] : slices[7], col_index])
    aug_sum = sum(year_df.iloc[slices[8] : slices[9], col_index])
    sep_sum = sum(year_df.iloc[slices[10] : slices[11], col_index])
    month_sums = (apr_sum, may_sum, jun_sum, jul_sum, aug_sum, sep_sum)
    return month_sums


def create_summed_met_df(weather_csv, years, col_index):
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
        df[f"{i}"] = met_sum_list
    return df


def chart_met_growing_seasons(
    df,
    field_name,
    met_var,
    var_units,
    years,
    plot_style,
    fig_width=10,
    fig_height=12,
    ylim=350,
    cols=2,
):
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
    x = ("Apr", "May", "Jun", "Jul", "Aug", "Sep")
    tot = len(years)
    tot_range = range(tot)
    rows = tot // cols
    rows += tot % cols
    position = range(1, tot + 1)
    fig = plt.figure(1, figsize=(fig_width, fig_height))
    for i, k in zip(years, tot_range):
        y = df[f"{i}"]
        # add every single subplot to the figure with a for loop
        ax = fig.add_subplot(rows, cols, position[k])
        ax.set_ylim(0, ylim)
        ax.bar(x, y)
        ax.set(title=f"{i}", ylabel=met_var)
    fig.suptitle(
        f"{field_name} Monthly {met_var} ({var_units})",
        fontsize=14,
        fontweight="bold",
        y=1.02,
    )
    fig.tight_layout()
    plt.show()


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
    set_type = {precip_col: float}
    df = df.loc[df[year_col] == year]
    df = df.astype(set_type)
    df = df.nlargest(10, precip_col)
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
    # set_type = {
    #     day_col: int,
    #     precip_col : float
    # }
    # df = df.astype(set_type)
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
        print("one adjacent day of precipitation")
        event1 = sum_adjacent_days(df, days_list, day_col, precip_col)
        event1_precip = event1[0][2]
        df = df[df.day != event1[0][0]]
        df = df[df.day != event1[0][1]]
        df = df.sort_values(precip_col, ascending=False)
        event2_precip = df[precip_col].iloc[0]
        precip_events = [event1_precip, event2_precip]
    elif len(days_list) >= 2:
        print("more than one adjacent day of precipitation")
        events = sum_adjacent_days(df, days_list, day_col, precip_col)
        precip_values = []
        for i in events:
            precip_values.append(i[2])
        precip_values.sort(reverse=True)
        event1_precip = precip_values[0]
        event2_precip = precip_values[1]
        precip_events = [event1_precip, event2_precip]
    else:
        print("no adjacent days of precipitation")
        df = df.sort_values(precip_col, ascending=False)
        event1_precip = df[precip_col].iloc[0]
        event2_precip = df[precip_col].iloc[1]
        precip_events = [event1_precip, event2_precip]
    return precip_events


###---------------------------------------------------------###
###                       Sentinel 2                        ###
###---------------------------------------------------------###


def find_sentinel_products(footprint, api, start_date, end_date, max_cloud_cover):
    products = api.query(
        footprint,
        date=(start_date, end_date),
        platformname="Sentinel-2",
        cloudcoverpercentage=(0, max_cloud_cover),
    )
    products_gdf = api.to_geodataframe(products)
    return products_gdf


def download_sentinel_image(products_gdf, api, out_path, img_index=0):
    products_gdf_sorted = products_gdf.sort_values(["cloudcoverpercentage"], ascending=[True])
    img_selected = products_gdf_sorted.index[img_index]
    img_meta = products_gdf_sorted.iloc[img_index]
    print(f"Downloading image {img_meta['title']}, {img_meta['summary']} with cloud cover of {img_meta['cloudcoverpercentage']}.")
    api.download(img_selected, directory_path=out_path)
    return img_meta


def check_product_status(image_uuid, api):
    product_info = api.get_product_odata(image_uuid)

    if product_info["Online"]:
        print(f"Product {image_uuid} is online. Starting download.")
        api.download(image_uuid)
    else:
        print(f"Product {image_uuid} is not online.")


def unzip_sentinel_images(image_path, img_title):
    file_name = f"{image_path}\\{img_title}.zip"
    with ZipFile(file_name, "r") as zip:
        zip.extractall(path=image_path)


###---------------------------------------------------------###
###                           NDVI                          ###
###---------------------------------------------------------###


def get_image_bands(in_path, img_bands=["*B04.jp2", "*B08.jp2", "*B04_10m.jp2", "*B08_10m.jp2"]) -> list:
    # finds files with desired band extensions
    # bands are blue = 2, green = 3, red = 4, nir = 8
    # get all files with .jp2 in folder
    file_list = glob(in_path + "/**/*.jp2", recursive=True)
    images = []
    # find and return the band 4 and band 8 images
    for filename in file_list:
        for pattern in img_bands:
            if fnmatch.fnmatch(filename, pattern):
                images.append(filename)
    # returns list of desired images with paths
    return images


def get_TCI_image(in_path) -> list:
    # finds TCI (RGB image) file in directory
    # basically just for plotting color image
    file_list = glob(in_path + "/**/*.jp2", recursive=True)
    images = []
    # find and return the band 4 and band 8 images
    for filename in file_list:
        for pattern in ["*TCI.jp2"]:
            if fnmatch.fnmatch(filename, pattern):
                images.append(filename)
    return images


def create_rgb_tif(file_paths_list, out_path):
    # b2 is blue band; b3 is green; b4 is red
    b2_file = [file for file in file_paths_list if "B02" in file]
    b3_file = [file for file in file_paths_list if "B03" in file]
    b4_file = [file for file in file_paths_list if "B04" in file]
    b2 = rio.open(b2_file[0])
    b3 = rio.open(b3_file[0])
    b4 = rio.open(b4_file[0])
    with rio.open(
        out_path,
        "w",
        driver="Gtiff",
        width=b4.width,
        height=b4.height,
        count=3,
        crs=b4.crs,
        transform=b4.transform,
        dtype=b4.dtypes[0],
    ) as rgb:
        rgb.write(b2.read(1), 1)
        rgb.write(b3.read(1), 2)
        rgb.write(b4.read(1), 3)
        rgb.close()


def create_ndvi_tif(file_paths_list, out_path):
    # normalized difference vegetation index (ndvi)
    # b4 is red band; b8 is nir band
    b4_file = [file for file in file_paths_list if "B04" in file]
    b8_file = [file for file in file_paths_list if "B08" in file]
    b4 = rio.open(b4_file[0])
    b8 = rio.open(b8_file[0])
    red_b = b4.read()
    nir_b = b8.read()
    ndvi = (nir_b.astype(np.float32) - red_b.astype(np.float32)) / (nir_b.astype(np.float32) + red_b.astype(np.float32))
    meta = b4.meta
    meta.update(driver="GTiff")
    meta.update(dtype=rio.float32)

    with rio.open(out_path, "w", **meta) as dst:
        dst.write(ndvi.astype(rio.float32))


def create_gci_tif(file_paths_list, out_path):
    # green chlorophyll index
    # b3 is green band; b8 is nir band
    # nir / green - 1
    b3_file = [file for file in file_paths_list if "B03" in file]
    b8_file = [file for file in file_paths_list if "B08" in file]
    b3 = rio.open(b3_file[0])
    b8 = rio.open(b8_file[0])
    green_b = b3.read()
    nir_b = b8.read()
    gci = (nir_b.astype(np.float32) / green_b.astype(np.float32)) - 1
    meta = b3.meta
    meta.update(driver="GTiff")
    meta.update(dtype=rio.float32)

    with rio.open(out_path, "w", **meta) as dst:
        dst.write(gci.astype(rio.float32))


def create_savi_tif(file_paths_list, out_path):
    # soil adjusted vegetation index
    # b4 is red band; b8 is nir band
    b4_file = [file for file in file_paths_list if "B04" in file]
    b8_file = [file for file in file_paths_list if "B08" in file]
    b4 = rio.open(b4_file[0])
    b8 = rio.open(b8_file[0])
    red_b = b4.read()
    nir_b = b8.read()
    savi = (nir_b.astype(np.float32) - red_b.astype(np.float32)) / (nir_b.astype(np.float32) + red_b.astype(np.float32) + 0.428) * (1.428)
    meta = b4.meta
    meta.update(driver="GTiff")
    meta.update(dtype=rio.float32)

    with rio.open(out_path, "w", **meta) as dst:
        dst.write(savi.astype(rio.float32))


def create_evi_tif(file_paths_list, out_path):
    # enhanced vegetation index
    # b2 is blue; b4 is red band; b8 is nir band
    b2_file = [file for file in file_paths_list if "B02" in file]
    b4_file = [file for file in file_paths_list if "B04" in file]
    b8_file = [file for file in file_paths_list if "B08" in file]
    b2 = rio.open(b2_file[0])
    b4 = rio.open(b4_file[0])
    b8 = rio.open(b8_file[0])
    blue_b = b2.read()
    red_b = b4.read()
    nir_b = b8.read()
    evi = 2.5 * ((nir_b.astype(np.float32) - red_b.astype(np.float32)) / ((nir_b.astype(np.float32) + 6) * (red_b.astype(np.float32) - 7.5) * (blue_b.astype(np.float32) + 1)))
    meta = b4.meta
    meta.update(driver="GTiff")
    meta.update(dtype=rio.float32)

    with rio.open(out_path, "w", **meta) as dst:
        dst.write(evi.astype(rio.float32))


def clip_raster(in_file, mask_layer, out_path):
    # crop ndvi image to field boundary
    with rio.open(in_file) as src:
        out_image, out_transform = mask(src, mask_layer, crop=True)
        out_meta = src.meta.copy()
        out_meta.update(
            {
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
            }
        )

    with rio.open(out_path, "w", **out_meta) as dst:
        dst.write(out_image)


###---------------------------------------------------------###
###                       Create full DF                    ###
###---------------------------------------------------------###


def prepare_twi_df(
    ym_path,
    in_path,
    out_path,
    target_crs,
    year,
    field_name,
    crop,
    all_touched=False,
):
    new_twi_file = reproject_raster(in_path, out_path, target_crs)
    twi_stats = rs.zonal_stats(
        ym_path,
        new_twi_file,
        geojson_out=True,
        stats=["mean"],
        all_touched=all_touched,
    )
    twi_gdf = gpd.GeoDataFrame.from_features(twi_stats)
    twi_gdf.rename(columns={"mean": "mean_twi"}, inplace=True)
    twi_gdf.insert(1, "Crop", crop)
    twi_gdf.insert(1, "Year", year)
    twi_gdf.insert(1, "Field", field_name)
    twi_gdf = twi_gdf.set_crs(target_crs)
    return twi_gdf


def prepare_ndvi_df(twi_gdf, month, in_path, out_path, target_crs, all_touched=False):
    # prepare ndvi
    new_ndvi_file = reproject_raster(in_path, out_path, target_crs)
    ndvi_stats = rs.zonal_stats(
        twi_gdf,
        new_ndvi_file,
        geojson_out=True,
        stats=["mean"],
        all_touched=all_touched,
    )
    ndvi_twi_gdf = gpd.GeoDataFrame.from_features(ndvi_stats)
    ndvi_twi_gdf.rename(columns={"mean": f"{month}_ndvi"}, inplace=True)
    # set projection again since it is lost for some reason
    ndvi_twi_gdf = ndvi_twi_gdf.set_crs(target_crs)
    return ndvi_twi_gdf


def prepare_gci_df(ndvi_twi_gdf, month, in_path, out_path, target_crs, all_touched=False):
    # prepare ndvi
    new_gci_file = reproject_raster(in_path, out_path, target_crs)
    gci_stats = rs.zonal_stats(
        ndvi_twi_gdf,
        new_gci_file,
        geojson_out=True,
        stats=["mean"],
        all_touched=all_touched,
    )
    gci_ndvi_twi_gdf = gpd.GeoDataFrame.from_features(gci_stats)
    gci_ndvi_twi_gdf.rename(columns={"mean": f"{month}_gci"}, inplace=True)
    # set projection again since it is lost for some reason
    gci_ndvi_twi_gdf = gci_ndvi_twi_gdf.set_crs(target_crs)
    return gci_ndvi_twi_gdf


def prepare_met_df(in_path, gci_ndvi_twi_gdf, year, header=7, precip_col="rain"):
    # get met data
    met_df = pd.read_csv(in_path, header=header, sep=" ")
    if met_df.empty:
        sys.exit("Dataframe is empty.")
    met_df = met_df.drop([0])
    data_type_dict = {
        "year": str,
        "day": int,
        "radn": float,
        "maxt": float,
        "mint": float,
        "rain": float,
    }
    met_df = met_df.astype(data_type_dict)
    top10_precip_events_df = get_top_ten_days(met_df, str(year), "year", precip_col)
    adjacent_days_list = check_adjacent_days(top10_precip_events_df, "day", precip_col)
    top2 = get_top2_precip_events(top10_precip_events_df, adjacent_days_list, "day", precip_col)
    total_precip = sum_met_precip(met_df, str(year), precip_col)
    gci_ndvi_twi_gdf.insert(3, "top_prec_2", top2[1])
    gci_ndvi_twi_gdf.insert(3, "top_prec_1", top2[0])
    gci_ndvi_twi_gdf.insert(3, "tot_precip", total_precip)
    gci_ndvi_twi_met_gdf = gci_ndvi_twi_gdf
    if gci_ndvi_twi_met_gdf.empty:
        print("ndvi_twi_met_gdf from prepare_met_df() is empty")
    return gci_ndvi_twi_met_gdf


def prepare_ssurgo_df(gci_ndvi_twi_met_gdf, in_path, out_path, target_crs):
    # prepare ssurgo
    new_ssurgo_file = reproject_vector(in_path, out_path, target_crs)
    ssurgo_df = gpd.read_file(new_ssurgo_file)
    ssurgo_df = ssurgo_df.drop(
        ["objectid", "shape_area", "shape_length", "shape_leng", "spatialver"],
        axis=1,
        errors="ignore",
    )
    gci_ndvi_twi_met_ssurgo_gdf = gpd.sjoin(gci_ndvi_twi_met_gdf, ssurgo_df)
    if gci_ndvi_twi_met_ssurgo_gdf.empty:
        print("ndvi_twi_met_ssurgo_gdf from prepare_ssurgo_df() is empty")
    return gci_ndvi_twi_met_ssurgo_gdf


def prepare_apsim_full_df(
    gci_ndvi_twi_met_ssurgo_gdf,
    apsim_files_path,
    year,
    project_out_path,
    write_file,
    driver="GeoJSON",
):
    # prepare apsim files
    if os.path.exists(project_out_path):
        num_files_removed = 0
        for filename in os.listdir(project_out_path):
            for pattern in ["*.dbf", "*.shp", "*.cpg", "*.prj", "*.shx"]:
                if fnmatch.fnmatch(filename, pattern):
                    os.remove(project_out_path + filename)
                    num_files_removed += 1
        print(f"Removed {num_files_removed} old files.")
    apsim_df = parse_summary_output_field(apsim_files_path, year)
    if apsim_df.empty:
        print("No apsim files to parse for prepare_apsim_full_df()")
    # check if mukeys are all in both files
    mukeys = list(np.unique(apsim_df["mukey"]))
    other_mukeys = list(np.unique(gci_ndvi_twi_met_ssurgo_gdf["mukey"]))
    if mukeys == other_mukeys:
        print("Mukeys are equal")
    else:
        print("Not all mukeys same in both files.")
        pass
    # merge to create full df
    full_df = gci_ndvi_twi_met_ssurgo_gdf.merge(apsim_df, on="mukey")
    full_path = os.path.join(project_out_path, write_file)
    full_df.to_file(full_path, driver)


# Field list is list with field names
# e.g. biocentury_fields = ['ebilsland', 'kfinch', 'accola']
def make_outdir_folders(field_list):
    for i in field_list:
        field_folder = os.path.join("out_files", i, "fus")
        if not os.path.exists(field_folder):
            os.makedirs(field_folder)


def create_sampled_geofile(field_list, driver="GeoJSON"):
    for i in field_list:
        field = json.loads(open(f"field_processing_jsons/{i}.json", "r").read())
        field_folder = os.path.join("out_files", i, "fus")
        # if not os.path.exists(field_folder):
        #     os.mkdirs(field_folder)
        for i in field["year"]:
            field_name = field["field_name"]
            twi_path = field["twi_file"]
            ssurgo_path = field["ssurgo_file"]
            fus_path = field["year"][i]["fus_path"]
            ym_file = field["year"][i]["ym_file"]
            rotation = field["year"][i]["rotation"]
            crop = field["year"][i]["crop"]
            apsim_folder = field["apsim_files"]
            met_file = field["met_file"]
            june_ndvi_date = f"jun_{i}"
            july_ndvi_date = f"jul_{i}"
            june_ndvi_file = ""
            july_ndvi_file = ""
            # gci
            june_gci_date = f"jun_{i}"
            july_gci_date = f"jul_{i}"
            june_gci_file = ""
            july_gci_file = ""
            # set target crs from gpd df
            ym_gdf = gpd.read_file(ym_file)
            target_crs = ym_gdf.crs
            # search for june and july ndvi files
            for file in os.listdir(f"ndvi/{field_name}"):
                if june_ndvi_date in file:
                    june_ndvi_file = file
                if july_ndvi_date in file:
                    july_ndvi_file = file
            if june_ndvi_file == "":
                print(f"June NDVI file not found for {field_name} {i}.")
                continue
            if july_ndvi_file == "":
                print(f"July NDVI file not found for {field_name} {i}.")
                continue
            # search for june and july gci files
            for file in os.listdir(f"gci/{field_name}"):
                if june_gci_date in file:
                    june_gci_file = file
                if july_gci_date in file:
                    july_gci_file = file
            if june_gci_file == "":
                print(f"June GCI file not found for {field_name} {i}.")
                continue
            if july_gci_file == "":
                print(f"July GCI file not found for {field_name} {i}.")
                continue
            # sample twi to ym file
            twi_out_path = os.path.join("out_files", field_name, f"{field_name}_twi_26915.tif")
            twi_gdf = prepare_twi_df(
                ym_file,
                twi_path,
                twi_out_path,
                target_crs,
                i,
                field_name,
                crop,
            )
            twi_gdf["fld_name"] = field_name
            ## sample ndvi
            # first get appropirate in and out paths
            jun_ndvi_in_path = os.path.join("ndvi", field_name, june_ndvi_file)
            jun_ndvi_out_path = os.path.join(
                "out_files",
                field_name,
                f"{field_name}_ndvi_twi_jun_{i}_26915.tif",
            )
            jul_ndvi_in_path = os.path.join("ndvi", field_name, july_ndvi_file)
            jul_ndvi_out_path = os.path.join(
                "out_files",
                field_name,
                f"{field_name}_ndvi_twi_jul_{i}_26915.tif",
            )
            # then sample for june and for july
            jun_ndvi_twi_gdf = prepare_ndvi_df(
                twi_gdf,
                "jun",
                jun_ndvi_in_path,
                jun_ndvi_out_path,
                target_crs,
                all_touched=False,
            )
            jul_ndvi_twi_gdf = prepare_ndvi_df(
                jun_ndvi_twi_gdf,
                "jul",
                jul_ndvi_in_path,
                jul_ndvi_out_path,
                target_crs,
                all_touched=False,
            )
            ## sample gci
            # first get appropirate in and out paths
            jun_gci_in_path = os.path.join("gci", field_name, june_gci_file)
            jun_gci_out_path = os.path.join(
                "out_files",
                field_name,
                f"{field_name}_gci_ndvi_twi_jun_{i}_26915.tif",
            )
            jul_gci_in_path = os.path.join("gci", field_name, july_gci_file)
            jul_gci_out_path = os.path.join(
                "out_files",
                field_name,
                f"{field_name}_gci_ndvi_twi_jul_{i}_26915.tif",
            )
            # then sample for june and for july
            jun_gci_twi_gdf = prepare_gci_df(
                jul_ndvi_twi_gdf,
                "jun",
                jun_gci_in_path,
                jun_gci_out_path,
                target_crs,
                all_touched=False,
            )
            jul_gci_ndvi_twi_gdf = prepare_gci_df(
                jun_gci_twi_gdf,
                "jul",
                jul_gci_in_path,
                jul_gci_out_path,
                target_crs,
                all_touched=False,
            )
            ## met
            met_path = os.path.join("met_files", "nasapwr", f"{met_file}")
            gci_ndvi_twi_met_gdf = prepare_met_df(met_path, jul_gci_ndvi_twi_gdf, i, header=7, precip_col="rain")
            ## ssurgo
            ssurgo_out_path = os.path.join("out_files", field_name, f"{field_name}_ssurgo_26915.geojson")
            gci_ndvi_twi_met_ssurgo_gdf = prepare_ssurgo_df(gci_ndvi_twi_met_gdf, ssurgo_path, ssurgo_out_path, target_crs)
            ## apsim files
            apsim_files_path = os.path.join("apsim_files", apsim_folder, i, rotation)
            write_file = f"{field_name}_{crop}_{i}_full.geojson"
            # driver = GeoJSON or ESRI Shapefile
            prepare_apsim_full_df(
                gci_ndvi_twi_met_ssurgo_gdf,
                apsim_files_path,
                int(i),
                field_folder,
                write_file,
                driver=driver,
            )
            fus_src = os.path.join(field_folder, write_file)
            fus_dst = os.path.join(fus_path, write_file)
            shutil.copy(fus_src, fus_dst)


###---------------------------------------------------------###
###                       Miscellaneous                     ###
###---------------------------------------------------------###


# Function to convert a CSV to JSON
# Takes the key/id column and file paths as arguments
def csv_to_json(key_col, csv_file_path, json_file_path):
    # create a dictionary
    data = {}

    # Open a csv reader called DictReader
    with open(csv_file_path, encoding="utf-8") as csvf:
        csv_reader = csv.DictReader(csvf)

        # Convert each row into a dictionary
        # and add it to data
        for rows in csv_reader:
            # key_col is the primary key/id column
            key = rows[key_col]
            data[key] = rows

    # Open a json writer, and use the json.dumps()
    # function to dump data
    with open(json_file_path, "w", encoding="utf-8") as jsonf:
        jsonf.write(json.dumps(data, indent=4))


# convert date to number date (e.g., day of year = 127)
day_of_year = datetime.now().timetuple().tm_yday
