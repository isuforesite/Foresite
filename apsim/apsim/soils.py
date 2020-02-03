#!/usr/bin/env Python

from xml.etree.ElementTree import ElementTree, Element, SubElement
import pandas as pd
import numpy as np

###
APSIM_Soil_Layers = [
    { 'min': 0.0, 'max': 2.0 },
    { 'min': 2.0, 'max': 4.0 },
    { 'min': 4.0, 'max': 6.0 },
    { 'min': 6.0, 'max': 8.0 },
    { 'min': 8.0, 'max': 10.0 },
    { 'min': 10.0, 'max': 15.0 },
    { 'min': 15.0, 'max': 20.0 },
    { 'min': 20.0, 'max': 25.0 },
    { 'min': 25.0, 'max': 30.0 },
    { 'min': 30.0, 'max': 35.0 },
    { 'min': 35.0, 'max': 40.0 },
    { 'min': 40.0, 'max': 50.0 },
    { 'min': 50.0, 'max': 75.0 },
    { 'min': 75.0, 'max': 100.0 },
    { 'min': 100.0, 'max': 150.0 },
    { 'min': 150.0, 'max': 200.0 }
]

###
def get_depth_weighted_value( apsim_lyr, var, layers ):
    apsim_top = apsim_lyr[ 'min' ]
    apsim_bttm = apsim_lyr[ 'max' ]
    lyrs = layers.copy( deep = True )
    for idx, lyr in lyrs.iterrows():
        top = lyr[ 'hzdept_r' ]
        bttm = lyr[ 'hzdepb_r' ]
        if ( ( apsim_top <= top ) & ( apsim_bttm > top ) ):
            wgt = ( apsim_bttm - top )/( apsim_bttm - apsim_top )
        elif ( ( apsim_top < bttm ) & ( apsim_bttm >= bttm ) ):
            wgt = ( bttm - apsim_top )/( apsim_bttm - apsim_top )
        elif ( ( apsim_top <= top ) & ( apsim_bttm >= bttm ) ):
            wgt = ( bttm - top )/( apsim_bttm - apsim_top )
        elif ( ( apsim_top > top ) & ( apsim_bttm < bttm ) ):
            wgt = 1.0
        else:
            wgt = 0.0
        value = var[ idx ]
        lyrs.loc[ idx, 'wgt' ] = wgt
        lyrs.loc[ idx, 'wgt_var' ] = wgt * value

        wgt_avg = lyrs[ 'wgt_var' ].sum()

    return wgt_avg

###
def add_crop_xml( parent, crop_name, soil ):
    crop_elem = SubElement( parent, 'SoilCrop' )
    crop_elem.set( 'name', crop_name )
    add_subelements( crop_elem, 'Thickness' )

    sc_ll = SubElement( crop_elem, 'LL' )
    for lyr_idx, lyr in enumerate( APSIM_Soil_Layers ):
        if lyr_idx < 4:
            fctr = 0.5
        else:
            fctr = 1.0

        val = get_depth_weighted_value(
            APSIM_Soil_Layers[ lyr_idx ],
            soil.LL15 * fctr,
            soil.Horizons )
        subelem = SubElement( sc_ll, 'double' )
        subelem.text = str( round( val, 3 ) )

    sc_kl = SubElement( crop_elem, 'KL' )
    for lyr in APSIM_Soil_Layers:
        val = 0.08 * np.exp( -0.00654 * lyr[ 'min' ] )
        subelem = SubElement( sc_kl, 'double' )
        subelem.text = str( round( val, 3 ) )

    sc_xf = SubElement( crop_elem, 'XF' )
    for lyr in APSIM_Soil_Layers:
        val = 1.0
        subelem = SubElement( sc_xf, 'double' )
        subelem.text = str( round( val, 3 ) )

    return

###
def add_subelements( parent, child, var = pd.DataFrame(), depths = None ):
    child_elem = SubElement( parent, child )
    for lyr in APSIM_Soil_Layers:
        if var.empty:
            value = 10 * ( lyr[ 'max' ] - lyr[ 'min' ] )
        else:
            value = get_depth_weighted_value( lyr, var, depths )
        dbl_elem = SubElement( child_elem, 'double' )
        dbl_elem.text = str( round( value, 3 ) )

    return

###
def add_subelement( parent, child, value ):
    subelem = SubElement( parent, child )
    subelem.text = str( round( value, 3 ) )

    return subelem

###
def set_value_by_depth( soil_df, var_name, min, max, value, eqn = None ):
    if value != None:
        if max == None:
            soil_df.loc[ ( soil_df[ 'hzdepb_r' ] >= min ), var_name ] = value
        else:
            soil_df.loc[ ( soil_df[ 'hzdept_r' ] >= min ) &
                ( soil_df[ 'hzdept_r' ] < max ), var_name ] = value
    elif eqn != None:
        if max == None:
            soil_df.loc[ ( soil_df[ 'hzdepb_r' ] >= min ), var_name ] = eqn(
                soil_df.loc[ ( soil_df[ 'hzdepb_r' ] >= min ) ] )
        else:
            soil_df.loc[ ( soil_df[ 'hzdept_r' ] >= min ) &
                ( soil_df[ 'hzdept_r' ] < max ), var_name ] = eqn(
                    soil_df.loc[ ( soil_df[ 'hzdept_r' ] >= min ) &
                        ( soil_df[ 'hzdept_r' ] < max ) ] )

    return

###
def calculate_saxton_rawls( soil_df ):
    S = soil_df[ 'sandtotal_r' ] * 0.01
    C = soil_df[ 'claytotal_r' ] * 0.01
    OM = soil_df[ 'om_r' ] * 0.01

    # LL15
    theta_1500t = ( -0.024 * S + 0.487 * C + 0.006 * OM + 0.005 * S * OM
        - 0.013 * C * OM + 0.068 * S * C + 0.031 )
    soil_df[ 'sr_LL15'] = theta_1500t + ( 0.14 * theta_1500t - 0.02 )

    # DUL
    theta_33t = ( -0.251 * S + 0.195 * C + 0.011 * OM + 0.006 * S * OM
        - 0.027 * C * OM + 0.452 * S * C + 0.299 )
    soil_df[ 'sr_DUL' ] = theta_33t + (
        1.283 * theta_33t**2 - 0.374 * theta_33t - 0.015 )

    # SAT
    theta_s33t = ( 0.278 * S + 0.034 * C + 0.022 * OM - 0.018 * S * OM
        - 0.027 * C * OM - 0.584 * S * C + 0.078 )
    theta_s33 = theta_s33t + ( 0.636 * theta_s33t - 0.107 )
    soil_df[ 'sr_SAT' ] = soil_df[ 'sr_DUL' ] + theta_s33 - 0.097 * S + 0.043

    # BD
    soil_df[ 'sr_BD' ] = ( 1 - soil_df[ 'sr_SAT' ] ) * 2.65

    # KS
    B = ( ( np.log( 1500 ) - np.log( 33 ) )/
        ( np.log( soil_df[ 'sr_DUL' ] ) - np.log( soil_df[ 'sr_LL15' ] ) ) )
    ks_lambda = 1/B
    soil_df[ 'sr_KS' ] = ( 1930 * ( soil_df[ 'sr_SAT' ] -
        soil_df[ 'sr_LL15' ] )**( 3 - ks_lambda ) )

    #air dry
    # 0 - 15 cm: 0.01 * 0.5 * wfifteenbar_r
    # 15 - 30 cm: 0.01 * 0.75 * wfifteenbar_r
    # > 30 cm: 0.01 * wfifteenbar_r
    ad_1 = lambda df: df[ 'sr_LL15'] * 0.5 * 0.01
    ad_2 = lambda df: df[ 'sr_LL15'] * 0.75 * 0.01
    ad_3 = lambda df: df[ 'sr_LL15'] * 0.01
    set_value_by_depth( soil_df, 'sr_AirDry', 0.0, 15.0, None, ad_1 )
    set_value_by_depth( soil_df, 'sr_AirDry', 15.0, 30.0, None, ad_2 )
    set_value_by_depth( soil_df, 'sr_AirDry', 30.0, None, None, ad_3 )

    # BD
    soil_df[ 'sr_BD' ] = ( 1 - soil_df[ 'sr_SAT' ] ) * 2.65

    # KS
    B = ( ( np.log( 1500 ) - np.log( 33 ) )/
        ( np.log( soil_df[ 'sr_DUL' ] ) - np.log( soil_df[ 'sr_LL15' ] ) ) )
    ks_lambda = 1/B
    soil_df[ 'sr_KS' ] = ( 1930 * ( soil_df[ 'sr_SAT' ]
        - soil_df[ 'sr_LL15' ] )**( 3 - ks_lambda ) )

    return

###
def get_swim_xml( lyr_cnt = 3 ):
    swim = Element( 'Swim' )
    salb = SubElement(swim, 'Salb').text = str( 0.13 )
    cn2bare = SubElement(swim, 'CN2Bare').text = str( 75 )
    cnred = SubElement(swim, 'CNRed').text = str( 20 )
    cncov = SubElement(swim, 'CNCov').text = str( 0.8 )
    kdul = SubElement(swim, 'KDul').text = str( 0.1 )
    psidul = SubElement(swim, 'PSIDul').text = str( -100 )
    vc = SubElement(swim, 'VC').text = 'true'
    dtmin = SubElement(swim, 'DTmin').text = str( 0 )
    dtmax = SubElement(swim, 'DTmax').text = str( 1440 )
    maxwater = SubElement(swim, 'MaxWaterIncrement').text = str( 10 )
    spaceweight = SubElement(swim, 'SpaceWeightingFactor').text = str( 0 )
    solutespace = SubElement(swim, 'SoluteSpaceWeightingFactor').text = str( 0 )
    diagnostics = SubElement(swim, 'Diagnostics').text = 'true'
    soluteparms = SubElement(swim, 'SwimSoluteParameters')
    dis = SubElement(soluteparms, 'Dis').text = str( 15 )
    disp = SubElement(soluteparms, 'Disp').text = str( 1 )
    sp_a = SubElement(soluteparms, 'A').text = str( 1 )
    dthc = SubElement(soluteparms, 'DTHC').text = str( 1 )
    dthp = SubElement(soluteparms, 'DTHP').text = str( 1 )
    wattabcl = SubElement(soluteparms, 'WaterTableCl').text = str( 0 )
    wattabno3 = SubElement(soluteparms, 'WaterTableNO3').text = str( 0 )
    wattabnh4 = SubElement(soluteparms, 'WaterTableNH4').text = str( 0 )
    wattaburea = SubElement(soluteparms, 'WaterTableUrea').text = str( 0 )
    wattabtracer = SubElement(soluteparms, 'WaterTableTracer').text = str( 0 )
    mininhib = SubElement(soluteparms, 'WaterTableMineralisationInhibitor').text = str( 0 )
    ureainhib = SubElement(soluteparms, 'WaterTableUreaseInhibitor').text = str( 0 )
    nitrifinhib = SubElement(soluteparms, 'WaterTableNitrificationInhibitor').text = str( 0 )
    denitrifinhib = SubElement(soluteparms, 'WaterTableDenitrificationInhibitor').text = str( 0 )
    thickness = SubElement(soluteparms, 'Thickness')
    for idx in range( 1, lyr_cnt, 1 ):
        SubElement(thickness, 'double').text = str( 1000 )
    no3exco = SubElement(soluteparms, 'NO3Exco')
    for idx in range( 1, lyr_cnt, 1 ):
        SubElement(no3exco, 'double').text = str( 0 )
    no3fip = SubElement(soluteparms, 'NO3FIP')
    for idx in range( 1, lyr_cnt, 1 ):
        SubElement(no3fip, 'double').text = str( 1 )
    nh4exco = SubElement(soluteparms, 'NH4Exco')
    for idx in range( 1, lyr_cnt, 1 ):
        SubElement(nh4exco, 'double').text = str( 100 )
    nh4fip = SubElement(soluteparms, 'NH4FIP')
    for idx in range( 1, lyr_cnt, 1 ):
        SubElement(nh4fip, 'double').text = str( 1 )
    ureaexco = SubElement(soluteparms, 'UreaExco')
    for idx in range( 1, lyr_cnt, 1 ):
        SubElement(ureaexco, 'double').text = str( 0 )
    ureafip = SubElement(soluteparms, 'UreaFIP')
    for idx in range( 1, lyr_cnt, 1 ):
        SubElement(ureafip, 'double').text = str( 1 )
    clexco = SubElement(soluteparms, 'ClExco')
    for idx in range( 1, lyr_cnt, 1 ):
        SubElement(clexco, 'double').text = str( 0 )
    clfip = SubElement(soluteparms, 'ClFIP')
    for idx in range( 1, lyr_cnt, 1 ):
        SubElement(clfip, 'double').text = str( 1 )
    swimwtab = SubElement(swim, 'SwimWaterTable')
    wattabdep = SubElement(swimwtab, 'WaterTableDepth').text = str(2000)
    subdrain = SubElement(swim, 'SwimSubsurfaceDrain')
    draindepth = SubElement(subdrain, 'DrainDepth').text = str(1000)
    drainspacing = SubElement(subdrain, 'DrainSpacing').text = str(13500)
    #using a drain radius for 4 inch tile
    drainradius = SubElement(subdrain, 'DrainRadius').text = str(52)
    klat = SubElement(subdrain, 'Klat').text = str(2800)
    impermdepth = SubElement(subdrain, 'ImpermDepth').text = str(3900)

    return swim

###
def get_soilwat_xml( soil ):
    ### get ave clay in profile
    tot_clay = 0.0
    for lyr in APSIM_Soil_Layers:
        depth = lyr[ 'max' ] - lyr[ 'min' ]
        tot_clay += depth * get_depth_weighted_value(
            lyr, soil.Clay, soil.Horizons )
    tot_clay = tot_clay/APSIM_Soil_Layers[-1][ 'max' ]

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

    soil_wat = Element( 'SoilWater' )
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
    diff_const.text = str( soil.DiffusConst )
    diff_slope = SubElement( soil_wat, 'DiffusSlope' )
    diff_slope.text = str( soil.DiffusSlope )
    salb = SubElement( soil_wat, 'Salb' )
    salb.text = str( soil.Salb )
    cn2bare = SubElement( soil_wat, 'CN2Bare' )
    cn2bare.text = str( soil.CN2Bare )
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
        subelem.text = str( 10 * ( lyr[ 'max' ] - lyr[ 'min' ] ) )

    ###
    add_subelements( soil_wat, 'SWCON', soil.SWCON, soil.Horizons )

    return soil_wat

###
class Soil:
    ###
    def __init__( self, soil_df, SWIM = False, SaxtonRawls = False ):
        self.data = soil_df
        self.SWIM = SWIM
        self.SaxtonRawls = SaxtonRawls
        if SaxtonRawls:
            calculate_saxton_rawls( self.data )

        #If using SWIM, update last two KS soil layers to be a 'hole' at
        #drainage depth with KS of 1.0 and 0.01, respectively.
        if SWIM:
            set_value_by_depth( soil_df, 'KS', 100.0, 150.0, 1.0, None )
            set_value_by_depth( soil_df, 'KS', 150.0, 200.0, 0.01, None )
            set_value_by_depth( soil_df, 'sr_KS', 100.0, 150.0, 1.0, None )
            set_value_by_depth( soil_df, 'sr_KS', 150.0, 200.0, 0.01, None )

        # fbiom = biom /(hum - inert_c)
        set_value_by_depth( soil_df, 'FBiom', 0.0, 15.0, 0.035, None)
        set_value_by_depth( soil_df, 'FBiom', 15.0, 30.0, 0.02, None )
        set_value_by_depth( soil_df, 'FBiom', 30.0, 60.0, 0.015, None )
        set_value_by_depth( soil_df, 'FBiom', 60.0, 90.0, 0.015, None )
        set_value_by_depth( soil_df, 'FBiom', 90.0, 120.0, 0.01, None )
        set_value_by_depth( soil_df, 'FBiom', 120.0, None, 0.01, None )

        ### finert
        set_value_by_depth( soil_df, 'FInert', 0.0, 15.0, 0.40, None )
        set_value_by_depth( soil_df, 'FInert', 15.0, 30.0, 0.48, None )
        set_value_by_depth( soil_df, 'FInert', 30.0, 60.0, 0.68, None )
        set_value_by_depth( soil_df, 'FInert', 60.0, 90.0, 0.80, None )
        set_value_by_depth( soil_df, 'FInert', 90.0, 120.0, 0.80, None )
        set_value_by_depth( soil_df, 'FInert', 120.0, None, 0.90, None )

        # air dry
        # 0 - 15 cm: 0.01 * 0.5 * wfifteenbar_r
        # 15 - 30 cm: 0.01 * 0.75 * wfifteenbar_r
        # > 30 cm: 0.01 * wfifteenbar_r
        ad_eqn_1 = lambda df: df[ 'wfifteenbar_r' ] * 0.01 * 0.5
        ad_eqn_2 = lambda df: df[ 'wfifteenbar_r' ] * 0.01 * 0.8
        ad_eqn_3 = lambda df: df[ 'wfifteenbar_r' ] * 0.01
        set_value_by_depth( soil_df, 'AirDry', 0.0, 15.0, None, ad_eqn_1 )
        set_value_by_depth( soil_df, 'AirDry', 15.0, 30.0, None, ad_eqn_2 )
        set_value_by_depth( soil_df, 'AirDry', 30.0, None, None, ad_eqn_3 )

        #entrapped air %
        soil_df.loc[ ( soil_df[ 'claytotal_r' ] >= 55 ), 'sat_e' ] = 0.03 #clay
        soil_df.loc[ ( soil_df[ 'sandtotal_r' ] >= 85 ), 'sat_e' ] = 0.07 #sands
        soil_df.loc[ ( soil_df[ 'claytotal_r' ] < 55 ) &
            ( soil_df[ 'sandtotal_r' ] < 85 ), 'sat_e' ] = 0.05 #loam

        #SWCON
        soil_df.loc[ ( soil_df[ 'claytotal_r' ] >= 55 ), 'swcon' ] = 0.3
        soil_df.loc[ ( soil_df[ 'sandtotal_r' ] >= 85 ), 'swcon' ] = 0.7
        soil_df.loc[ ( soil_df[ 'claytotal_r' ] < 55 ) &
            ( soil_df[ 'sandtotal_r' ] < 85 ), 'swcon' ] = 0.5

        #BD: bulk density
        #LL15: soil lower limit
        #DUL: soil drained upper limit
        #SAT: saturated water holding capacity
        #KS: saturated hydraulic conductivity
        #OC: soil organic carbon
        #PH: soil pH
        #NO3: initial soil nitrate concentration
        #NH4: initial soil ammonium concentration
        #AirDry: air-dried water holding capacity

        ### provide direct access to apsim properties
        self.FBiom = soil_df[ 'FBiom' ]
        self.FInert = soil_df[ 'FInert' ]
        self.OM = soil_df[ 'om_r' ]
        self.OC = soil_df[ 'om_r' ]/1.724
        self.PH = soil_df[ 'ph1to1h2o_r' ]
        self.NO3 = soil_df[ 'om_r' ]
        self.NH4 = soil_df[ 'om_r' ]
        self.Clay = soil_df[ 'claytotal_r' ]
        self.Sand = soil_df[ 'sandtotal_r' ]
        self.Silt = soil_df[ 'silttotal_r' ]
        self.SWCON = soil_df[ 'swcon' ]

        if soil_df[ 'claytotal_r' ][0] >= 55:
            self.DiffusConst = 40
            self.DiffusSlope = 16
            self.CN2Bare = 73
        elif soil_df[ 'sandtotal_r' ][0] >= 85:
            self.DiffusConst = 250
            self.DiffusSlope = 22
            self.CN2Bare = 68
        else:
            self.DiffusConst = 88
            self.DiffusSlope = 35
            self.CN2Bare = 73

        self.RootCN = 40
        self.RootWt = 1000
        self.SoilCN = 12
        self.EnrACoeff = 7.4
        self.EnrBCoeff = 0.2
        self.Salb = 0.13

        self.Horizons = soil_df[ [ 'hzdept_r', 'hzdepb_r' ] ]
        if SaxtonRawls:
            self.BD = soil_df[ 'sr_BD' ]
            self.LL15 = soil_df[ 'sr_LL15' ]
            self.AirDry = soil_df[ 'sr_AirDry' ]
            self.DUL = soil_df[ 'sr_DUL' ]
            self.SAT = soil_df[ 'sr_SAT' ]
            self.KS = soil_df[ 'sr_KS' ]
        else:
            self.BD = soil_df[ 'dbthirdbar_r' ]
            self.LL15 = 0.01 * soil_df[ 'wfifteenbar_r' ]
            self.DUL = 0.01 * soil_df[ 'wthirdbar_r' ]
            self.KS = 0.001 * 3600 * 24 * soil_df[ 'ksat_r' ]
            self.AirDry = soil_df[ 'AirDry' ]
            self.SAT = 1 - ( soil_df[ 'dbthirdbar_r']/2.65 ) - soil_df[ 'sat_e' ]

            print( soil_df )

    ###
    def soil_xml( self ):
        # construct soil xml
        soil_xml = Element( 'Soil' )

        # initial water
        initwater = SubElement( soil_xml, 'InitialWater' )
        initwater.set( 'name', 'Initial Water' )
        fracfull = SubElement( initwater, 'FractionFull' )
        fracfull.text = str( 1 )
        percmethod = SubElement( initwater, 'PercentMethod' )
        percmethod.text = 'FilledFromTop'
        water = SubElement( soil_xml, 'Water' )

        add_crop_xml( water, 'maize', self )
        add_crop_xml( water, 'soybean', self )
        add_crop_xml( water, 'wheat', self )

        add_subelements( water, 'Thickness' )

        ### bulk density
        add_subelements( water, 'BD', self.BD, self.Horizons )

        ### air dry
        add_subelements( water, 'AirDry', self.AirDry, self.Horizons )

        ### lower limit (wilting pt.)
        add_subelements( water, 'LL15', self.LL15, self.Horizons )

        ### drained upper limit (field cap.)
        add_subelements( water, 'DUL', self.DUL, self.Horizons )

        ### saturated water holding capacity
        add_subelements( water, 'SAT', self.SAT, self.Horizons )

        ### saturated hydraulic conductivity
        add_subelements( water, 'KS', self.KS, self.Horizons )

        #soil water module - SWIM or APSIM
        if self.SWIM:
            soilwat = get_swim_xml()
        else:
            soilwat = get_soilwat_xml( self )
        soil_xml.append( soilwat )

        ### surface OM module variables
        som = SubElement( soil_xml, 'SoilOrganicMatter' )

        add_subelement( som, 'RootCN', self.RootCN )
        add_subelement( som, 'RootWt', self.RootWt )
        add_subelement( som, 'SoilCN', self.SoilCN )
        add_subelement( som, 'EnrACoeff', self.EnrACoeff )
        add_subelement( som, 'EnrBCoeff', self.EnrBCoeff )

        add_subelements( som, 'Thickness' )

        # soil organic carbon
        add_subelements( som, 'OC', self.OC, self.Horizons )

        # fbiom = biom /(hum - inert_c)
        add_subelements( som, 'FBiom', self.FBiom, self.Horizons )

        # finert
        add_subelements( som, 'FInert', self.FInert, self.Horizons )

        # analysis
        anlys = SubElement( soil_xml, 'Analysis' )
        add_subelements( anlys, 'Thickness' )

        # soil pH
        add_subelements( anlys, 'PH', self.PH, self.Horizons )

        # soil sample inputs
        sample = SubElement( soil_xml, 'Sample' )
        sample.set( 'name', 'Initial nitrogen' )

        sampdate = SubElement( sample, 'Date' )
        sampdate.set( 'type', 'date' )
        sampdate.set( 'description', 'Sample Date:' )

        add_subelements( sample, 'Thickness' )

        ### initial no3 ( set to OM percent )
        add_subelements( sample, 'NO3', self.NO3, self.Horizons )

        ### initial nh4 ( set to OM percent )
        add_subelements( sample, 'NH4', self.NH4, self.Horizons )

        return soil_xml


#     soil_df.to_csv( 'tmp.txt', sep = '\t', header = True )
#

#
#
#
#
#
#
# ###
# def Get_SSURGO_Soils_Data( mukeys, db_conn ):
#     mukeystr = ','.join( mukeys )
#     query = (
#         '''select
#             *
#         from api.get_soil_properties( \'{''' + mukeystr + '}\'::text[] )' )
#     soils_df = pd.read_sql( query, db_conn )
#
#     return soils_df
#

#

#
#

#
# def Add_SWIM( lyr_cnt = 3 ):
#     swim = Element( 'Swim' )
#     salb = SubElement(swim, 'Salb').text = str( 0.13 )
#     cn2bare = SubElement(swim, 'CN2Bare').text = str( 75 )
#     cnred = SubElement(swim, 'CNRed').text = str( 20 )
#     cncov = SubElement(swim, 'CNCov').text = str( 0.8 )
#     kdul = SubElement(swim, 'KDul').text = str( 0.1 )
#     psidul = SubElement(swim, 'PSIDul').text = str( -100 )
#     vc = SubElement(swim, 'VC').text = 'true'
#     dtmin = SubElement(swim, 'DTmin').text = str( 0 )
#     dtmax = SubElement(swim, 'DTmax').text = str( 1440 )
#     maxwater = SubElement(swim, 'MaxWaterIncrement').text = str( 10 )
#     spaceweight = SubElement(swim, 'SpaceWeightingFactor').text = str( 0 )
#     solutespace = SubElement(swim, 'SoluteSpaceWeightingFactor').text = str( 0 )
#     diagnostics = SubElement(swim, 'Diagnostics').text = 'true'
#     soluteparms = SubElement(swim, 'SwimSoluteParameters')
#     dis = SubElement(soluteparms, 'Dis').text = str( 15 )
#     disp = SubElement(soluteparms, 'Disp').text = str( 1 )
#     sp_a = SubElement(soluteparms, 'A').text = str( 1 )
#     dthc = SubElement(soluteparms, 'DTHC').text = str( 1 )
#     dthp = SubElement(soluteparms, 'DTHP').text = str( 1 )
#     wattabcl = SubElement(soluteparms, 'WaterTableCl').text = str( 0 )
#     wattabno3 = SubElement(soluteparms, 'WaterTableNO3').text = str( 0 )
#     wattabnh4 = SubElement(soluteparms, 'WaterTableNH4').text = str( 0 )
#     wattaburea = SubElement(soluteparms, 'WaterTableUrea').text = str( 0 )
#     wattabtracer = SubElement(soluteparms, 'WaterTableTracer').text = str( 0 )
#     mininhib = SubElement(soluteparms, 'WaterTableMineralisationInhibitor').text = str( 0 )
#     ureainhib = SubElement(soluteparms, 'WaterTableUreaseInhibitor').text = str( 0 )
#     nitrifinhib = SubElement(soluteparms, 'WaterTableNitrificationInhibitor').text = str( 0 )
#     denitrifinhib = SubElement(soluteparms, 'WaterTableDenitrificationInhibitor').text = str( 0 )
#     thickness = SubElement(soluteparms, 'Thickness')
#     for idx in range( 1, lyr_cnt, 1 ):
#         SubElement(thickness, 'double').text = str( 1000 )
#     no3exco = SubElement(soluteparms, 'NO3Exco')
#     for idx in range( 1, lyr_cnt, 1 ):
#         SubElement(no3exco, 'double').text = str( 0 )
#     no3fip = SubElement(soluteparms, 'NO3FIP')
#     for idx in range( 1, lyr_cnt, 1 ):
#         SubElement(no3fip, 'double').text = str( 1 )
#     nh4exco = SubElement(soluteparms, 'NH4Exco')
#     for idx in range( 1, lyr_cnt, 1 ):
#         SubElement(nh4exco, 'double').text = str( 100 )
#     nh4fip = SubElement(soluteparms, 'NH4FIP')
#     for idx in range( 1, lyr_cnt, 1 ):
#         SubElement(nh4fip, 'double').text = str( 1 )
#     ureaexco = SubElement(soluteparms, 'UreaExco')
#     for idx in range( 1, lyr_cnt, 1 ):
#         SubElement(ureaexco, 'double').text = str( 0 )
#     ureafip = SubElement(soluteparms, 'UreaFIP')
#     for idx in range( 1, lyr_cnt, 1 ):
#         SubElement(ureafip, 'double').text = str( 1 )
#     clexco = SubElement(soluteparms, 'ClExco')
#     for idx in range( 1, lyr_cnt, 1 ):
#         SubElement(clexco, 'double').text = str( 0 )
#     clfip = SubElement(soluteparms, 'ClFIP')
#     for idx in range( 1, lyr_cnt, 1 ):
#         SubElement(clfip, 'double').text = str( 1 )
#     swimwtab = SubElement(swim, 'SwimWaterTable')
#     wattabdep = SubElement(swimwtab, 'WaterTableDepth').text = str(2000)
#     subdrain = SubElement(swim, 'SwimSubsurfaceDrain')
#     draindepth = SubElement(subdrain, 'DrainDepth').text = str(1000)
#     drainspacing = SubElement(subdrain, 'DrainSpacing').text = str(13500)
#     #using a drain radius for 4 inch tile
#     drainradius = SubElement(subdrain, 'DrainRadius').text = str(52)
#     klat = SubElement(subdrain, 'Klat').text = str(2800)
#     impermdepth = SubElement(subdrain, 'ImpermDepth').text = str(3900)
#
#     return swim
#
#
#
# ###
# def add_subelem( parent, child, value ):
#     subelem = SubElement( parent, child )
#     subelem.text = str( round( value, 3 ) )
#
#     return subelem
#
# def Create_Soil_XML( soil_df, SWIM = False, SaxtonRawls = False ):
#
#     # bulk density
#     soil_df[ 'BD' ] = soil_df[ 'dbthirdbar_r' ]
#
#     # air dry
#     # 0 - 15 cm: 0.01 * 0.5 * wfifteenbar_r
#     # 15 - 30 cm: 0.01 * 0.75 * wfifteenbar_r
#     # > 30 cm: 0.01 * wfifteenbar_r
#     air_dry_1 = lambda df: df[ 'wfifteenbar_r' ] * 0.5 * 0.01
#     air_dry_2 = lambda df: df[ 'wfifteenbar_r' ] * 0.75 * 0.01
#     air_dry_3 = lambda df: df[ 'wfifteenbar_r' ] * 0.01
#     update_by_depth( soil_df, 'AirDry', 0.0, 15.0, None, air_dry_1 )
#     update_by_depth( soil_df, 'AirDry', 15.0, 30.0, None, air_dry_2 )
#     update_by_depth( soil_df, 'AirDry', 30.0, None, None, air_dry_3 )
#
#     # soil lower limit
#     soil_df[ 'LL15' ] = 0.01 * soil_df[ 'wfifteenbar_r' ]
#
#     # soil drained upper limit
#     soil_df[ 'DUL' ] = 0.01 * soil_df[ 'wthirdbar_r' ]
#
#     # saturated water holding capacity
#     soil_df[ 'SAT' ] = 1 - ( soil_df[ 'dbthirdbar_r']/2.65 )
#
#     # saturated hydraulic conductivity
#     soil_df[ 'KS' ] = 0.001 * 3600 * 24 * soil_df[ 'ksat_r' ]
#
#     # soil organic carbon
#     soil_df[ 'OC' ] = soil_df[ 'om_r' ]/1.724
#
#     # fbiom = biom /(hum - inert_c)
#     update_by_depth( soil_df, 'FBiom', 0.0, 15.0, 0.35, None)
#     update_by_depth( soil_df, 'FBiom', 15.0, 30.0, 0.21, None )
#     update_by_depth( soil_df, 'FBiom', 30.0, 60.0, 0.13, None )
#     update_by_depth( soil_df, 'FBiom', 60.0, None, 0.10, None )
#
#     ### finert
#     update_by_depth( soil_df, 'FInert', 0.0, 15.0, 0.40, None )
#     update_by_depth( soil_df, 'FInert', 15.0, 30.0, 0.48, None )
#     update_by_depth( soil_df, 'FInert', 30.0, 60.0, 0.68, None )
#     update_by_depth( soil_df, 'FInert', 60.0, 90.0, 0.80, None )
#     update_by_depth( soil_df, 'FInert', 90.0, 120.0, 0.80, None )
#     update_by_depth( soil_df, 'FInert', 120.0, None, 0.90, None )
#
#     # pH
#     soil_df[ 'PH' ] = soil_df[ 'ph1to1h2o_r' ]
#
#     # init NO3 and NH4
#     soil_df[ 'NO3' ] = soil_df[ 'om_r' ]
#     soil_df[ 'NH4' ] = soil_df[ 'om_r' ]
#
#     # Saxton-Rawls calculations
#     S = soil_df[ 'sandtotal_r' ] * 0.01
#     C = soil_df[ 'claytotal_r' ] * 0.01
#     OM = soil_df[ 'om_r' ] * 0.01
#
#     # LL15
#     theta_1500t = ( -0.024 * S + 0.487 * C + 0.006 * OM + 0.005 * S * OM
#         - 0.013 * C * OM + 0.068 * S * C + 0.031 )
#     soil_df[ 'sr_LL15'] = theta_1500t + ( 0.14 * theta_1500t - 0.02 )
#
#     # DUL
#     theta_33t = ( -0.251 * S + 0.195 * C + 0.011 * OM + 0.006 * S * OM
#         - 0.027 * C * OM + 0.452 * S * C + 0.299 )
#     soil_df[ 'sr_DUL' ] = theta_33t + (
#         1.283 * theta_33t**2 - 0.374 * theta_33t - 0.015 )
#
#     # SAT
#     theta_s33t = ( 0.278 * S + 0.034 * C + 0.022 * OM - 0.018 * S * OM
#         - 0.027 * C * OM - 0.584 * S * C + 0.078 )
#     theta_s33 = theta_s33t + ( 0.636 * theta_s33t - 0.107 )
#     soil_df[ 'sr_SAT' ] = soil_df[ 'sr_DUL' ] + theta_s33 - 0.097 * S + 0.043
#
#     # air dry
#     # 0 - 15 cm: 0.01 * 0.5 * wfifteenbar_r
#     # 15 - 30 cm: 0.01 * 0.75 * wfifteenbar_r
#     # > 30 cm: 0.01 * wfifteenbar_r
#     air_dry_1 = lambda df: df[ 'sr_LL15'] * 0.5 * 0.01
#     air_dry_2 = lambda df: df[ 'sr_LL15'] * 0.75 * 0.01
#     air_dry_3 = lambda df: df[ 'sr_LL15'] * 0.01
#     update_by_depth( soil_df, 'sr_AirDry', 0.0, 15.0, None, air_dry_1 )
#     update_by_depth( soil_df, 'sr_AirDry', 15.0, 30.0, None, air_dry_2 )
#     update_by_depth( soil_df, 'sr_AirDry', 30.0, None, None, air_dry_3 )
#
#     # BD
#     soil_df[ 'sr_BD' ] = ( 1 - soil_df[ 'sr_SAT' ] ) * 2.65
#
#     # KS
#     B = ( ( np.log( 1500 ) - np.log( 33 ) )/
#         ( np.log( soil_df[ 'sr_DUL' ] ) - np.log( soil_df[ 'sr_LL15' ] ) ) )
#     ks_lambda = 1/B
#     soil_df[ 'sr_KS' ] = ( 1930 * ( soil_df[ 'sr_SAT' ]
#         - soil_df[ 'sr_LL15' ] )**( 3 - ks_lambda ) )
#
#     #If using SWIM, update last two KS soil layers to be a 'hole' at drainage depth with KS of 1.0 and 0.01, respectively.
#     if SWIM:
#         update_by_depth( soil_df, 'KS', 100.0, 150.0, 1.0, None )
#         update_by_depth( soil_df, 'KS', 150.0, 200.0, 0.01, None )
#         update_by_depth( soil_df, 'sr_KS', 100.0, 150.0, 1.0, None )
#         update_by_depth( soil_df, 'sr_KS', 150.0, 200.0, 0.01, None )
#
#
#     soil_df.to_csv( 'tmp.txt', sep = '\t', header = True )
#
#     # construct soil xml
#     soil_xml = Element( 'Soil' )
#
#     # initial water
#     initwater = SubElement( soil_xml, 'InitialWater' )
#     initwater.set( 'name', 'Initial Water' )
#     fracfull = SubElement( initwater, 'FractionFull' )
#     fracfull.text = str( 1 )
#     percmethod = SubElement( initwater, 'PercentMethod' )
#     percmethod.text = 'FilledFromTop'
#     water = SubElement( soil_xml, 'Water' )
#     water.append( Add_Soil_Crop( 'maize', soil_df ) )
#     water.append( Add_Soil_Crop( 'soybean', soil_df ) )
#     water.append( Add_Soil_Crop( 'wheat', soil_df ) )
#
#     thickness = SubElement( water, 'Thickness' )
#     add_subelems( thickness, 'double' )
#
#     ### layer thickness
#     if SaxtonRawls:
#         ### bulk density
#         bulk_dens = SubElement( water, 'BD' )
#         add_subelems( bulk_dens, 'double', soil_df, 'sr_BD' )
#
#         ### air dry
#         air_dry = SubElement( water, 'AirDry' )
#         add_subelems( air_dry, 'double', soil_df, 'sr_AirDry' )
#
#         ### lower limit (wilting pt.)
#         ll15 = SubElement( water, 'LL15' )
#         add_subelems( ll15, 'double', soil_df, 'sr_LL15' )
#
#         ### drained upper limit (field cap.)
#         dul = SubElement( water, 'DUL' )
#         add_subelems( dul, 'double', soil_df, 'sr_DUL' )
#
#         ### saturated water holding capacity
#         sat = SubElement( water, 'SAT' )
#         add_subelems( sat, 'double', soil_df, 'sr_SAT' )
#
#         ### saturated hydraulic conductivity
#         ks = SubElement( water, 'KS' )
#         add_subelems( ks, 'double', soil_df, 'sr_KS' )
#
#     else:
#         ### bulk density
#         bulk_dens = SubElement( water, 'BD' )
#         add_subelems( bulk_dens, 'double', soil_df, 'BD' )
#
#         ### air dry
#         air_dry = SubElement( water, 'AirDry' )
#         add_subelems( air_dry, 'double', soil_df, 'AirDry' )
#
#         ### lower limit (wilting pt.)
#         ll15 = SubElement( water, 'LL15' )
#         add_subelems( ll15, 'double', soil_df, 'LL15' )
#
#         ### drained upper limit (field cap.)
#         dul = SubElement( water, 'DUL' )
#         add_subelems( dul, 'double', soil_df, 'DUL' )
#
#         ### saturated water holding capacity
#         sat = SubElement( water, 'SAT' )
#         add_subelems( sat, 'double', soil_df, 'SAT' )
#
#         ### saturated hydraulic conductivity
#         ks = SubElement( water, 'KS' )
#         add_subelems( ks, 'double', soil_df, 'KS' )
#
#     # soil water module - SWIM or APSIM
#     if SWIM:
#         soilwat = Add_SWIM()
#     else:
#         soilwat = Add_SoilWat( soil_df )
#     soil_xml.append( soilwat )
#
#     ### surface OM module variables
#     som = SubElement( soil_xml, 'SoilOrganicMatter' )
#     add_subelem( som, 'RootCN', 40 )
#     add_subelem( som, 'RootWt', 1200 )
#     add_subelem( som, 'SoilCN', 12 )
#     add_subelem( som, 'EnrACoeff', 7.4 )
#     add_subelem( som, 'EnrBCoeff', 7.4 )
#
#     thickness = SubElement( som, 'Thickness' )
#     add_subelems( thickness, 'double' )
#
#     # soil organic carbon
#     oc = SubElement( som, 'OC' )
#     add_subelems( oc, 'double', soil_df, 'OC' )
#
#     # fbiom = biom /(hum - inert_c)
#     fbiom = SubElement( som, 'FBiom' )
#     add_subelems( fbiom, 'double', soil_df, 'FBiom' )
#
#     # finert
#     finert = SubElement( som, 'FInert' )
#     add_subelems( finert, 'double', soil_df, 'FInert' )
#
#     # analysis
#     anlys = SubElement( soil_xml, 'Analysis' )
#     thickness = SubElement( anlys, 'Thickness' )
#     add_subelems( thickness, 'double' )
#
#     # soil pH
#     ph = SubElement( anlys, 'PH' )
#     add_subelems( ph, 'double', soil_df, 'PH' )
#
#     # soil sample inputs
#     sample = SubElement( soil_xml, 'Sample' )
#     sample.set( 'name', 'Initial nitrogen' )
#
#     sampdate = SubElement( sample, 'Date' )
#     sampdate.set( 'type', 'date' )
#     sampdate.set( 'description', 'Sample Date:' )
#
#     thickness = SubElement( sample, 'Thickness' )
#     add_subelems( thickness, 'double' )
#
#     ### initial no3 ( set to OM percent )
#     no3 = SubElement( sample, 'NO3' )
#     add_subelems( no3, 'double', soil_df, 'NO3' )
#
#     ### initial nh4 ( set to OM percent )
#     nh4 = SubElement( sample, 'NH4' )
#     add_subelems( nh4, 'double', soil_df, 'NH4' )
#
#     return soil_xml
#
#
# def Create_SSURGO_Soil_XML( soil_df, SWIM = False, SaxtonRawls = False ):
#
#     # base specs
#     muname = soil_df[ 'muname' ][0]
#     texture = soil_df[ 'texdesc' ][0]
#     mukey = soil_df[ 'mukey' ][0]
#     musym = soil_df[ 'musym' ][0]
#     cokey = soil_df[ 'cokey' ][0]
#     area_sym = soil_df[ 'areasymbol' ][0]
#
#     ssurgo_yr = 2019
#
#     # bulk density
#     soil_df[ 'BD' ] = soil_df[ 'dbthirdbar_r' ]
#
#     # air dry
#     # 0 - 15 cm: 0.01 * 0.5 * wfifteenbar_r
#     # 15 - 30 cm: 0.01 * 0.75 * wfifteenbar_r
#     # > 30 cm: 0.01 * wfifteenbar_r
#     air_dry_1 = lambda df: df[ 'wfifteenbar_r' ] * 0.5 * 0.01
#     air_dry_2 = lambda df: df[ 'wfifteenbar_r' ] * 0.75 * 0.01
#     air_dry_3 = lambda df: df[ 'wfifteenbar_r' ] * 0.01
#     update_by_depth( soil_df, 'AirDry', 0.0, 15.0, None, air_dry_1 )
#     update_by_depth( soil_df, 'AirDry', 15.0, 30.0, None, air_dry_2 )
#     update_by_depth( soil_df, 'AirDry', 30.0, None, None, air_dry_3 )
#
#     # soil lower limit
#     soil_df[ 'LL15' ] = 0.01 * soil_df[ 'wfifteenbar_r' ]
#
#     # soil drained upper limit
#     soil_df[ 'DUL' ] = 0.01 * soil_df[ 'wthirdbar_r' ]
#
#     # saturated water holding capacity
#     soil_df[ 'SAT' ] = 1 - ( soil_df[ 'dbthirdbar_r']/2.65 )
#
#     # saturated hydraulic conductivity
#     soil_df[ 'KS' ] = 0.001 * 3600 * 24 * soil_df[ 'ksat_r' ]
#
#     # soil organic carbon
#     soil_df[ 'OC' ] = soil_df[ 'om_r' ]/1.724
#
#     # fbiom = biom /(hum - inert_c)
#     update_by_depth( soil_df, 'FBiom', 0.0, 15.0, 0.35, None)
#     update_by_depth( soil_df, 'FBiom', 15.0, 30.0, 0.21, None )
#     update_by_depth( soil_df, 'FBiom', 30.0, 60.0, 0.13, None )
#     update_by_depth( soil_df, 'FBiom', 60.0, None, 0.10, None )
#
#     ### finert
#     update_by_depth( soil_df, 'FInert', 0.0, 15.0, 0.40, None )
#     update_by_depth( soil_df, 'FInert', 15.0, 30.0, 0.48, None )
#     update_by_depth( soil_df, 'FInert', 30.0, 60.0, 0.68, None )
#     update_by_depth( soil_df, 'FInert', 60.0, 90.0, 0.80, None )
#     update_by_depth( soil_df, 'FInert', 90.0, 120.0, 0.80, None )
#     update_by_depth( soil_df, 'FInert', 120.0, None, 0.90, None )
#
#     # pH
#     soil_df[ 'PH' ] = soil_df[ 'ph1to1h2o_r' ]
#
#     # init NO3 and NH4
#     soil_df[ 'NO3' ] = soil_df[ 'om_r' ]
#     soil_df[ 'NH4' ] = soil_df[ 'om_r' ]
#
#     # Saxton-Rawls calculations
#     S = soil_df[ 'sandtotal_r' ] * 0.01
#     C = soil_df[ 'claytotal_r' ] * 0.01
#     OM = soil_df[ 'om_r' ] * 0.01
#
#     # LL15
#     theta_1500t = ( -0.024 * S + 0.487 * C + 0.006 * OM + 0.005 * S * OM
#         - 0.013 * C * OM + 0.068 * S * C + 0.031 )
#     soil_df[ 'sr_LL15'] = theta_1500t + ( 0.14 * theta_1500t - 0.02 )
#
#     # DUL
#     theta_33t = ( -0.251 * S + 0.195 * C + 0.011 * OM + 0.006 * S * OM
#         - 0.027 * C * OM + 0.452 * S * C + 0.299 )
#     soil_df[ 'sr_DUL' ] = theta_33t + (
#         1.283 * theta_33t**2 - 0.374 * theta_33t - 0.015 )
#
#     # SAT
#     theta_s33t = ( 0.278 * S + 0.034 * C + 0.022 * OM - 0.018 * S * OM
#         - 0.027 * C * OM - 0.584 * S * C + 0.078 )
#     theta_s33 = theta_s33t + ( 0.636 * theta_s33t - 0.107 )
#     soil_df[ 'sr_SAT' ] = soil_df[ 'sr_DUL' ] + theta_s33 - 0.097 * S + 0.043
#
#     # BD
#     soil_df[ 'sr_BD' ] = ( 1 - soil_df[ 'sr_SAT' ] ) * 2.65
#
#     # KS
#     B = ( ( np.log( 1500 ) - np.log( 33 ) )/
#         ( np.log( soil_df[ 'sr_DUL' ] ) - np.log( soil_df[ 'sr_LL15' ] ) ) )
#     ks_lambda = 1/B
#     soil_df[ 'sr_KS' ] = ( 1930 * ( soil_df[ 'sr_SAT' ]
#         - soil_df[ 'sr_LL15' ] )**( 3 - ks_lambda ) )
#
#     #If using SWIM, update last two KS soil layers to be a 'hole' at drainage depth with KS of 1.0 and 0.01, respectively.
#     if SWIM:
#         update_by_depth( soil_df, 'KS', 100.0, 150.0, 1.0, None )
#         update_by_depth( soil_df, 'KS', 150.0, 200.0, 0.01, None )
#         update_by_depth( soil_df, 'sr_KS', 100.0, 150.0, 1.0, None )
#         update_by_depth( soil_df, 'sr_KS', 150.0, 200.0, 0.01, None )
#
#     soil_df.to_csv( 'tmp.txt', sep = '\t', header = True )
#
#     # construct soil xml
#     soil_xml = Element( 'Soil' )
#
#     # initial water
#     initwater = SubElement( soil_xml, 'InitialWater' )
#     initwater.set( 'name', 'Initial Water' )
#     fracfull = SubElement( initwater, 'FractionFull' )
#     fracfull.text = str( 1 )
#     percmethod = SubElement( initwater, 'PercentMethod' )
#     percmethod.text = 'FilledFromTop'
#     water = SubElement( soil_xml, 'Water' )
#     water.append( Add_Soil_Crop( 'maize', soil_df ) )
#     water.append( Add_Soil_Crop( 'soybean', soil_df ) )
#     water.append( Add_Soil_Crop( 'wheat', soil_df ) )
#
#     thickness = SubElement( water, 'Thickness' )
#     add_subelems( thickness, 'double' )
#
#     ### layer thickness
#     if SaxtonRawls:
#         ### bulk density
#         bulk_dens = SubElement( water, 'BD' )
#         add_subelems( bulk_dens, 'double', soil_df, 'sr_BD' )
#
#         ### air dry
#         air_dry = SubElement( water, 'AirDry' )
#         add_subelems( air_dry, 'double', soil_df, 'sr_AirDry' )
#
#         ### lower limit (wilting pt.)
#         ll15 = SubElement( water, 'LL15' )
#         add_subelems( ll15, 'double', soil_df, 'sr_LL15' )
#
#         ### drained upper limit (field cap.)
#         dul = SubElement( water, 'DUL' )
#         add_subelems( dul, 'double', soil_df, 'sr_DUL' )
#
#         ### saturated water holding capacity
#         sat = SubElement( water, 'SAT' )
#         add_subelems( sat, 'double', soil_df, 'sr_SAT' )
#
#         ### saturated hydraulic conductivity
#         ks = SubElement( water, 'KS' )
#         add_subelems( ks, 'double', soil_df, 'sr_KS' )
#
#     else:
#         ### bulk density
#         bulk_dens = SubElement( water, 'BD' )
#         add_subelems( bulk_dens, 'double', soil_df, 'BD' )
#
#         ### air dry
#         air_dry = SubElement( water, 'AirDry' )
#         add_subelems( air_dry, 'double', soil_df, 'AirDry' )
#
#         ### lower limit (wilting pt.)
#         ll15 = SubElement( water, 'LL15' )
#         add_subelems( ll15, 'double', soil_df, 'LL15' )
#
#         ### drained upper limit (field cap.)
#         dul = SubElement( water, 'DUL' )
#         add_subelems( dul, 'double', soil_df, 'DUL' )
#
#         ### saturated water holding capacity
#         sat = SubElement( water, 'SAT' )
#         add_subelems( sat, 'double', soil_df, 'SAT' )
#
#         ### saturated hydraulic conductivity
#         ks = SubElement( water, 'KS' )
#         add_subelems( ks, 'double', soil_df, 'KS' )
#
#     # soil water module - SWIM or APSIM
#     if SWIM:
#         soilwat = Add_SWIM()
#     else:
#         soilwat = Add_SoilWat( soil_df )
#     soil_xml.append( soilwat )
#
#     ### surface OM module variables
#     som = SubElement( soil_xml, 'SoilOrganicMatter' )
#     add_subelem( som, 'RootCN', 40 )
#     add_subelem( som, 'RootWt', 1200 )
#     add_subelem( som, 'SoilCN', 12 )
#     add_subelem( som, 'EnrACoeff', 7.4 )
#     add_subelem( som, 'EnrBCoeff', 7.4 )
#
#     thickness = SubElement( som, 'Thickness' )
#     add_subelems( thickness, 'double' )
#
#     # soil organic carbon
#     oc = SubElement( som, 'OC' )
#     add_subelems( oc, 'double', soil_df, 'OC' )
#
#     # fbiom = biom /(hum - inert_c)
#     fbiom = SubElement( som, 'FBiom' )
#     add_subelems( fbiom, 'double', soil_df, 'FBiom' )
#
#     # finert
#     finert = SubElement( som, 'FInert' )
#     add_subelems( finert, 'double', soil_df, 'FInert' )
#
#     # analysis
#     anlys = SubElement( soil_xml, 'Analysis' )
#     thickness = SubElement( anlys, 'Thickness' )
#     add_subelems( thickness, 'double' )
#
#     # soil pH
#     ph = SubElement( anlys, 'PH' )
#     add_subelems( ph, 'double', soil_df, 'PH' )
#
#     # soil sample inputs
#     sample = SubElement( soil_xml, 'Sample' )
#     sample.set( 'name', 'Initial nitrogen' )
#
#     sampdate = SubElement( sample, 'Date' )
#     sampdate.set( 'type', 'date' )
#     sampdate.set( 'description', 'Sample Date:' )
#
#     thickness = SubElement( sample, 'Thickness' )
#     add_subelems( thickness, 'double' )
#
#     ### initial no3 ( set to OM percent )
#     no3 = SubElement( sample, 'NO3' )
#     add_subelems( no3, 'double', soil_df, 'NO3' )
#
#     ### initial nh4 ( set to OM percent )
#     nh4 = SubElement( sample, 'NH4' )
#     add_subelems( nh4, 'double', soil_df, 'NH4' )
#
#     return soil_xml
