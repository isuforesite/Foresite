from configparser import ConfigParser

def config( filename='database.ini', section='postgresql' ):
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
        raise Exception(f'Section {section} not found in the {filename} file.')
    #return database information
    return db
