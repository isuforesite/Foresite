#!/usr/bin/env Python

#%%
from os import system
from cdl_database import config

#%%
raster_path = 'cdl_raster/2019_30m_cdls.img'
schema = 'cdl'
table = 'cdl_30m_2019'
params = config()

#%%
dbhost = params['host']
dbport = params['port']
dbname = params['database']
dbuser = params['user']
dbpassword = params['password']

#%%
def cdl_callstr(rstr_path, dbschema, dbtable, host, port, name, user):
    callstr = 'raster2pgsql -Y -q -I -N 0 -s 102039 -t 50x50 {} {}.{} | psql -h {} -p {} -d {} -U {}'.format( raster_path, dbschema, dbtable, host, port, name, user)
    system( callstr )

if __name__ == "__main__":
    cdl_callstr(raster_path, schema, table, dbhost, dbport, dbname, dbuser)