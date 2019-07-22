#!/usr/bin/env Python

import xml.etree.ElementTree
from xml.etree.ElementTree import ElementTree, Element, SubElement

from soils import *
from database import *

user = 'aepe'
database = 'aepe'
port = 2345
host = '129.186.185.33'
ssurgo_db = ConnectToDB( port, host, user, database )

#####
def Init_Apsim_File():
    apsim_xml = Element( 'folder' )
    apsim_xml.set( 'version', '36' )
    apsim_xml.set( 'creator', 'Apsim_Wrapper' )
    apsim_xml.set( 'name', 'S1' )
    simgrp = SubElement( apsim_xml, 'folder' )
    simgrp.set( 'name', 'Tests' )
    sim = SubElement( simgrp, 'simulation' )
    sim.set( 'name', 'Test Sim' )
    metfile = SubElement( sim, 'metfile' )
    metfile.set( 'name', 'met' )
    filename = SubElement( metfile, 'filename' )
    filename.set( 'name', 'filename' )
    filename.set( 'input', 'yes' )
    filename.text = 'MSF_daymet_1980_2017.met'
    clock = SubElement( sim, 'clock' )
    clock_start = SubElement( clock, 'start_date' )
    clock_start.set( 'type', 'date' )
    clock_start.set( 'description', 'Enter the start date of the simulation' )
    clock_start.text = '01/01/2007'
    clock_end = SubElement( clock, 'end_date' )
    clock_end.set( 'type', 'date' )
    clock_end.set( 'description', 'Enter the end date of the simulation' )
    clock_end.text = '31/12/2017'
    sumfile = SubElement( sim, 'summaryfile' )
    area = SubElement( sim, 'area' )
    area.set( 'name', 'paddock' )

    return apsim_xml

#####
mukeys = [ '403351' ]
soils_lyr_df = Get_SSURGO_Soils_Data( mukeys, ssurgo_db )
for mukey in mukeys:
    soil_df = soils_lyr_df.loc[ soils_lyr_df[ 'mukey' ] == mukey ]
    soil_xml = Create_Soil_XML( soil_df )

apsim_xml = Init_Apsim_File()


tree = ElementTree()
tree._setroot( apsim_xml )
tree.write( 'tester.apsim' )
