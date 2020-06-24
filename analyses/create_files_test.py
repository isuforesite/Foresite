#!/usr/bin/env Python
import sys
sys.path.append( '../.' )
import pathlib
import json
import os
import traceback
import xml.etree.ElementTree
from xml.etree.ElementTree import ElementTree, Element, SubElement
import pandas as pd
import apsim.wrapper as apsim
from apsim.apsim_input_writer import create_mukey_runs

# Connect to database
dbconn = apsim.connect_to_database( 'database.ini' )

mukeys = [ '411333','2765537', '2800480', '2835021', '2835194', '2922031' ]

accola_soy_mgmt_2018 = json.loads( open( 'crop_jsons/accola_sfc_2018.json', 'r' ).read() )
accola_corn_mgmt_2019 = json.loads( open( 'crop_jsons/accola_cfs_2019.json', 'r' ).read() )

create_mukey_runs( mukeys, dbconn, 'sfc', 'accola.met', 'Accola', sfc_mgmt=accola_soy_mgmt_2018, cfs_mgmt=accola_corn_mgmt_2019)
