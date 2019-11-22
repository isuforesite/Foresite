#!/usr/bin/env Python

from xml.etree.ElementTree import ElementTree, Element, SubElement
import pandas as pd
import math

###
APSIM_Soil_Layers = [
    ( 0.0, 2.0 ),
    ( 2.0, 4.0 ),
    ( 4.0, 6.0 ),
    ( 6.0, 8.0 ),
    ( 8.0, 10.0 ),
    ( 10.0, 15.0 ),
    ( 15.0, 20.0 ),
    ( 20.0, 25.0 ),
    ( 25.0, 30.0 ),
    ( 30.0, 35.0 ),
    ( 35.0, 40.0 ),
    ( 40.0, 50.0 ),
    ( 50.0, 75.0 ),
    ( 75.0, 100.0 ),
    ( 100.0, 150.0 ),
    ( 150.0, 200.0 )
]

###
def Get_SSURGO_Soils_Data( mukeys, db_conn ):
    mukeystr = ','.join( mukeys )
    query = (
        '''select
            *
        from api.get_soil_properties( \'{''' + mukeystr + '}\'::text[] )' )
    soils_df = pd.read_sql( query, db_conn )

    return soils_df

###
def Create_Layer_XML( parent, name, eqn ):
    for lyr in APSIM_Soil_Layers:
        subelem = SubElement( parent, name )
        subelem.text = str( eqn( lyr ) )
    return

###
def Get_Depth_Weighted( lyr, var, horizon_df, ssurgo = True ):
    apsim_top = lyr[0]
    apsim_bttm = lyr[1]
    for idx, hrzn in horizon_df.iterrows():
        if ssurgo:
            hzdept = hrzn['hzdept']
            hzdepb = hrzn['hzdepb']
        else:
            hzdept = float( hrzn['layer'] ) - 20
            hzdepb = float( hrzn['layer'] )

        if ( ( apsim_top <= hzdept ) & ( apsim_bttm > hzdept ) ):
            wgt = ( apsim_bttm - hzdept )/( apsim_bttm - apsim_top )
        elif ( ( apsim_top < hzdepb ) & ( apsim_bttm >= hzdepb ) ):
            wgt = ( hzdepb - apsim_top )/( apsim_bttm - apsim_top )
        elif ( ( apsim_top <= hzdept ) & ( apsim_bttm >= hzdepb ) ):
            wgt = ( hzdepb - hzdept )/( apsim_bttm - apsim_top )
        elif ( ( apsim_top > hzdept ) & ( apsim_bttm < hzdepb ) ):
            wgt = 1.0
        else:
            wgt = 0.0

        value = float( hrzn[ var ] )

        horizon_df.loc[ idx, 'wgt' ] = wgt
        horizon_df.loc[ idx, 'wgt_var' ] = wgt * value

    if horizon_df[ 'wgt' ].sum() != 1.0:
        value = float( hrzn[ var ] )
    else:
        value = horizon_df[ 'wgt_var' ].sum()

    return value

###
def Add_Soil_Crop( crop, hrzn_df, ssurgo = True ):
    soil_crp = Element( 'SoilCrop' )
    soil_crp.set( 'name', crop )
    sc_thickness = SubElement( soil_crp, 'Thickness' )
    for lyr in APSIM_Soil_Layers:
        subelem = SubElement( sc_thickness, 'double' )
        subelem.text = str( 10 * ( lyr[1] - lyr[0] ) )

    sc_ll = SubElement( soil_crp, 'LL' )
    for lyr in APSIM_Soil_Layers:
        val = Get_Depth_Weighted( lyr, 'wfifteenbar_r', hrzn_df, ssurgo )
        subelem = SubElement( sc_ll, 'double' )
        subelem.text = str( round( 0.01 * val, 3 ) )

    sc_kl = SubElement( soil_crp, 'KL' )
    for lyr in APSIM_Soil_Layers:
        val = 0.08 * math.exp( -0.00654 * lyr[0] )
        subelem = SubElement( sc_kl, 'double' )
        subelem.text = str( round( val, 3 ) )

    sc_xf = SubElement( soil_crp, 'XF' )
    for lyr in APSIM_Soil_Layers:
        val = 1.0
        subelem = SubElement( sc_xf, 'double' )
        subelem.text = str( round( val, 3 ) )

    return soil_crp

###
def Create_SSURGO_Soil_XML( hrzn_df ):
    # base specs
    muname = hrzn_df[ 'muname' ][0]
    texture = hrzn_df[ 'texdesc' ][0]
    mukey = hrzn_df[ 'mukey' ][0]
    musym = hrzn_df[ 'musym' ][0]
    cokey = hrzn_df[ 'cokey' ][0]
    area_sym = hrzn_df[ 'areasymbol' ][0]

    soil_xml = Element( 'Soil' )
    soil_xml.set( 'name', muname )
    rec_id = SubElement( soil_xml, 'RecordNumber' )
    rec_id.text = mukey
    lname = SubElement( soil_xml, 'LocalName' )
    lname.text = '_'.join( [ str( musym ), str( mukey ), str( cokey ) ] )
    site = SubElement( soil_xml, 'Site' )
    site.text = area_sym
    region = SubElement( soil_xml, 'Region' )
    region.text = area_sym
    state = SubElement( soil_xml, 'State' )
    state.text = area_sym[2:]
    cntry = SubElement( soil_xml, 'Country' )
    cntry.text = 'U.S.'
    lat = SubElement( soil_xml, 'Latitude' )
    lat.text = ''
    lon = SubElement( soil_xml, 'Longitude' )
    lon.text = ''
    sample_yr = SubElement( soil_xml, 'YearOfSampling' )
    sample_yr.text = '2019'
    datasrc = SubElement( soil_xml, 'DataSource' )
    datasrc.text = 'SSURGO 2019'
    comment = SubElement( soil_xml, 'Comment' )
    comment.text = 'Iowa State University Foresite Framework'
    water = SubElement( soil_xml, 'Water' )

    hrzn_df.loc[ hrzn_df.index[-1], 'hzdepb'] = APSIM_Soil_Layers[-1][1]

    ### layer thickness
    thickness = SubElement( water, 'Thickness' )
    for lyr in APSIM_Soil_Layers:
        subelem = SubElement( thickness, 'double' )
        subelem.text = str( 10 * ( lyr[1] - lyr[0] ) )

    ### bulk density
    bulk_dens = SubElement( water, 'BD' )
    for lyr in APSIM_Soil_Layers:
        value = Get_Depth_Weighted( lyr, 'dbthirdbar', hrzn_df )
        subelem = SubElement( bulk_dens, 'double' )
        subelem.text = str( round( value, 3 ) )

    ### air dry
    air_dry = SubElement( water, 'AirDry' )
    for lyr in APSIM_Soil_Layers:
        if lyr[0] <= 15.0 & lyr[0] > 0.0:
            value = Get_Depth_Weighted( lyr, 'wfifteenbar', hrzn_df )
            value = 0.01 * value * 0.5
        elif lyr[0] <= 30.0 & lyr[0] > 15.0:
            value = Get_Depth_Weighted( lyr, 'wfifteenbar', hrzn_df )
            value = 0.01 * value * 0.75
        else:
            value = 0.01 * Get_Depth_Weighted( lyr, 'wfifteenbar', hrzn_df )
        subelem = SubElement( air_dry, 'double' )
        subelem.text = str( round( value, 3 ) )

    ### lower limit (wilting pt.)
    ll15 = SubElement( water, 'LL15' )
    for lyr in APSIM_Soil_Layers:
        value = Get_Depth_Weighted( lyr, 'wfifteenbar', hrzn_df )
        value = value * 0.01
        subelem = SubElement( air_dry, 'double' )
        subelem.text = str( round( value, 3 ) )

    ### drained upper limit (field cap.)
    dul = SubElement( water, 'DUL' )
    for lyr in APSIM_Soil_Layers:
        value = Get_Depth_Weighted( lyr, 'wthirdbar', hrzn_df )
        value = value * 0.01
        subelem = SubElement( dul, 'double' )
        subelem.text = str( round( value, 3 ) )

    ### saturated water holding capacity
    sat = SubElement( water, 'SAT' )
    for lyr in APSIM_Soil_Layers:
        value = Get_Depth_Weighted( lyr, 'dbthirdbar', hrzn_df )
        value = 1 - ( value/2.65 )
        subelem = SubElement( sat, 'double' )
        subelem.text = str( round( value, 3 ) )

    ### saturated hydraulic conductivity
    ks = SubElement( water, 'KS' )
    for lyr in APSIM_Soil_Layers:
        value = Get_Depth_Weighted( lyr, 'ksat', hrzn_df )
        value = 0.001 * 3600 * 24 * value
        subelem = SubElement( ks, 'double' )
        subelem.text = str( round( value, 3 ) )

    ### initialize crop-soil params
    water.append( Add_Soil_Crop( 'maize', hrzn_df ) )
    water.append( Add_Soil_Crop( 'soybean', hrzn_df ) )

    ### get ave clay in profile
    tot_clay = 0.0
    for lyr in APSIM_Soil_Layers:
        depth = lyr[1] - lyr[0]
        tot_clay += depth * Get_Depth_Weighted( lyr, 'claytotal', hrzn_df )
    tot_clay = tot_clay/APSIM_Soil_Layers[-1][1]

    clay_bckts = [
        [ ( 0, 10 ), 6.75, 3.5 ],
        [ ( 10, 20 ), 8.5, 3.75 ],
        [ ( 20, 30 ), 9.0, 4.0 ],
        [ ( 30, 40 ), 9.5, 4.0 ],
        [ ( 40, 50 ), 9, 4.0 ],
        [ ( 50, 60 ), 8.25, 3.75 ],
        [ ( 60, 70 ), 6.75, 3.5 ],
        [ ( 70, 100 ), 6.75, 3.5] ]

    for cb in clay_bckts:
        if ( ( cb[0][0] <= tot_clay ) & ( cb[0][1] > tot_clay ) ):
            u = cb[1]
    u = [ cb[1] for cb in clay_bckts
    if ( ( cb[0][0] <= tot_clay ) & ( cb[0][1] > tot_clay ) ) ][0]

    cona = [ cb[2] for cb in clay_bckts
    if ( ( cb[0][0] <= tot_clay ) & ( cb[0][1] > tot_clay ) ) ][0]

    """ soil_wat = SubElement( soil_xml, 'SoilWater' )
    sum_cona = SubElement( soil_wat, 'SummerCona' )
    sum_cona.text = str( cona )
    sum_u = SubElement( soil_wat, 'SummerU' )
    sum_u.text = str( u )
    sum_date = SubElement( soil_wat, 'SummerDate' )
    sum_date.text = '1-Jun'
    win_cona = SubElement( soil_wat, 'SummerCona' )
    win_cona.text = str( cona )
    win_u = SubElement( soil_wat, 'SummerU' )
    win_u.text = str( u )
    win_date = SubElement( soil_wat, 'WinterDate' )
    win_date.text = '1-Dec'
    diff_const = SubElement( soil_wat, 'DiffusConst' )
    diff_const.text = str( 40 )
    diff_slope = SubElement( soil_wat, 'DiffusSlope' )
    diff_slope.text = str( 16 )
    salb = SubElement( soil_wat, 'Salb' )
    salb.text = str( 0.12 )
    cn2bare = SubElement( soil_wat, 'CN2Bare' )
    cn2bare.text = str( 65 )
    cnred = SubElement( soil_wat, 'CNRed' )
    cnred.text = str( 20 )
    cncov = SubElement( soil_wat, 'CNCov' )
    cncov.text = str( 0.8 )
    slope = SubElement( soil_wat, 'Slope' )
    slope.text = 'NaN'
    diswidth = SubElement( soil_wat, 'DischargeWidth' )
    diswidth.text = 'NaN'
    catch_area = SubElement( soil_wat, 'CatchmentArea' )
    catch_area.text = 'NaN'
    max_pond = SubElement( soil_wat, 'MaxPond' )
    max_pond.text = 'NaN'

    ### layer thickness
    thickness = SubElement( soil_wat, 'Thickness' )
    for lyr in APSIM_Soil_Layers:
        subelem = SubElement( thickness, 'double' )
        subelem.text = str( 10 * ( lyr[1] - lyr[0] ) )

    ###
    swcon = SubElement( soil_wat, 'SWCON' )
    for lyr in APSIM_Soil_Layers:
        subelem = SubElement( swcon, 'double' )
        subelem.text = str( 10 * ( lyr[1] - lyr[0] ) ) """

    ###
    som = SubElement( soil_xml, 'SoilOrganicMatter' )
    rootcn = SubElement( som, 'RootCN' )
    rootcn.text = str( 40 )
    rootwt = SubElement( som, 'RootWt' )
    rootwt.text = str( 1200 )
    soilcn = SubElement( som, 'SoilCN' )
    soilcn.text = str( 12 )
    enracoeff = SubElement( som, 'EnrACoeff' )
    enracoeff.text = str( 7.4 )
    enrbcoeff = SubElement( som, 'EnrBCoeff' )
    enrbcoeff.text = str( 7.4 )

    ### soil organic carbon
    oc = SubElement( som, 'OC' )
    for lyr in APSIM_Soil_Layers:
        value = Get_Depth_Weighted( lyr, 'om', hrzn_df )
        print( value )
        value = value/1.724
        subelem = SubElement( oc, 'double' )
        subelem.text = str( round( value, 3 ) )

    ###
    fbiom = SubElement( som, 'FBiom' )
    depth_bckts = [
        [ ( 0, 15 ), 0.35 ],
        [ ( 15, 30 ), 0.21 ],
        [ ( 30, 60 ), 0.13 ],
        [ ( 60, 1000 ), 0.1 ] ]
    for lyr in APSIM_Soil_Layers:
        value = [ db[0] for db in depth_bckts
            if ( ( db[0][0] <= lyr[1] ) & ( db[0][1] > lyr[1] ) ) ][0]
        subelem = SubElement( fbiom, 'double' )
        subelem.text = str( round( value, 3 ) )

    finert = SubElement( som, 'FInert' )
    depth_bckts = [
        [ ( 0, 15 ), 0.40 ],
        [ ( 15, 30 ), 0.48 ],
        [ ( 30, 60 ), 0.68 ],
        [ ( 60, 90 ), 0.80 ],
        [ ( 90, 120 ), 0.80 ],
        [ ( 120, 1000 ), 0.9 ] ]
    for lyr in APSIM_Soil_Layers:
        value = [ db[0] for db in depth_bckts
            if ( ( db[0][0] <= lyr[1] ) & ( db[0][1] > lyr[1] ) ) ][0]
        subelem = SubElement( finert, 'double' )
        subelem.text = str( round( value, 3 ) )

    ###
    oc_units = SubElement( som, 'OCUnits' )
    oc_units.text = 'Total'

    anlys = SubElement( soil_xml, 'Analysis' )
    thickness = SubElement( anlys, 'Thickness' )
    for lyr in APSIM_Soil_Layers:
        subelem = SubElement( thickness, 'double' )
        subelem.text = str( 10 * ( lyr[1] - lyr[0] ) )

    txtr = SubElement( anlys, 'Texture' )
    for lyr in APSIM_Soil_Layers:
        subelem = SubElement( txtr, 'string' )

    mcolor = SubElement( anlys, 'MunsellColour' )
    for lyr in APSIM_Soil_Layers:
        subelem = SubElement( mcolor, 'string' )

    ph = SubElement( anlys, 'PH' )
    for lyr in APSIM_Soil_Layers:
        value = Get_Depth_Weighted( lyr, 'ph1to1h2o', hrzn_df )
        subelem = SubElement( ph, 'double' )
        subelem.text = str( round( value, 3 ) )

    phunits = SubElement( anlys, 'PHUnits' )
    phunits.text = 'Water'
    boronunits = SubElement( anlys, 'BoronUnits' )
    boronunits.text = 'HotWater'
    init_h2o = SubElement( soil_xml, 'InitialWater' )
    fracfull = SubElement( init_h2o, 'FractionFull' )
    fracfull.text = str( 1 )
    depthwet = SubElement( init_h2o, 'DepthWetSoil' )
    depthwet.text = str( 'NaN' )
    percmethod = SubElement( init_h2o, 'PercentMethod' )
    percmethod.text = 'FilledFromTop'

    sample = SubElement( soil_xml, 'Sample' )
    sample.set( 'name', 'Initial nitrogen' )

    thickness = SubElement( sample, 'Thickness' )
    for lyr in APSIM_Soil_Layers:
        subelem = SubElement( thickness, 'double' )
        subelem.text = str( 10 * ( lyr[1] - lyr[0] ) )

    ### init no3
    no3 = SubElement( sample, 'NO3' )
    lyr_cnt = 0
    for lyr in APSIM_Soil_Layers:
        subelem = SubElement( no3, 'double' )
        subelem.text = str( 10 - lyr_cnt )
        lyr_cnt += 1

    ### init nh4
    nh4 = SubElement( sample, 'NH4' )
    lyr_cnt = 0
    for lyr in APSIM_Soil_Layers:
        subelem = SubElement( nh4, 'double' )
        subelem.text = str( 10 - lyr_cnt )
        lyr_cnt += 1

    no3_units = SubElement( sample, 'NO3Units' )
    no3_units.text = 'kgha'
    nh4_units = SubElement( sample, 'NH4Units' )
    nh4_units.text = 'kgha'
    sw_units = SubElement( sample, 'SWUnits' )
    sw_units.text = 'Volumetric'
    oc_units = SubElement( sample, 'OCUnits' )
    oc_units.text = 'Total'
    ph_units = SubElement( sample, 'PHUnits' )
    ph_units.text = 'Water'

    xmltree = ElementTree( soil_xml )
    xmltree.write( mukey + '.apsim' )

    return soil_xml

###
def Create_Soil_XML( uuid, soil_df ):
    # base specs
    soil_sample_id = soil_df.iloc[0][ 'soil_sample_id' ]

    soil_xml = Element( 'Soil' )
    initwater = SubElement( soil_xml, 'InitialWater' )
    initwater.set( 'name', 'Initial Water' )
    fracfull = SubElement( initwater, 'FractionFull' )
    fracfull.text = str( 1 )
    percmethod = SubElement( initwater, 'PercentMethod' )
    percmethod.text = 'FilledFromTop'
    water = SubElement( soil_xml, 'Water' )
    water.append( Add_Soil_Crop( 'maize', soil_df, False ) )
    water.append( Add_Soil_Crop( 'soybean', soil_df, False ) )

    ### layer thickness
    thickness = SubElement( water, 'Thickness' )
    for lyr in APSIM_Soil_Layers:
        subelem = SubElement( thickness, 'double' )
        subelem.text = str( 10 * ( lyr[1] - lyr[0] ) )

    ### bulk density
    bulk_dens = SubElement( water, 'BD' )
    for lyr in APSIM_Soil_Layers:
        value = Get_Depth_Weighted( lyr, 'dbthirdbar_r', soil_df, False )
        subelem = SubElement( bulk_dens, 'double' )
        subelem.text = str( round( value, 3 ) )

    ### air dry
    air_dry = SubElement( water, 'AirDry' )
    for lyr in APSIM_Soil_Layers:
        value = Get_Depth_Weighted( lyr, 'wfifteenbar_r', soil_df, False )
        if ( lyr[0] <= 15.0 ) & ( lyr[0] > 0.0 ):
            value = value * 0.5 * 0.01
        elif ( lyr[0] <= 30.0 ) & ( lyr[0] > 15.0 ):
            value = value * 0.75 * 0.01
        else:
            value = value * 0.01
        subelem = SubElement( air_dry, 'double' )
        subelem.text = str( round( value, 3 ) )

    ### lower limit (wilting pt.)
    ll15 = SubElement( water, 'LL15' )
    for lyr in APSIM_Soil_Layers:
        value = Get_Depth_Weighted( lyr, 'wfifteenbar_r', soil_df, False )
        value = value * 0.01
        subelem = SubElement( ll15, 'double' )
        subelem.text = str( round( value, 3 ) )

    ### drained upper limit (field cap.)
    dul = SubElement( water, 'DUL' )
    for lyr in APSIM_Soil_Layers:
        value = Get_Depth_Weighted( lyr, 'wthirdbar_r', soil_df, False)
        value = value * 0.01
        subelem = SubElement( dul, 'double' )
        subelem.text = str( round( value, 3 ) )

    ### saturated water holding capacity
    sat = SubElement( water, 'SAT' )
    for lyr in APSIM_Soil_Layers:
        value = Get_Depth_Weighted( lyr, 'dbthirdbar_r', soil_df, False )
        value = 1 - ( value/2.65 )
        subelem = SubElement( sat, 'double' )
        subelem.text = str( round( value, 3 ) )

    ### saturated hydraulic conductivity
    ks = SubElement( water, 'KS' )
    for lyr in APSIM_Soil_Layers:
        value = Get_Depth_Weighted( lyr, 'ksat_r', soil_df, False )
        value = 0.001 * 3600 * 24 * value
        subelem = SubElement( ks, 'double' )
        subelem.text = str( round( value, 3 ) )

    ### get ave clay in profile
    tot_clay = 0.0
    for lyr in APSIM_Soil_Layers:
        depth = lyr[1] - lyr[0]
        tot_clay += depth * Get_Depth_Weighted( lyr, 'claytotal_r', soil_df, False )
    tot_clay = tot_clay/APSIM_Soil_Layers[-1][1]

    clay_bckts = [
        [ ( 0, 10 ), 6.75, 3.5 ],
        [ ( 10, 20 ), 8.5, 3.75 ],
        [ ( 20, 30 ), 9.0, 4.0 ],
        [ ( 30, 40 ), 9.5, 4.0 ],
        [ ( 40, 50 ), 9, 4.0 ],
        [ ( 50, 60 ), 8.25, 3.75 ],
        [ ( 60, 70 ), 6.75, 3.5 ],
        [ ( 70, 100 ), 6.75, 3.5] ]

    for cb in clay_bckts:
        if ( ( cb[0][0] <= tot_clay ) & ( cb[0][1] > tot_clay ) ):
            u = cb[1]
    u = [ cb[1] for cb in clay_bckts
    if ( ( cb[0][0] <= tot_clay ) & ( cb[0][1] > tot_clay ) ) ][0]

    cona = [ cb[2] for cb in clay_bckts
    if ( ( cb[0][0] <= tot_clay ) & ( cb[0][1] > tot_clay ) ) ][0]

    """ soil_wat = SubElement( soil_xml, 'SoilWater' )
    sum_cona = SubElement( soil_wat, 'SummerCona' )
    sum_cona.text = str( cona )
    sum_u = SubElement( soil_wat, 'SummerU' )
    sum_u.text = str( u )
    sum_date = SubElement( soil_wat, 'SummerDate' )
    sum_date.text = '1-Jun'
    win_cona = SubElement( soil_wat, 'WinterCona' )
    win_cona.text = str( cona )
    win_u = SubElement( soil_wat, 'WinterU' )
    win_u.text = str( u )
    win_date = SubElement( soil_wat, 'WinterDate' )
    win_date.text = '1-Dec'
    diff_const = SubElement( soil_wat, 'DiffusConst' )
    diff_const.text = str( 40 )
    diff_slope = SubElement( soil_wat, 'DiffusSlope' )
    diff_slope.text = str( 16 )
    salb = SubElement( soil_wat, 'Salb' )
    salb.text = str( 0.12 )
    cn2bare = SubElement( soil_wat, 'CN2Bare' )
    cn2bare.text = str( 65 )
    cnred = SubElement( soil_wat, 'CNRed' )
    cnred.text = str( 20 )
    cncov = SubElement( soil_wat, 'CNCov' )
    cncov.text = str( 0.8 )

    ### layer thickness
    thickness = SubElement( soil_wat, 'Thickness' )
    for lyr in APSIM_Soil_Layers:
        subelem = SubElement( thickness, 'double' )
        subelem.text = str( 10 * ( lyr[1] - lyr[0] ) )

    ###
    swcon = SubElement( soil_wat, 'SWCON' )
    for lyr in APSIM_Soil_Layers:
        subelem = SubElement( swcon, 'double' )
        subelem.text = str( 0.5 ) """
    
    ###SWIM for tile drainage and NO3 leaching
    swim = SubElement(soil_xml, 'Swim')
    salb = SubElement(swim, 'Salb').text = str(0.13)
    cn2bare = SubElement(swim, 'CN2Bare').text = str(75)
    cnred = SubElement(swim, 'CNRed').text = str(20)
    cncov = SubElement(swim, 'CNCov').text = str(0.8)
    kdul = SubElement(swim, 'KDul').text = str(0.1)
    psidul = SubElement(swim, 'PSIDul').text = str(-100)
    vc = SubElement(swim, 'VC').text = 'true'
    dtmin = SubElement(swim, 'DTmin').text = str(0)
    dtmax = SubElement(swim, 'DTmax').text = str(1440)
    maxwater = SubElement(swim, 'MaxWaterIncrement').text = str(10)
    spaceweight = SubElement(swim, 'SpaceWeightingFactor').text = str(0)
    solutespace = SubElement(swim, 'SoluteSpaceWeightingFactor').text = str(0)
    diagnostics = SubElement(swim, 'Diagnostics').text = 'true'
    soluteparms = SubElement(swim, 'SwimSoluteParameters')
    dis = SubElement(soluteparms, 'Dis').text = str(15)
    disp = SubElement(soluteparms, 'Disp').text = str(1)
    sp_a = SubElement(soluteparms, 'A').text = str(1)
    dthc = SubElement(soluteparms, 'DTHC').text = str(1)
    dthp = SubElement(soluteparms, 'DTHP').text = str(1)
    wattabcl = SubElement(soluteparms, 'WaterTableCl').text = str(0)
    wattabno3 = SubElement(soluteparms, 'WaterTableNO3').text = str(0)
    wattabnh4 = SubElement(soluteparms, 'WaterTableNH4').text = str(0)
    wattaburea = SubElement(soluteparms, 'WaterTableUrea').text = str(0)
    wattabtracer = SubElement(soluteparms, 'WaterTableTracer').text = str(0)
    mininhib = SubElement(soluteparms, 'WaterTableMineralisationInhibitor').text = str(0)
    ureainhib = SubElement(soluteparms, 'WaterTableUreaseInhibitor').text = str(0)
    nitrifinhib = SubElement(soluteparms, 'WaterTableNitrificationInhibitor').text = str(0)
    denitrifinhib = SubElement(soluteparms, 'WaterTableDenitrificationInhibitor').text = str(0)
    thickness = SubElement(soluteparms, 'Thickness')
    double = SubElement(thickness, 'double').text = str(1000)
    double = SubElement(thickness, 'double').text = str(1000)
    double = SubElement(thickness, 'double').text = str(1000)
    no3exco = SubElement(soluteparms, 'NO3Exco')
    double = SubElement(no3exco, 'double').text = str(0)
    double = SubElement(no3exco, 'double').text = str(0)
    double = SubElement(no3exco, 'double').text = str(0)
    no3fip = SubElement(soluteparms, 'NO3FIP')
    double = SubElement(no3fip, 'double').text = str(1)
    double = SubElement(no3fip, 'double').text = str(1)
    double = SubElement(no3fip, 'double').text = str(1)
    nh4exco = SubElement(soluteparms, 'NH4Exco')
    double = SubElement(nh4exco, 'double').text = str(100)
    double = SubElement(nh4exco, 'double').text = str(100)
    double = SubElement(nh4exco, 'double').text = str(100)
    nh4fip = SubElement(soluteparms, 'NH4FIP')
    double = SubElement(nh4fip, 'double').text = str(1)
    double = SubElement(nh4fip, 'double').text = str(1)
    double = SubElement(nh4fip, 'double').text = str(1)
    ureaexco = SubElement(soluteparms, 'UreaExco')        
    double = SubElement(ureaexco, 'double').text = str(0)
    double = SubElement(ureaexco, 'double').text = str(0)
    double = SubElement(ureaexco, 'double').text = str(0)
    ureafip = SubElement(soluteparms, 'UreaFIP')
    double = SubElement(ureafip, 'double').text = str(1)
    double = SubElement(ureafip, 'double').text = str(1)
    double = SubElement(ureafip, 'double').text = str(1)
    clexco = SubElement(soluteparms, 'ClExco')
    double = SubElement(clexco, 'double').text = str(0)
    double = SubElement(clexco, 'double').text = str(0)
    double = SubElement(clexco, 'double').text = str(0)
    clfip = SubElement(soluteparms, 'ClFIP')
    double = SubElement(clfip, 'double').text = str(1)
    double = SubElement(clfip, 'double').text = str(1)
    double = SubElement(clfip, 'double').text = str(1)     
    swimwtab = SubElement(swim, 'SwimWaterTable')
    wattabdep = SubElement(swimwtab, 'WaterTableDepth').text = str(2000)
    subdrain = SubElement(swim, 'SwimSubsurfaceDrain')
    draindepth = SubElement(subdrain, 'DrainDepth').text = str(1100)
    drainspacing = SubElement(subdrain, 'DrainSpacing').text = str(13500)
    #using a drain radius for 4 inch tile
    drainradius = SubElement(subdrain, 'DrainRadius').text = str(52)
    klat = SubElement(subdrain, 'Klat').text = str(2800)
    impermdepth = SubElement(subdrain, 'ImpermDepth').text = str(3900)

    ###
    som = SubElement( soil_xml, 'SoilOrganicMatter' )
    rootcn = SubElement( som, 'RootCN' )
    rootcn.text = str( 40 )
    rootwt = SubElement( som, 'RootWt' )
    rootwt.text = str( 1200 )
    soilcn = SubElement( som, 'SoilCN' )
    soilcn.text = str( 12 )
    enracoeff = SubElement( som, 'EnrACoeff' )
    enracoeff.text = str( 7.4 )
    enrbcoeff = SubElement( som, 'EnrBCoeff' )
    enrbcoeff.text = str( 7.4 )

    thickness = SubElement( som, 'Thickness' )
    for lyr in APSIM_Soil_Layers:
        subelem = SubElement( thickness, 'double' )
        subelem.text = str( 10 * ( lyr[1] - lyr[0] ) )

    ### soil organic carbon
    oc = SubElement( som, 'OC' )
    for lyr in APSIM_Soil_Layers:
        value = Get_Depth_Weighted( lyr, 'om_r', soil_df, False )
        value = value/1.724
        if value == 0.0:
            value = 0.1
        subelem = SubElement( oc, 'double' )
        subelem.text = str( round( value, 3 ) )

    ###
    fbiom = SubElement( som, 'FBiom' )
    depth_bckts = [
        [ ( 0, 15 ), 0.35 ],
        [ ( 15, 30 ), 0.21 ],
        [ ( 30, 60 ), 0.13 ],
        [ ( 60, 1000 ), 0.1 ] ]
    for lyr in APSIM_Soil_Layers:
        value = [ db[1] for db in depth_bckts
            if ( ( db[0][0] <= lyr[1] ) & ( db[0][1] > lyr[1] ) ) ][0]
        subelem = SubElement( fbiom, 'double' )
        subelem.text = str( round( value, 3 ) )

    finert = SubElement( som, 'FInert' )
    depth_bckts = [
        [ ( 0, 15 ), 0.40 ],
        [ ( 15, 30 ), 0.48 ],
        [ ( 30, 60 ), 0.68 ],
        [ ( 60, 90 ), 0.80 ],
        [ ( 90, 120 ), 0.80 ],
        [ ( 120, 1000 ), 0.9 ] ]
    for lyr in APSIM_Soil_Layers:
        value = [ db[1] for db in depth_bckts
            if ( ( db[0][0] <= lyr[1] ) & ( db[0][1] > lyr[1] ) ) ][0]
        subelem = SubElement( finert, 'double' )
        subelem.text = str( round( value, 3 ) )

    anlys = SubElement( soil_xml, 'Analysis' )
    thickness = SubElement( anlys, 'Thickness' )
    for lyr in APSIM_Soil_Layers:
        subelem = SubElement( thickness, 'double' )
        subelem.text = str( 10 * ( lyr[1] - lyr[0] ) )

    ph = SubElement( anlys, 'PH' )
    for lyr in APSIM_Soil_Layers:
        value = Get_Depth_Weighted( lyr, 'ph1to1h2o_r', soil_df, False )
        subelem = SubElement( ph, 'double' )
        subelem.text = str( round( value, 3 ) )

    sample = SubElement( soil_xml, 'Sample' )
    sample.set( 'name', 'Initial nitrogen' )

    sampdate = SubElement( sample, 'Date' )
    sampdate.set( 'type', 'date' )
    sampdate.set( 'description', 'Sample Date:' )

    thickness = SubElement( sample, 'Thickness' )
    for lyr in APSIM_Soil_Layers:
        subelem = SubElement( thickness, 'double' )
        subelem.text = str( 10 * ( lyr[1] - lyr[0] ) )

    ### init no3
    no3 = SubElement( sample, 'NO3' )
    lyr_cnt = 0
    for lyr in APSIM_Soil_Layers:
        subelem = SubElement( no3, 'double' )
        subelem.text = str( 0.0 )
        lyr_cnt += 1

    ### init nh4
    nh4 = SubElement( sample, 'NH4' )
    lyr_cnt = 0
    for lyr in APSIM_Soil_Layers:
        subelem = SubElement( nh4, 'double' )
        subelem.text = str( 0.0 )
        lyr_cnt += 1

    return soil_xml
