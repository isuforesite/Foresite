#!/usr/bin/env Python

import requests
import pandas as pd
import io

daymet_endpt = 'https://daymet.ornl.gov/single-pixel/api/data'

### Daymet variables
# day length (s/day)
# min_temp (C)
# max_temp (C)
# precip (mm)
# radiation (W/m2)
# snow-water equiv. (kg/m2)
# vapor pressure (Pa)

leap_years = [ yr for yr in range( 1980, 2020, 4 ) ]

print( leap_years )

def GetDaymetData( filepath, startyr, endyr, lat, lon,
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
    df[ 'dayL' ] = round( df[ 'dayl (s)' ]/3600, 1 )

    #solar radiation (MJ/m2)
    df[ 'radn' ] = round( df[ 'srad (W/m^2)' ] * df[ 'dayl (s)' ] / 3600 * 0.0036, 1 )

    #max temperature (deg C)
    df[ 'maxt' ] = round( df[ 'tmax (deg c)' ], 1 )

    #min temperature (deg C)
    df[ 'mint' ] = round( df[ 'tmin (deg c)' ], 1 )

    #vapor pressure (kPa)
    df[ 'vp' ] = round( df[ 'vp (Pa)' ] * 0.001, 1 )

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
        'vp', 'dayL' ] ]

    print( df )

    headers = ' '.join( [ 'year', 'day', 'radn', 'maxt', 'mint', 'rain',
        'snow', 'vp', 'dayL' ] )
    units = ' '.join( [ '()', '()', '(MJ/m^2)', '(oC)', '(oC)', '(mm)', '(mm)',
        '(kPa)', '(hours)' ] )

    metfile = open( filepath, 'w' )
    metfile.write( '[weather.met.weather]\r\n' )
    metfile.write( 'stateionname = Foresite generated weather\r\n')
    metfile.write( 'latitude = {} (DECIMAL DEGREES)\r\n'.format( lat ) )
    metfile.write( 'longitude = {} (DECIMAL DEGREES)\r\n'.format( lon ) )
    metfile.write( 'tav = ' + str( round( df[ 'maxt' ].mean(), 1 ) ) + '\r\n' )
    metfile.write( 'amp = ' + str( round( df[ 'maxt' ].max(), 1 ) ) + '\r\n' )
    metfile.write( '!Weather generated using ISU Foresite framework\r\n')
    metfile.write( headers + '\r\n' )
    metfile.write( units + '\r\n' )
    metfile.write( df.to_csv( sep = ' ', header = False, index = False,
        line_terminator='\r\n' ) )
    metfile.close()

    return df

def Create_Met_Files( wth_df ):
    wth_sample_ids = wth_df[ 'weather_sample_id' ].unique()
    for wth_id in wth_sample_ids:
        file_path = 'wth_sample_{}.met'.format( wth_id )
        df = pd.DataFrame()
        df[ 'day' ] = wth_df[ 'yday' ]
        df[ 'dayL' ] = wth_df[ 'dayl' ]/3600
        df[ 'radn' ] = wth_df[ 'srad' ] * wth_df[ 'dayl' ] / 3600 * 0.0036
        df[ 'maxt' ] = wth_df[ 'tmax' ]
        df[ 'mint' ] = wth_df[ 'tmin' ]
        df[ 'prcp' ] = wth_df[ 'prcp' ]
        df[ 'swe' ] = wth_df[ 'swe' ]
        df[ 'vp' ] = wth_df[ 'vp' ] * 0.001
        df[ 'rain' ] = 0.0
        df[ 'snow' ] = 0.0
        df[ 'weather_id' ] = wth_id
        df[ 'year' ] = 2019

        #check is snow-water equivalent increases next day
        for idx, row in df.iterrows():
            if idx == 0:
                df.loc[ idx:idx, 'snow' ] = 0.0
                df.loc[ idx:idx, 'rain' ] = row[ 'prcp' ]
                continue
            elif idx == len( df ) - 1:
                df.loc[ idx:idx, 'snow' ] = 0.0
                df.loc[ idx:idx, 'rain' ] = row[ 'prcp' ]
                continue
            else:
                cur = row[ 'swe' ]
                next = df.iloc[idx+1][ 'swe' ]
                if next > cur:
                    df.loc[ idx:idx, 'snow' ] = row[ 'prcp' ]
                    df.loc[ idx:idx, 'rain' ] = 0.0
                elif ( next > 0.0 ) & ( next == cur ):
                    df.loc[ idx:idx, 'snow' ] = row[ 'prcp' ]
                    df.loc[ idx:idx, 'rain' ] = 0.0
                else:
                    df.loc[ idx:idx, 'snow' ] = 0.0
                    df.loc[ idx:idx, 'rain' ] = row[ 'prcp' ]

        df = df.round( 2 )

        df = df[ [ 'year', 'day', 'radn', 'maxt', 'mint', 'rain', 'snow', 'vp','dayL' ] ]

        file_path = 'apsim_files/met_files/weather_{}.met'.format( wth_id )
        headers = ' '.join( [ 'year', 'day', 'radn', 'maxt', 'mint', 'rain', 'snow', 'vp', 'dayL' ] )
        units = ' '.join( [ '()', '()', '(MJ/m^2)', '(oC)', '(oC)', '(mm)', '(mm)', '(kPa)', '(hours)' ] )

        metfile = open( file_path, 'w' )
        metfile.write( '[weather.met.weather]\n' )
        metfile.write( 'stateionname = Foresite generated weather\n')
        metfile.write( 'latitude = 42.0204 (DECIMAL DEGREES)\n' )
        metfile.write( 'longitude = -93.7738 (DECIMAL DEGREES)\n' )
        metfile.write( 'tav = ' + str( df[ 'maxt' ].mean() ) + '\n' )
        metfile.write( 'amp = ' + str( df[ 'maxt' ].max() ) + '\n' )
        metfile.write( '!Weather generated using ISU Foresite framework\n')
        metfile.write( headers + '\n' )
        metfile.write( units + '\n' )
        metfile.write( df.to_csv( sep = ' ', header = False, index = False ) )
        metfile.close()


    return

### example
#GetDaymetDataBuffer( 'IA169', 1980, 2018, 42.0362414914617, -93.4650447653806 )
