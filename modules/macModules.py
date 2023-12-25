# macOS version checker + logger
#TODO #30 Cleanup all of this, it is a mess.


#Imports
import requests
from datetime import datetime, date
import json
from modules.miscModules import daysSince, toUnixInt
from modules.databaseModules import queryDB


def macVersions():
    """ Get latest macOS version information, update database """
    request = requests.get("https://endoflife.date/api/macos" + ".json") # Free API, not clear how often it updates, so should be taken with a grain of salt.
    response = json.loads(request.content)
    for versions in response:
        sqlQuery = 'INSERT OR IGNORE INTO osx_versions VALUES(?,?,?,?,?,?,?,?)'
        sqlData = (versions['codename'],versions['cycle'],toUnixInt(versions['releaseDate']),versions['latest'],toUnixInt(versions['latestReleaseDate']),'False' if versions['eol'] == False else 'True',versions['eol'] if versions['eol'] != False else None,toUnixInt(datetime.now()))
        queryDB(sqlQuery,sqlData,'default','commit')



def macCheck(osVerRaw,macModel,osSupported=False):
    """ Check current device macOS support (returned values below)
    Values returned (statuses)
    1 - Possibly Unsupported = No supported operating systems but entry has not been verified
    2 - Unsupported = No supported operating systems
    3 - OS Unsupported = OS is unsupported, device could be upgraded
    4 - Out-of-date
    5 - Up-to-date
    - """
    if osVerRaw[:2] == '10': # Check for old versioning format of macOS
        osVerMain = float(osVerRaw[:5])
        osVerSub = float(osVerRaw[6:])
        legacyOS = True
    else:
        osVerMain = int(osVerRaw[:2])
        osVerSub = float(osVerRaw[3:])
        legacyOS = False
    queryMacVer = 'SELECT os_name FROM osx_versions WHERE os_ver=?'
    queryMacData = (osVerMain,)
    macQuery = queryDB(queryMacVer,queryMacData,'default','searchone')[0]


    # Check macOS version status
    def checkMacOS(mode='eol'): 
        """ This tool checks the current version of macOS against the EOL API.

        osVerRaw is now just the number

        ## IGNORE BELOW ##
        osVerRaw will need to be trimmed on arrival for now. Maybe later it should be trimmed before it arrives?
        osVerRaw would look like this: macOS 10.13.6 build 17G14042 
        We only need the numbers, so the rest is discarded. As I'm typing this I'm realising it should be sent as just the number
        """
        request = requests.get("https://endoflife.date/api/macos/" + str(osVerMain) + ".json") # Free API, not clear how often it updates, so should be taken with a grain of salt.
        response = json.loads(request.content)

        eol = response["eol"] if response["eol"] == False else True # Grab EOL tag

        if legacyOS == True: # Legacy OS type conversion
            latestRelease = float(response['latest'][6:])
        else:
            latestRelease = float(response['latest'][3:])

        outdated = True if latestRelease > osVerSub else False # Computer is out of date?
        
        """ Possible return values
        3 - OS Unsupported
        4 - Out of date
        5 - Up to date
        """
        if mode == 'os': 
            return 3 if eol == True else 4 if eol == False and outdated == True else 5
        elif mode == 'eol': # Returns EOL status - True/False 
            return eol
    

    # Guess latest supported macOS per mac type
    def osxSupportedModels(report=False):
        sqlQuery1 = "SELECT * FROM mac_models WHERE model=?" # Search for mac model that was sent 
        sqlData1 = (macModel.lower(),)
        dbName = "os_details.db"
        sqlResponse = queryDB(sqlQuery1,sqlData1,dbName,'searchone')
        
        if sqlResponse != None and macModel.lower() in sqlResponse: #Confirm device exists in DB
            if sqlResponse[3] == 'True' and sqlResponse[5] == 'False' and osSupported== 2: # Change verified to True
                queryDB('UPDATE mac_models SET verified="True", last_updated=? WHERE model=?',(int(str(datetime.now().timestamp())[:10]),sqlResponse[0]),dbName,'commit')
            if sqlResponse[1] > osVerMain: # Current min os data is incorrect
                sqlQuery = "UPDATE mac_models SET min_supported_os=?, last_updated=?, verified='False' WHERE model=?"
                sqlData = (osVerMain,int(str(datetime.now().timestamp())[:10]),macModel.lower())
                queryDB(sqlQuery,sqlData,dbName,'commit')
            elif sqlResponse[2] < osVerMain: # Current max os data is incorrect
                sqlQuery = "UPDATE mac_models SET max_supported_os=?, max_os_is_eol=?, last_updated=?, verified='False' WHERE model=?"
                sqlData = (osVerMain,str(checkMacOS(osVerMain,True)),int(str(datetime.now().timestamp())[:10]),macModel.lower())
                queryDB(sqlQuery,sqlData,dbName,'commit')
            elif sqlResponse[3] == 'False' and date.fromtimestamp(sqlResponse[4]) < daysSince(30): #TODO #17 check if it has been over a month since info was updated.
                if checkMacOS(True) == True: # Check if macOS version is EOL 
                    sqlQuery = "UPDATE mac_models SET max_os_is_eol=?, last_updated=?, verified='False' WHERE model=?"
                    sqlData = (str(osVerRaw,True),int(str(datetime.now().timestamp())[:10]),macModel.lower())
                    queryDB(sqlQuery,sqlData,dbName,'commit')
        else: # Add device details.
            sqlQuery = "INSERT INTO mac_models VALUES(:model, :minOS, :maxOS, :maxEOL, :lastUpdated, :verified)"
            sqlDict = {
                'model': macModel.lower(),
                'minOS': osVerMain,
                'maxOS': osVerMain,
                'maxEOL': str(checkMacOS(True)),
                'lastUpdated': int(str(datetime.now().timestamp())[:10]),
                'verified': 'False'
            }
            queryDB(sqlQuery,sqlDict,dbName,'commit')
        if report == True:
            sqlR = queryDB(sqlQuery1,sqlData1,dbName,'searchone') # Send original query again to get relevant information.
            return  queryDB(sqlQuery1,sqlData1,dbName,'searchone')
    macInfo = osxSupportedModels(True) # Returns details about the current mac model
    if macInfo[3] == 'True': # Device reports that it is EOL
        if macInfo[5] == 'True': # EOL has been verified 
            return 2, macQuery # Return unsupported
        else: 
            return 1, macQuery # Return possibly unsupported
    else: # Mac is not EOL, now check current OS to see if it is unsupported or out of date
        return checkMacOS('os'), macQuery # Response should be valid
        
    
"""  Example call to end of life       
    {
        'codename': 'High Sierra', 
        'releaseDate': '2017-09-25', 
        'eol': '2020-12-01', 
        'latest': '10.13.6', 
        'latestReleaseDate': '2018-07-09', 
        'lts': False
        } """