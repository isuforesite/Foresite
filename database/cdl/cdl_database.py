#!/usr/bin/env Python

from sqlalchemy import create_engine
from configparser import ConfigParser


def config(filename="database.ini", section="postgresql"):
    # create a parser to parse through section of ini
    parser = ConfigParser()
    parser.read(filename)

    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(f"Section {section} not found in the {filename} file.")
    # return database information
    return db


# create a new database connection
def connect_to_db(filepath):
    # import db info from config file
    params = config(filepath)
    # create new connection from config info
    connstr = ("postgresql+psycopg2://{}:{}@{}:{}/{}").format(
        params["user"],
        params["password"],
        params["host"],
        params["port"],
        params["database"],
    )
    db_conn = create_engine(connstr)

    return db_conn
