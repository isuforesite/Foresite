#!/usr/bin/env Python

from config import config
from sqlalchemy import create_engine

#create a new database connection
def ConnectToDB():
    #import db info from config file
    params = config()
    #create new connection from config info
    connstr = ( 'postgresql+psycopg2://{}:{}@{}:{}/{}' ).format(
        params['user'], params['password'], params['host'], params['port'], params['database'] )
    db_conn = create_engine( connstr )

    return db_conn