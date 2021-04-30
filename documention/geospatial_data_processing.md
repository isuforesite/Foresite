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
* Once intersected, area needs to be recalculated with 'Add geometry attributes'. This area can then be multipled by 0.000247105 to get the area in acres.\

### Calculate TWI with SAGA
1.	‘Fill sinks’ (Planch and Darbeaux) using DEM as input.
2.	Calculate Slope, Aspect, Curvature using the 'filled' DEM from step 1.
3.	Take the filled dem from step 1 and calculate ‘Flow Accumulation’ (Top Down)
4.	Calculate ‘Flow Width and Specific Catchment Area’ by taking filled DEM from step 1 and the ‘Flow Accumulation’ from step 3 (Flow Accumulation is the input for ‘Total Catchment Area’) 
5.	Calculate TWI using the ‘Specific Catchment Area’ from step 4 and the Slope from step 2.

### Yield monitor cleaning
Currently, outliers are removed by simply removing any point  
with bu/ac under 25 or over 350 bu/ac (col. Yld_Vol_Dr)

### Looping through Pandas DF
