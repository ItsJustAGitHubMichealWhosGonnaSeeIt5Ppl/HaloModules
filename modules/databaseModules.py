# Database functions + database creation

import sqlite3


def createDB(input = 'all'):
    # Create databases, only needs to be run once
    # By default, all DBs will be created.
    #TODO #14 Fix DB path to work anywhere
    database = sqlite3.connect("os_details.db") 
    cursor = database.cursor()


    # OSX versions 
    cursor.execute("""CREATE TABLE if NOT EXISTS osx_versions(
        os_name TEXT PRIMARY KEY,
        os_ver REAL,
        os_release_date INT,
        os_ver_latest TEXT,
        os_ver_latest_date INT,
        os_eol TEXT,
        os_eol_date INT,
        last_updated INT
    )""")

    """ Guide for osx_versions
    os_name = "codename" of the OS (Catalina, Big Sur)
    os_ver = First digit(s) of the OS (eg 10.15 or 13)
    os_release_date = Release date in unix
    os_ver_latest = Latest available version of the OS (EG 10.15.7 or 13.7.2)
    os_ver_latest_date = release date of latest verion in unix
    os_eol = True/False
    os_eol_date = Date that OS support stopped
    last_updated = last time this entry was updated
    """
    

    # Mac models and supported OSes (no API for this annoyingly)
    cursor.execute("""CREATE TABLE if NOT EXISTS mac_models(
        model TEXT PRIMARY KEY,
        min_supported_os REAL,
        max_supported_os REAL,
        max_os_is_eol TEXT,
        last_updated INT,
        verified TEXT
    )""")

    """ Guide for mac_models 
    model = Mac model (macbookair10,1)
    min_supported_os = Minimum supported OS
    max_supported_os = Maximum supported OS 
    max_os_is_eol = True/False. Set based on above inputs
    last_updated = last time this entry was updated
    verified = True/False. This entries information has been manually verified.
    """


    # Windows major versions 
    cursor.execute(""" CREATE TABLE if NOT EXISTS win_versions_main(
        os_build_main INT PRIMARY KEY,
        os_build_friendly TEXT,
        release_date INT,
        os_build_latest INT,
        os_build_latest_date INT,
        os_eol TEXT,
        os_eol_lts TEXT,
        last_updated INT,
        FOREIGN KEY(os_build_latest) REFERENCES win_versions_minor(os_build)
    )""")

    """ Guide for win_versions_main
    os_build_main - Main OS 19045...
    os_build_friendly - Name 22H2
    release_date - Initial release UNIX
    os_build_latest - Latest build number ...3803
    os_build_latest_date - Latest release date UNIX
    os_eol - True/False
    os_eol_lts - True/False
    last_updated - Last updated UNIX
    """


    # Windows minor versions
    cursor.execute(""" CREATE TABLE if NOT EXISTS win_versions_sub(
        os_build TEXT PRIMARY KEY,
        release_date INT,
        last_updated INT
    )""")

    """ Guide for win_versions_sub
    os_build - Latest build number ...3803
    release_date Release date UNIX
    last_updated Last updated UNIX
    """



def queryDB(query,data,dbName='default',qType='commit'):
    # Execute SQL here, maybe it a better name
    # Can be run with only 2 params.
    qType = qType.lower()
    db = "os_details.db" if dbName == 'default' else dbName 
    database = sqlite3.connect(db)
    cursor = database.cursor()
    cursor.execute(query,data)
    if qType == 'commit': 
        database.commit() # Save changes
    elif qType == 'searchall': 
        return cursor.fetchall()
    elif qType == 'searchone': 
        return cursor.fetchone()