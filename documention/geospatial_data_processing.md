### Convert vector data to raster
Step 1:
* add boundary and yield monitor vector layers  

Step 2
* Convert yield polygons to raster with gdal’s rasterize (vector to raster) 
* Note: the higher the width/horizontal resolution the more grid points
* See example below  
  
![Vector to raster conversion example in QGIS/gdal](figures/vector-to-raster.png "Vector to raster conversion in QGIS")  
  
### Intersect SSURGO and field boundaries  
Step 1:
* add field boundary  

Step 2:
* Add SSURGO soils.
* Easiest way is to select the underlying county data from the database with fips. County IDs can be found at https://websoilsurvey.nrcs.usda.gov/app/WebSoilSurvey.aspx (state of Iowa is 19, so 19015 is Boone county with fips 015)
* Once the county SSURGO data is added you can do an intersection with the field boundary and ssurgo to get underlying soils.
* Once intersected, area needs to be recalculated with 'Add geometry attributes'. This area can then be multipled by 0.000247105 to get the area in acres.