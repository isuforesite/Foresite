#!/usr/bin/env Python

import getpass
from sqlalchemy import create_engine

def ConnectToDB( port, host, user, database ):
    passwd = getpass.getpass( database + ' password:' )
    connstr = ( 'postgresql+psycopg2://{}:{}@{}:{}/{}' ).format(
        user, passwd, host, str(port), database )
    db_conn = create_engine( connstr )

    return db_conn
