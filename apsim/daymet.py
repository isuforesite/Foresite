#!/usr/bin/env Python

import requests
import pandas as pd
import io

DAYMET_URL = 'https://daymet.ornl.gov/single-pixel/api/data'

### Daymet variables and units
# day length (s/day)
# min_temp (C)
# max_temp (C)
# precip (mm)
# radiation (W/m2)
# snow-water equiv. (kg/m2)
# vapor pressure (Pa)

def GetDaymetData( startyr, endyr, lat, lon,
    attributes = [ 'dayl','prcp', 'srad','swe', 'tmax','tmin','vp' ],
    filepath = None ):

    leap_years = [ yr for yr in range( 1980, 2020, 4 ) ]

    year_arr = [ str( startyr + i ) for i in range( endyr - startyr + 1 ) ]
    payload = {
        'lat': str( lat ),
        'lon': str( lon ),
        'vars': ','.join( attributes ),
        'years': ','.join( year_arr )
    }
    req = requests.get( DAYMET_URL, params = payload )
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

    # The Daymet calendar is based on a standard calendar year. All Daymet
    # years have 1 - 365 days, including leap years. For leap years, the Daymet
    # database includes leap day. Values for December 31 are discarded from
    # leap years to maintain a 365-day year.
    for lp_yr in leap_years:
        lp_day = df.loc[ ( df[ 'year' ] == lp_yr ) &
            ( df[ 'day' ] == 365 ) ].copy( deep = True )
        lp_day[ 'day' ] = 366
        lp_day[ 'yday' ] = 366

        df = df.append( lp_day, ignore_index = True )

    df = df.sort_values( by = [ 'year', 'yday' ] )

    # check if snow-water equivalent increases next day
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

    headers = ' '.join( [ 'year', 'day', 'radn', 'maxt', 'mint', 'rain',
        'snow', 'vp', 'dayL' ] )
    units = ' '.join( [ '()', '()', '(MJ/m^2)', '(oC)', '(oC)', '(mm)', '(mm)',
        '(kPa)', '(hours)' ] )

    # dump met file with Windows line endings
    if filepath:
        metfile = open( filepath, 'w' )
        metfile.write( '[weather.met.weather]\r\n' )
        metfile.write( 'stateionname = Daymet weather\r\n')
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

def Create_Met_Files(
    wth_df,
    spinup_data ):
    attributes = [ 'dayl','prcp', 'srad','swe', 'tmax','tmin','vp' ]
    leap_years = [ yr for yr in range( 1980, 2020, 4 ) ]

    # get spinup data from Daymet
    spup_start = spinup_data[ 'init_yr' ]
    spup_end = spinup_data[ 'end_yr' ]
    year_arr = [ str( spup_start + i ) for i in
        range( spup_end - spup_start + 1 ) ]
    payload = {
        'lat': spinup_data[ 'lat' ],
        'lon': spinup_data[ 'lon' ],
        'vars': ','.join( attributes ),
        'years': ','.join( year_arr )
    }
    req = requests.get( DAYMET_URL, params = payload )
    spup_df = pd.read_csv( io.StringIO( req.text ), sep = ',', header = 6 )

    # get weather sample id
    wth_id = wth_df[ 'weather_sample_id' ].values[0]
    print( wth_id )

    # rename columns for merge with design weather
    renames = {
        'dayl (s)': 'dayl',
        'prcp (mm/day)': 'prcp',
        'srad (W/m^2)': 'srad',
        'swe (kg/m^2)': 'swe',
        'tmax (deg c)': 'tmax',
        'tmin (deg c)': 'tmin',
        'vp (Pa)': 'vp'
    }
    spup_df = spup_df.rename( columns = renames )

    wth_df = wth_df.drop( columns = [ 'weather_sample_id', 'f1' ], axis = 1 )
    wth_df = spup_df.append( wth_df, sort = False )

    print( wth_df )

    # create APSIM weather dataframe and dump to .met
    df = pd.DataFrame()
    df[ 'year' ] = wth_df[ 'year' ]
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

    # clear original dataframe from memory
    wth_df = None

    # check for leap years
    for lp_yr in leap_years:
        lp_day = df.loc[ ( df[ 'year' ] == lp_yr ) &
            ( df[ 'day' ] == 365 ) ].copy( deep = True )
        lp_day[ 'day' ] = 366
        lp_day[ 'yday' ] = 366

        df = df.append( lp_day, ignore_index = True, sort = False )

    df = df.sort_values( by = [ 'year', 'day' ] )

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

    headers = ' '.join( [ 'year', 'day', 'radn', 'maxt', 'mint', 'rain', 'snow', 'vp', 'dayL' ] )
    units = ' '.join( [ '()', '()', '(MJ/m^2)', '(oC)', '(oC)', '(mm)', '(mm)', '(kPa)', '(hours)' ] )

    filepath = 'apsim_files/met_files/weather_sample_{}.met'.format( wth_id )

    metfile = open( filepath, 'w' )
    metfile.write( '[weather.met.weather]\r\n' )
    metfile.write( 'stateionname = Foresite generated weather\r\n')
    metfile.write( ( 'latitude = {} (DECIMAL DEGREES)\r\n' ).format( spinup_data[ 'lat' ] ) )
    metfile.write( ( 'longitude = {} (DECIMAL DEGREES)\r\n' ).format( spinup_data[ 'lon' ] ) )
    metfile.write( 'tav = ' + str( round( df[ 'maxt' ].mean(), 1 ) ) + '\r\n' )
    metfile.write( 'amp = ' + str( round( df[ 'maxt' ].max(), 1 ) ) + '\r\n' )
    metfile.write( '!Weather generated using ISU Foresite framework\r\n')
    metfile.write( headers + '\r\n' )
    metfile.write( units + '\r\n' )
    metfile.write( df.to_csv( sep = ' ', header = False, index = False,
        line_terminator='\r\n' ) )
    metfile.close()

    return df
