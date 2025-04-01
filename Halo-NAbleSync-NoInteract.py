# // Imports
from datetime import datetime, date, timedelta
import os

# Local modules
from HaloPSA import Assets, RecurringInvoices, Users
from NAbleAPI import NAble
import logging
import os
import re
logger = logging.getLogger(__name__)

logging.basicConfig(filename='NSightSync.log', 
                    level=logging.WARNING, 
                    format='%(asctime)s %(levelname)-8s %(message)s', 
                    datefmt='%Y-%m-%d %H:%M:%S')

# HALO
HALO_TENANT = os.getenv('HALO_TENANT')
HALO_ID = os.getenv('HALO_CLIENT_ID')
HALO_SECRET = os.getenv('HALO_SECRET')

hAssets = Assets(HALO_TENANT,HALO_ID,HALO_SECRET)
hRecurrInv = RecurringInvoices(HALO_TENANT,HALO_ID,HALO_SECRET)
hUsers = Users(HALO_TENANT,HALO_ID,HALO_SECRET)

# NAble
enAble = NAble('uk',key=os.getenv("NABLE_KEY"))

version = "0.0.6" 
#TODO Before making public, status IDs must be switched or it will be useless.
#TODO set up a no interaction arg so this can be run on a server
#TODO remove OS checking, put that somewhere else.

# // Moved miscModules directly into script
def customFieldCheck(id,value):
    """ 
    Adds custom field to be used when updating asset ticket, etc
    
    :param id: Custom field ID
    :param value: Custom field value
    :return: Returns a list item to be added to your main list of fields
    """
    listItem = [
        {"id": id, 
        "value": value}]
    return listItem

def valueExtract(customFields,IDs,fieldName):
    # Extract values from custom fields
    fieldsDict = {}
    
    # Fix for single check devices
    if isinstance(customFields,dict):
            if customFields[fieldName[0]] in IDs and fieldName[1] in customFields:
                fieldsDict[customFields[fieldName[0]]] = customFields[fieldName[1]]
    else:
        for field in customFields:
            if field[fieldName[0]] in IDs and fieldName[1] in field:
                fieldsDict[field[fieldName[0]]] = field[fieldName[1]]
    return fieldsDict

def daysSince(day,value='day'):
    """ Input days to subtract.  Optionally, input 'time' to receive a datetime formatted response (default is date formatted)"""
    # Accepts INT input, returns todays date minus input number(days). Output can be used to compare to other date values.
    # value can be day or time. Time will return a full datetime string for comparison.
    return (date.today() - timedelta(days=day)) if value.lower() == 'day' else (datetime.now() - timedelta(days=day)) if value.lower() == 'time' else 'invalid request'

def bitlocker_key_extract(check_details:str):
    """Get Bitlocker keys from check details.  
    
    Only works with this check: https://me.n-able.com/s/article/BitLocker-Disk-Encryption-Monitoring-v2-N-central

    Args:
        check_details (str): Check details string

    Returns:
        list: List of drive names, keys, and identifiers (each is their own dictionary object)
    """
    
    bitlocker_data = check_details.split("Policy Output Parameters:")[1].splitlines()
    details = []
    for line_num, line in enumerate(bitlocker_data):
        if re.search(r"Encrypted Drive Found - \d - Name:: .:", line):
            details.append({
            'name': re.search(r"Encrypted Drive Found - \d - Name:: (.:)", line).group(1),
            'identifier': re.search(r"Encrypted Drive Found - \d - Identifier: (.*)",bitlocker_data[line_num+2]).group(1).strip("{}"),
            'key': re.search(r"Encrypted Drive Found - \d - Key:: (.*)",bitlocker_data[line_num+1]).group(1)})
            
    return details

# // Code
# Global Variables used to check how long a device has been online (day only)
today = date.today()
noneDate = date.fromisoformat("1970-01-01")


assetList = hAssets.search(assettype_id=128)

for device in assetList['assets']:
    logging.info(f'[{device['id']}] - Starting device')
    optionalList = [] # Used for all optional checks 
    
    if device['third_party_id'] == 0 or device['assettype_name'] == 'Server': # Skip invalid devices (servers)
        if device['assettype_name'] == 'Server':
            logging.warning(f'[{device['id']}] - Server, skipping device')
        else:
            logging.warning(f'[{device['id']}] - No third party ID, skipping device')
        continue

    # Get additional asset information from Halo
    logging.info(f'[{device['id']}] - Getting device details from Halo')
    haloDetailExpanded  = hAssets.get(id=device['id'],includedetails=True)
    haloFieldNames = ['id','value']    

    
    try: # Skips recently checked dvices. Reduces API requests to NAble, which can be quite slow.
        if datetime.fromisoformat(valueExtract(haloDetailExpanded['fields'],[159],haloFieldNames)[159]) > daysSince(1,'time'):
            logging.info(f'[{device['id']}] - Device was checked in the last 24 hours, skipping')
            continue
        
    except: # Try except used in case field does not have any data
        logging.warning(f'[{device['id']}] - Unable to determine last check date for device')
        pass
    logging.info(f'[{device['id']}] - Getting device details from NSight')
    try:
        nAbleDetails = enAble.deviceDetails(deviceid=device['third_party_id'],experimentalChecks=True)
    except ValueError: # Device no longer exists
        logging.error(f'[{device['id']}] - Unable to get device details for {device['third_party_id']} from NSight. Skipping')
        continue # TODO add an actual system here to deal with this. 
    
    if  nAbleDetails == False: # Skip device if N-Able returns an error #TODO is this needed?
        logging.error(f'[{device['id']}] - Unable to get device details for {device['third_party_id']} from NSight. Skipping')
        continue
    logging.info(f'[{device['id']}] - Got device details from NSight')

  
    """ List of Halo custom fields
    156 = HasAV - 1/Yes, 2/No
    160 = hasChecks - 1/Yes, 2/No
    161 = Do Not Contact 1/True, 2/False
    164 = Bitlocker Identifier - [text]
    165 = Bitlocker Key - [text]
    166 = Has Bitlocker (1/Yes, 2/No)
    175 = All Bitlocker Keys [memo]
    
    """
    
    # Check for bitdefender
    avCheck = '1' if int(nAbleDetails['mavbreck']) == 1 or int(nAbleDetails['edr']) == 1 else '2' 
    # Needed for bitlocker check
    bitID = None
    bitKey = None
    bitlocker_other = ""
    encryptionCheck = 2 # 2 = no
    hasEDR = False
    
    
    if int(nAbleDetails['checks']['@count']) > 0:
        for check in nAbleDetails['checks']['check']:
            if isinstance(check,str):
                continue
            elif check['description'] == 'Script Check - FileVault Status' and check['extra'] =='FileVault is On.': # macOS encryption
                encryptionCheck = 1
            # Get bitlocker keys from script check
            elif check['description'] == 'Script Check - Enable and Collect Bitlocker Keys' and check['extra'] != None:
                encryptionCheck = 1
                if check['extra'] == "Script timed out":
                    logging.warning(f'[{device['id']}] - Bitlocker check is failing!')
                else:
                    bitlocker_info = bitlocker_key_extract(check['extra'])
                    
                    bitID = bitlocker_info[0]['key']
                    bitKey = bitlocker_info[0]['identifier']
                        
                    bitlocker_other = ""
                    bitlocker_str = "{drive_letter}\n- Identifier: {identifier}\n- Key: {key}" # Blank string for extra keys
                    if len(bitlocker_info) > 1: # More than 1 key provided
                        for info in bitlocker_info[1:]: # Skip first item 
                            bitlocker_other += bitlocker_str.format(drive_letter=info['name'], identifier=info['identifier'], key=info['key']) +"\n"
                        
                
            # Check for EDR since there isnt a "feature" to check for this in the API
            elif check['description'] == 'Integration Check - EDR - Agent Health Status':
                avCheck = '1'
                hasEDR = True

    if hasEDR and avCheck == '1':
        pass
    elif not hasEDR and avCheck == '2': # No EDR
        pass
    else:
        logging.warning(f'[{device['id']}] - Conflicting results for EDR.  hasEDR={hasEDR} but avCheck={avCheck}')
    
    # Format output from workstations for Halo
    
    # Look for active checks on device that are NOT AV related
    avCheckNames = ['Integration Check - EDR - Agent Health Status','Integration Check - EDR - Threat Status','Script Check - EDR - VSS Status']
    if hasEDR == True: # There is EDR, see if any checks are not related to EDR.
        checkCount = int(nAbleDetails['checks']['@count'])
        for check in nAbleDetails['checks']['check']:
            if check['description'] in avCheckNames:
                checkCount -=1
        activeChecks = '1' if checkCount > 0 else '2'
            
        
    elif int(nAbleDetails['checks']['@count']) > 0: # No AV, but there are active checks
        activeChecks = '1'
    else: # No AV, no active checks
        activeChecks = '2'
        

    # AV Checks (1 = yes)
    optionalList += customFieldCheck(156,avCheck)
    
    # Active Checks (1 = yes)
    optionalList += customFieldCheck(160,activeChecks)
    
    # Encryption (bitlocker) check enabled (1 = yes)   
    optionalList += customFieldCheck(166,encryptionCheck)

    # Date checks, commenting these out will likely cause chaos
    
    logging.info(f'[{device['id']}] - Checking last boot and last response information')
    lastResponse = date.fromisoformat(nAbleDetails['lastresponse'][:10]) if nAbleDetails['lastresponse'] != '0000-00-00 00:00:00' else "Not Available"
    lastBoot =  date.fromisoformat(nAbleDetails['lastboot'][:10])
    if lastBoot == noneDate:
        lastBootString = 'Not Available'
        logging.warning(f'[{device['id']}] - Last boot information not available')
        
    else: 
        lastBootString = 'Today' if lastBoot == today else str(today - lastBoot).replace('0:00:00', '').replace(', ', '') + " ago"
    lastResponseString = 'Today' if lastResponse == today else str(today - lastResponse).replace('0:00:00', '').replace(', ', '') + " ago"  if lastResponse != "Not Available" else "Not Available"    

    # Base list of asset values
    baseList = [ 
        {"id": "155", # Last Boot
            "value": lastBootString},
        {"id": "154", # Last Response
            "value": lastResponseString},
        {"id": "159", # Last Checked
            "value": str(datetime.now()),},
        {"id": "158", # LLast Response Date
            "value": nAbleDetails['lastresponse'],},
        {"id": "157", # Last Boot Date TODO # Make this modular
            "value": nAbleDetails['lastboot'] if lastBootString != "Not Available" else None},
        {"id": "164", # Bitlocker ID
            "value": bitID if bitID != None else None},
        {"id": "165", # Bitlocker Key
            "value": bitKey if bitKey != None else None},
        {"id": "175", # Bitlocker Additional Keys Field
            "value": bitlocker_other if bitlocker_other != "" else None}
        ]
    

    # Halo asset fields to check
    haloCustomFIDs = [51,161,162]
    haloFieldNames = ['id','value']
    """ Halo Custom Fields
    51-STR = Device Model 
    161-INT = Do Not Contact Value
    162-INT = Supported Value
    """

    # N-Able asset fields to check
    nAbleCheckNames = ['Script Check - Full Build Number']
    nAbleFieldNames = ['description','extra']
    """ nAble Custom Fields
    ?-STR = Windows full version (if windows device)
    """

    
    haloValues = valueExtract(haloDetailExpanded['fields'],haloCustomFIDs,haloFieldNames)
    nAbleValues = valueExtract(nAbleDetails['checks']['check'],nAbleCheckNames,nAbleFieldNames) if int(nAbleDetails['checks']['@count']) > 0 else 'No checks'


    # OS Type/version 
    if 'macOS' in nAbleDetails["os"]:
        osMain = 'macOS ' # macOS version is added later
        osMainRaw = osMain.strip() # Clean version of macOS, idk if we need this
    elif 'Microsoft' in nAbleDetails["os"]:
        osMain = 'Windows ' + str(nAbleDetails["os"].split(' ')[2])
    else:
        osMain = 'Unknown'


    optionalList += [
        {"id": "163", # Os "Type" (Windows 10, macOS,)
            "value": osMain}]
    
    logging.info(f'[{device['id']}] - Trying to match asset to user')
    userItem = None
    
    if  len(haloDetailExpanded['users']) != 0: # Asset already has a user
        userID = haloDetailExpanded['users'][0]['id']
        logging.info(f'[{device['id']}] - Asset already matched to user ID: {userID}')

    else: # Asset does not have a user
        userID = None
        queries = {
        'deviceName':nAbleDetails['name'].split(' ')[0],
        'deviceDescription':nAbleDetails['description'].split(' ')[0],
        'deviceUser':nAbleDetails['username'],
        }
        for term in queries.values():
            users = hUsers.search(
                pageinate = False,
                client_id = device['client_id'], # Client ID 
                count = 3,
                search = term,
            )
            if users['record_count'] == 0:
                logging.info(f'[{device['id']}] - No users found to match')
                continue
            elif users['record_count'] == 1:
                userID = users['users'][0]['id']
                userItem = [{'id':userID}]
                logging.info(f'[{device['id']}] - Found user with ID {userID}, matching')
                break
            elif users['record_count'] > 1:
                logging.error(f'[{device['id']}] - Multiple matches found for search {term}, please set manually')
                break
    
        # Attempt to update device if debug mode disabled
    if True:
        notSent = 0 # Request has not been sent.
        while notSent < 10:
            try:
                updateAsset = hAssets.update( # Device update payload
                    _dontaddnewfields= True,
                    isassetdetails=True,
                    fields= baseList + optionalList,
                    id=device['id'], # Device ID
                    users= userItem if userItem != None else None)
                logging.info(f'[{device['id']}] - Device updated successfully')
                break
            
            except:
                notSent +=1
        if notSent == 10:
            logging.error(f'[{device['id']}] - Device failed to update')
    else:
        logging.info(f'[{device['id']}] - Debug mode enabled, asset not upated')
        