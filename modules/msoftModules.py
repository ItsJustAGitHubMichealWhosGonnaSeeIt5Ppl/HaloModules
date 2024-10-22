# Microsoft functions
# Web scraper and tool to update HaloPSA device info

import requests
from bs4 import BeautifulSoup
import xmltodict
from datetime import date, datetime
from modules.databaseModules import queryDB
from modules.miscModules import toUnixInt, daysSince


def msoftVerHistoryScraper(link): 
    # Get windows versions

    def eolCheck(input): 
        # Checks if version of Windows is supported still, was doing it inline but this is cleaner
        if input == 'End of servicing':
            return 'True'
        input = date.fromisoformat(input)
        # Realistically, 'Unknown' should never be returned but I wanted to be safe!
        return 'False' if input > date.today() else 'True' if input < date.today() else 'Unknown'
    

    scapeResultRaw = requests.get(link)
    soupScrape = BeautifulSoup(scapeResultRaw.content, 'html.parser')
    goodSoup = soupScrape.find('table') # Finds the first table (which happens to be the one we need)
    tableRows = goodSoup.find_all('tr', class_='highlight')
    supportedOSList = [] # Used later when getting the sub versions
    for x in tableRows: 
        dictUnformatted = xmltodict.parse(str(x))
        dictUnformatted = dictUnformatted['tr']['td']
        sqlQMain = 'INSERT OR REPLACE INTO win_versions_main VALUES(?, ?, ?, ?, ?, ?, ?, ?)'
        sqlValMain = (int(str(dictUnformatted[4]).split('.')[0]),dictUnformatted[0],toUnixInt(dictUnformatted[2]),int(str(dictUnformatted[4]).split('.')[1]),toUnixInt(dictUnformatted[3]),eolCheck(dictUnformatted[5]),eolCheck(dictUnformatted[6]),toUnixInt(date.today()))
        queryDB(sqlQMain,sqlValMain)
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
        if eolCheck(dictUnformatted[5]) in ['False','Unknown']:
            supportedOSList.append(int(str(dictUnformatted[4]).split('.')[0]))

    # Find the releases from the lists at the bottom of the page
    oldReleases = soupScrape.find_all('table', class_="cells-centered") # Find older OS versions 
    

    for y in oldReleases:
        if any(str(s) in str(y) for s in supportedOSList):
            oldReleaseDict = xmltodict.parse(str(y)) # Convert the supported OS version to a dict for easier data extraction
            for x in oldReleaseDict['table']['tbody']['tr']:
                if 'th' in x:
                    continue # Skips the table header. Probably a nicer way to do this, but I don't know how
                sqlQuery = "INSERT OR REPLACE INTO win_versions_sub VALUES(?,?,?)"
                sqlValues = (x['td'][2],toUnixInt(x['td'][1]),toUnixInt(date.today()))
                queryDB(sqlQuery,sqlValues)

                

def msoftVersions():
    # Windows 10 and 11 have different URLs, but only 11 actually says its 11... 
    winVers = {
    'win10': 'https://learn.microsoft.com/en-gb/windows/release-health/release-information',
    'win11': 'https://learn.microsoft.com/en-gb/windows/release-health/windows11-release-information'
    }
    for versions in winVers.values(): 
        msoftVerHistoryScraper(versions)


def winCheck(osVerRaw):
    """ OS Statuses - Sent back from macCheck system
    1 - Possibly Unsupported
    2 - Unsupported
    3 - OS Unsupported
    4 - Out of date
    5 - Up to date
    """
    #TODO #23 Always check and update DB first
    osVerMajor = int(osVerRaw.split('.')[2])
    osVerMinor = int(osVerRaw.split('.')[3])

    sqlQuery = "SELECT * FROM win_versions_main WHERE os_build_main=?"
    sqlData = (osVerMajor,)
    sqlResult = queryDB(sqlQuery,sqlData,'default','searchone')
    if sqlResult != None and daysSince(13) > date.fromtimestamp(sqlResult[7]):
        msoftVersions()
        sqlResult = queryDB(sqlQuery,sqlData,'default','searchone') # Re-run search with updated information
    sqlFQuery = "SELECT * FROM win_versions_sub WHERE os_build=?"
    sqlFData = (f'{osVerMajor}.{osVerMinor}',)
    sqlFullBuild = queryDB(sqlFQuery,sqlFData,'default','searchone')

    # TODO #34 Check minor version list
    osString = f'{osVerMajor}.{osVerMinor} ({sqlResult[1] if sqlResult != None else "Unknown"})'
    def osStatusCheck():
        if sqlFullBuild == None:
            return 1 # Full version string not found, report possibly unsupported.
        if sqlResult[5] == 'True': # Device OS is EOL
            return 3
        elif sqlResult[3] != osVerMinor and daysSince(13) > date.fromtimestamp(sqlFullBuild[1]): # OS is out of date
            return 4
        elif sqlResult[3] == osVerMinor or daysSince(13) < date.fromtimestamp(sqlFullBuild[1]): # OS is up to date or in 14 day grace period
            return 5
        else:
            return 1
    return osStatusCheck(), osString
    



# Trying something new for this, anything I had to look up will be in here
""" Sources, References, and other things that helped make this script
# Literally the entire beautiful soup documentation page and geeksforgeeks page
## https://www.geeksforgeeks.org/implementing-web-scraping-python-beautiful-soup/?ref=lbp
## https://www.crummy.com/software/BeautifulSoup/bs4/doc/
# Scaper portion was heavily Inspired by RB_635 in this thread. I used some of the same find_all() things. Would have been completely stumped without it!
## https://answers.microsoft.com/en-us/windows/forum/all/is-there-an-api-that-will-list-out-all-windows/3e3c3d03-fda8-4316-8129-0b0ac7d24a20
# Couldn't figure out why my list of supported OS versions was not comparing to the dictionary in OldReleaseDict.
## https://stackoverflow.com/questions/43033128/check-if-any-of-a-list-of-strings-is-in-another-string
# Kept ending up with a PyCache file in my github commit
## https://stackoverflow.com/questions/6794717/git-ignore-certain-files-in-sub-directories-but-not-all
"""