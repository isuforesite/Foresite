import geopandas as gpd
import pandas as pd

# A csv file in wide format with one yield monitor observation per row and at least the following column variables (include header in the first row).
# site: site name, e.g., Basswood, Orbweaver North
# year: year, e.g., 2020
# record: a numeric, ordered index
# x: latitude in meters
# y: longitude in meters
# mass: the variable to smooth, e.g., harvested mass in kilograms at standard market moisture
# swath: swath width in meters
# d: distance in meters between the current row observation and the previous row observation,

def read_ym_file(ym_file) -> gpd.GeoDataFrame:
    """Reads in ym file, checks if geometry column exists, and returns gdf.

    Args:
        ym_file (str): Path to ym file.

    Returns:
        gpd.GeoDataFrame: a geopandas geodataframe
    """
    try:
        gdf = gpd.read_file(ym_file)
        if gdf.geometry is not None:
            return gdf
        else:
            print('File has no geometry column.')
            return
    except Exception:
        print('Incorrect path, file does not exist, or not readable by GeoPandas.')

def reproject_ym(ym_gdf, target_crs='EPSG:26915') -> gpd.GeoDataFrame:
    """Reporjects yield monitor file to a UTM projection.

    Args:
        ym_gdf (gpd.GeoDataFrame): geopandas dataframe to reproject
        target_crs (str, optional): Target crs to convert to. Must be UTM. Defaults to 'EPSG:26915'.

    Returns:
        gpd.GeoDataFrame: gdf in new UTM projection.
    """
    if ym_gdf.crs.utm_zone is not None:
        print('Projection is already in UTM')
        return
    else:
        print('Changing projection to UTM')
        #convert to a UTM projection, default is UTM zone 15N/26915
        reprojected_ym_gdf = ym_gdf.to_crs('EPSG:26915')
        return reprojected_ym_gdf


def format_xy(ym_gdf) -> gpd.GeoDataFrame:
    """Adds coordinates to gdf as new columns: x and y.

    Args:
        ym_gdf (gpd.GeoDataframe): geopandas geodataframe

    Returns:
        gpd.GeoDataFrame: a geopandas geodataframe with new x, y columns
    """
    if ym_gdf.crs.utm_zone is not None:
        ym_gdf['x'] = ym_gdf['geometry'].x
        ym_gdf['y'] = ym_gdf['geometry'].y
        return ym_gdf
    else:
        return

def add_record_col(ym_gdf) -> gpd.GeoDataFrame:
    """Adds record/id/numberic column to gdf.
    Args:
        ym_gdf (gpd.GeoDataframe): geopandas geodataframe
    Returns:
        gpd.GeoDataFrame: a geopandas geodataframe with new record/id column.
    """
    ym_gdf['record'] = range(1, len(ym_gdf)+1)
    return ym_gdf

class RitasYieldMonitor:
    """Class for basic RITAS yield monitor file creation.
    Args:
        ym_file (str): Path to target ym file.
        site_name (str): Name of field site
        crop (str): type of crop planted.
        tar_moist (float): target crop moisture value (e.g. 15.5 for maize, 13 for soybeans)
        tar_crs (str): Target CRS for file. Must be in UTM. Default is UTM 15N/26915.
    Returns:
        gpd.GeoDataFrame: a geopandas geodataframe with new record/id column.

    """
    def __init__(self, ym_file, site_name, crop, tar_moist=15.5, tar_crs="EPSG:26915"):
        self.ym_file = ym_file
        self.site_name = site_name
        self.crop = crop
        self.tar_moist = tar_moist
        self.tar_crs = tar_crs
        
    def format_ym_file(self):
        if self.tar_moist < 0:
            print('Target moisture cannot be less than 0')
            return
        else:
            self.tar_moist = 1 + (self.tar_moist/100)
        self.formatted_gdf = read_ym_file(self.ym_file)
        self.formatted_gdf = reproject_ym(self.formatted_gdf, target_crs=self.tar_crs)
        self.formatted_gdf = format_xy(self.formatted_gdf)
        self.formatted_gdf = add_record_col(self.formatted_gdf)
        self.formatted_gdf['crop'] = self.crop
        self.formatted_gdf['site'] = self.site_name
        return self.formatted_gdf
    
class ApexYieldMonitor(RitasYieldMonitor):
    """RITAS Yield Monitor class for JD Apex system data.

    Important variables:

    HarvestM : Harvest moisture (%) -> returned as 'moisture' (%)
    YieldMas : Dry yield mass (lbs or tons) --- think it's lbs?
    mass : YieldMas * standark market moisture of whichever crop (e.g., * 1.155 for 15.5% moisture corn)
    Width : width of harvest pass (feet) -> returned as 'swath' (meters)
    Distance : Distance traveled (feet) -> returned as 'd' (meters)
    'ProcYear': returned as 'year'
    """
    def __init__(self, ym_file, site_name, crop, tar_moist, tar_crs):
        super().__init__(ym_file, site_name, crop, tar_moist, tar_crs)
    
    def format_apex_file(self):
        self.formatted_gdf = super().format_ym_file()
        ## if converting lbs to kg
        self.formatted_gdf['swath'] = self.formatted_gdf['Width'] * 0.3048
        self.formatted_gdf['Distance'] = self.formatted_gdf['Distance'] * 0.3048
        self.formatted_gdf['mass'] = (self.formatted_gdf['YieldMas'] * self.tar_moist) * 0.45359237
        self.formatted_gdf['ProcYear'] = self.formatted_gdf['ProcYear'].astype('int32')
        ## if converting tons to kg
        # self.formatted_gdf['mass'] = (self.formatted_gdf['YieldMas'] * self.tar_moist) * 907.18474
        self.formatted_gdf = self.formatted_gdf.rename(columns = {
            'Distance': 'd',
            'HarvestM' : 'moisture',
            'ProcYear':'year'
            })
        
        return self.formatted_gdf



