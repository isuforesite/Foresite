#!/usr/bin/env Python

import requests
import pandas as pd
import io

daymet_endpt = 'https://daymet.ornl.gov/single-pixel/api/data'

# day length (s/day)
# min_temp (C)
# max_temp (C)
# precip (mm)
# radiation (W/m2)
# snow-water equiv. (kg/m2)
# vapor pressure (Pa)
def GetDaymetDataBuffer( site, startyr, endyr, lat, lon,
    attributes = [ 'dayl','prcp', 'srad','swe', 'tmax','tmin','vp' ] ):
    year_arr = [ str( startyr + i ) for i in range( endyr - startyr + 1 ) ]
    payload = {
        'lat': str( lat ),
        'lon': str( lon ),
        'vars': ','.join( attributes ),
        'years': ','.join( year_arr )
    }
    req = requests.get( daymet_endpt, params = payload )
    df = pd.read_csv( io.StringIO( req.text ), sep = ',', header = 6 )

    df[ 'day' ] = df[ 'yday' ]

    #daylength (hours)
    df[ 'dayL' ] = df[ 'dayl (s)' ]/3600

    #solar radiation (MJ/m2)
    df[ 'radn' ] = df[ 'srad (W/m^2)' ] * df[ 'dayl (s)' ] / 3600 * 0.0036

    #max temperature (deg C)
    df[ 'maxt' ] = df[ 'tmax (deg c)' ]

    #min temperature (deg C)
    df[ 'mint' ] = df[ 'tmin (deg c)' ]

    #vapor pressure (kPa)
    df[ 'vp' ] = df[ 'vp (Pa)' ] * 0.001

    #snow and rain (mm)
    df[ 'rain' ] = 0.0
    df[ 'snow' ] = 0.0

    #check is snow-water equivalent increases next day
    for idx, row in df.iterrows():

        if idx == 0:
            df.iloc[idx][ 'snow' ] = 0.0
            df.iloc[idx][ 'rain' ] = row[ 'prcp (mm/day)' ]
            continue
        elif idx == len( df ) - 1:
            df.iloc[idx][ 'snow' ] = 0.0
            df.iloc[idx][ 'rain' ] = row[ 'prcp (mm/day)' ]
            continue
        else:
            cur = row[ 'swe (kg/m^2)' ]
            next = df.iloc[idx+1][ 'swe (kg/m^2)' ]
            if next > cur:
                df.iloc[idx][ 'snow' ] = row[ 'prcp (mm/day)' ]
                df.iloc[idx][ 'rain' ] = 0.0
            elif ( next > 0.0 ) & ( next == cur ):
                df.iloc[idx][ 'snow' ] = row[ 'prcp (mm/day)' ]
                df.iloc[idx][ 'rain' ] = 0.0
            else:
                df.iloc[idx][ 'snow' ] = 0.0
                df.iloc[idx][ 'rain' ] = row[ 'prcp (mm/day)' ]

    df = df[ [ 'year', 'day', 'radn', 'maxt', 'mint', 'rain', 'snow',
        'vp','dayL' ] ]

    filename = site + '_' + str( startyr ) + '_' + str( endyr ) + '.met'
    headers = '\t'.join( [ 'year', 'day', 'radn', 'maxt', 'mint', 'rain',
        'snow', 'vp', 'dayL' ] )
    units = '\t'.join( [ '()', '()', 'MJ/m^2', 'oC', 'oC', 'mm',
        'mm', 'kPa', 'hours' ] )

    metfile = open( filename, 'w' )
    metfile.write( '[weather.met.weather]\n' )
    metfile.write( 'Location = ' + site + '\n' )
    metfile.write( 'latitude = ' + str( lat ) + ' (DECIMAL DEGREES)\n' )
    metfile.write( 'longitude = ' + str( lon ) + ' (DECIMAL DEGREES)\n' )
    metfile.write( 'Elevation = ' + '\n' )
    metfile.write( 'tav = ' + '\n' )
    metfile.write( 'amp = ' + '\n' )
    metfile.write( '! AEPE framework - Iowa State University\n' )
    metfile.write( '! source: Daymet (daymet.ornl.gov)\n' )
    metfile.write( headers + '\n' )
    metfile.write( units + '\n' )
    metfile.write( df.to_csv( sep = '\t', header = False, index = False ) )
    metfile.close()

    return req.content


daymet_buff = GetDaymetDataBuffer( 'test_site', 2018, 2018, 38.4811551130942,
    -94.5346701279425 )
