#!/usr/bin/env Python

from config import config
from sqlalchemy import create_engine

def ConnectToDB():
    params = config()
    connstr = ( 'postgresql+psycopg2://{}:{}@{}:{}/{}' ).format(
        params['user'], params['password'], params['host'], params['port'], params['database'] )
    db_conn = create_engine( connstr )

    return db_conn