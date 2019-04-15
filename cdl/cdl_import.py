#!/usr/bin/env Python

import os

rstr_path = '2009_30m_cdls.img'
dbschema = 'cdl'
dbtable = 'cdl_30m_2009'

host = '111.111.111.11'
port = 1111
dbname = ''
user = ''

callstr = 'raster2pgsql -Y -q -I -N 0 -s 102039 -t 50x50 {} {}.{} | psql -h {} -p {} -d {} -U {}'.format( rstr_path, dbschema, dbtable, host, port, dbname, user )

os.system( callstr )
