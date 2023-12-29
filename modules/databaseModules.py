# Database functions + database creation

import sqlite3


def createDB(dbName='default',create='default'):
    # Create databases, only needs to be run once
    # By default, all DBs will be created.
    #TODO #14 Fix DB path to work anywhere
    if dbName == 'default':
        database = sqlite3.connect("os_details.db")
    else:
        database = sqlite3.connect(dbName)
    cursor = database.cursor()


    # OSX versions
    if create == 'default':
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
    else:
        cursor.execute(""" CREATE TABLE IF NOT EXISTS products(
            id INT PRIMARY KEY,
            name TEXT,
            status INT,
            desc TEXT,
            purchase_desc TEXT,
            STOCK INT,
            base_price INT,
            supplier_id INT,
            supplier_name TEXT,
            'promptforprice': False,
            'taxcode': 10,
            'taxcodeother': 0,
            'costprice': 12.5,
            'accountsid': '4G Dongle',
            'nominalcode': '200',
            'costingmethod': 0,
            xero_id (shaccountsid),
            'markupperc': 0.0,
            recurring INT,
            recurring_price TRUE
            'xero_id_also?': 'b1a80afe-05d9-4a21-a403-37830665a916',
            'purchasenominalcode': '',
            'salestaxincluded': False,
            'purchasetaxincluded': False,
            'taxable': True,
            'assetaccountcode': 0,
            'xero_tenant_id': '0a9b508f-ddf9-4688-b33e-e208864d68c5',
            'income_account_name': '',
            'expense_account_name': '',
            'asset_account_name': '',
            'qbosku': '',
            'qbocategoryid': '',
            'qbocategoryname': '',
            'autotaskserviceid': -1,
            'autotaskproductid': -1,
            'iscontractitem': False,
            'dontinvoice': False,
            'kashflowid': 0,
            'kashflow_tenant_id': 0,
            'linked_item_id': 0,
            'update_recurring_invoice_price': False,
            'update_recurring_invoice_cost': False,
            'snelstart_id': '',
            'snelstart_department_id': '',
            'snelstart_department_name': '',
            'maxitemdiscount': 100.0,
            'item_default_billing_period': 3,
            'primaryimageid': 0,
            'lastmodified': '2023-10-31T14:40:11.26',
            'item_group_nominalcode': '',
            'item_group_nominalcode_purchase': '',
            'recurringcost': 0.0,
            'dbc_company_id': '',
            'type': 0,
            'sage50uk_department_id': 0,
            'dont_track_stock': False}

        ) """)


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