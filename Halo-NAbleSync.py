# // Imports
from datetime import datetime, date
import json
import os

# Local modules
import modules.HaloPSA.HaloV3 as Halo
from modules.miscModules import daysSince, valueExtract, customFieldCheck, userInput
from modules.msoftModules import winCheck
from modules.nAbleModulesv3 import nAble
from modules.macModules import macCheck

version = "0.0.3"
#TODO Before making public, status IDs must be switched or it will be useless.
#TODO Add exception if checks are for EDR

settings = {
    'osChecking': False, # Enable checking of OS version
    'forceUpdate': False, #Update assets even if they have already been checked today
    'debugOnly': False, # Disable asset updating
    'debugLog': False,
}

settingsTextFriendly = {
    'osChecking': 'Should the OS version/status be checked?', 
    'forceUpdate': 'Should devices be re-checked, even if they were checked in the last 24 hours?', 
    'debugLog': 'Should log be displayed?',
    'debugOnly': 'DEBUG MODE? (Won\'t update assets)',
    
}

print(f'Halo-NAble Asset Sync script tool Version: {version}')
print('Settings\n')
for setting, text in settingsTextFriendly.items():
    validatedInput = userInput(text,['y','n'])
    if validatedInput == False:
        raise Exception('No valid input provided')
    else:
        settings[setting] = False if validatedInput.lower() == 'n' else True

# // Code
# Global Variables used to check how long a device has been online (day only)
today = date.today()
noneDate = date.fromisoformat("1970-01-01")

def debugText(string,warnLevel):
    """Display text for current action

    Args:
        string (string): Text to display
        section (warnLevel): Level
    """
    if settings['debugLog'] == True:
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f'{date} [{warnLevel}]: {string}')

# Halo.invoiceActivator()
# Create Halo Variables
hAssets = Halo.assets()
assetList = hAssets.search(assettype_id=128)
hRecurrInv = Halo.recurringInvoices()
hUsers = Halo.users()

# NAble
enAble = nAble('uk',key=os.getenv("NABLE_KEY"))

for device in assetList['assets']:

    debugText('starting next device',f'INFO-{device['id']}')
    
    optionalList = [] # Used for all optional checks 
    
    if device['third_party_id'] == 0 or device['assettype_name'] == 'Server': # Skip invalid devices (servers)
        debugText('No match, skipping device',f'WARN-{device['id']}')
        continue

    # Get additional asset information from Halo
    debugText(f'Getting device details from Halo','INFO')
    haloDetailExpanded  = hAssets.get(id=device['id'],includedetails=True)
    haloFieldNames = ['id','value']    

    
    try: # Skips recently checked dvices. Reduces API requests to NAble, which can be quite slow.
        if settings['forceUpdate'] == False and  datetime.fromisoformat(valueExtract(haloDetailExpanded['fields'],[159],haloFieldNames)[159]) > daysSince(1,'time'):
            debugText('Device was checked in the last 24 hours, skipping',f'INFO-{device['id']}')
            continue
        
    except: # Try except used in case field does not have any data
        debugText('Unable to determine last check date, continuing',f'ERROR-{device['id']}')
        pass
    debugText('Getting device details from n-Able',f'INFO-{device['id']}')
    nAbleDetails = enAble.deviceDetails(deviceid=device['third_party_id'])
    if  nAbleDetails == False: # Skip device if N-Able returns an error
        continue
    debugText('Got details from n-Able',f'INFO-{device['id']}')

  
    """ List of Halo custom fields
    156 = HasAV - 1/Yes, 2/No
    160 = hasChecks - 1/Yes, 2/No
    161 = Do Not Contact 1/True, 2/False
    164 = Bitlocker Identifier - [text]
    165 = Bitlocker Key - [text]
    166 = Has Bitlocker (1/Yes, 2/No)
    
    """

    debugText('Reformatting check data',f'INFO-{device['id']}')
    
    # Check for bitdefender
    avCheck = '1' if int(nAbleDetails['mavbreck']) == 1 else '2' 
    
    # Needed for bitlocker check
    bitID = None
    bitKey = None
    encryptionCheck = 2 # 2 = no
    hasEDR = False
    
    if int(nAbleDetails['checks']['@count']) > 0:
        for check in nAbleDetails['checks']['check']:
            if isinstance(check,str):
                continue
            
            # Get bitlocker keys from script check
            elif check['description'] == 'Script Check - Enable and Collect Bitlocker Keys' and check['extra'] != None:
                encryptionCheck = 1
                extraData = check['extra'].splitlines()

                for dataLine in extraData:
                    if 'Encrypted Drive Found - 1 - Identifier: ' in dataLine:
                        bitID = dataLine.split('{')[1].strip('}')
                    elif 'Encrypted Drive Found - 1 - Key::' in dataLine:
                        bitKey = dataLine.split('Key:: ')[1]
                ## extra
                
            # Check for EDR since there isnt a "feature" to check for this in the API
            elif check['description'] == 'Integration Check - EDR - Agent Health Status':
                avCheck = '1'
                hasEDR = True
                
    
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
    
    debugText('Checking last boot and last response information',f'INFO-{device['id']}')
    lastResponse = date.fromisoformat(nAbleDetails['lastresponse'][:10]) if nAbleDetails['lastresponse'] != '0000-00-00 00:00:00' else "Not Available"
    lastBoot =  date.fromisoformat(nAbleDetails['lastboot'][:10])
    if lastBoot == noneDate:
        lastBootString = 'Not Available'
        debugText('Last boot information not available',f'WARN-{device['id']}')
        
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
            "value": bitKey if bitID != None else None}
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

    
    debugText('Getting custom field',f'INFO-{device['id']}')    # Run value extract on devices (Halo, then nAble)
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

    # Windows and macOS checks
    if settings['osChecking'] == True: # Confirm OS checking is enabled, check if current device is a mac
        if nAbleValues != 'No checks' and 'Windows' in osMain and nAbleCheckNames[0] in nAbleValues.keys() and nAbleValues[nAbleCheckNames[0]] not in [None,'Script awaiting download','Script timed out']:
            debugText('Checking Windows versions',f'INFO-{device['id']}')
            winDetails = winCheck(nAbleValues[nAbleCheckNames[0]])
            osVersion = winDetails[1]
            osDetails = winDetails[0]
        elif 'macOS' in osMain:
            debugText('Checking MacOS versions',f'INFO-{device['id']}')
            macDetails = macCheck(nAbleDetails["os"].split(" ")[1],haloValues[51] if 51 in haloValues else 'Unknown',haloValues[162] if 162 in haloValues else 'Unknown')
            osVersion = nAbleDetails["os"].split(" ")[1]
            osDetails = macDetails[0]
            osMain += macDetails[1] # Not inline to allow this to be used in later alert
        else:
            debugText('Unknown OS, skipping',f'WARN-{device['id']}')
            osVersion = 'Unknown'
            osDetails = 'Unknown'
            
        # TODO #33 Only append this field if data exists, do not overwrite existing information. 
        debugText('OS checking completed',f'INFO-{device['id']}')
        optionalList += [
            {"id": "162", #OS Status
                "value": osDetails},
            {"id": "102", # OS version
                "value": osVersion},
            {"id": "163", # Os "Type" (Windows 10, macOS,)
                "value": osMain}]


    # Match users and assets where possible
    ### THIS SHOULD BE ItS OWN MODULE ###   
    
    debugText('Trying to match asset to user',f'INFO-{device['id']}') 
    userItem = None
    
    if  len(haloDetailExpanded['users']) != 0: # Asset already has a user
        userID = haloDetailExpanded['users'][0]['id']
        debugText(f'Asset already matched to user ID: {userID}',f'INFO-{device['id']}')

    else: # Asset does not have a user
        debugText('No user found, searching',f'INFO-{device['id']}')
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
                debugText('No matching user found',f'WARN-{device['id']}')
                continue
            elif users['record_count'] == 1:
                userID = users['users'][0]['id']
                userItem = [{'id':userID}]
                debugText(f'Found user, ID: {userID}',f'INFO-{device['id']}')
                break
            elif users['record_count'] > 1:
                debugText(f'Multiple matches found for search {term}, please choose correct input',f'WARN-{device['id']}')
                text = f'{haloDetailExpanded['client_name']} has multiple matches for {term}.  PC name is {haloDetailExpanded['key_field']}' 
                count = 1
                validChoices = []
                for user in users['users']: # Allows user to pick a 
                    text += f'\n {count}: {user['name']} from site {user['site_name']}'
                    validChoices +=[str(count)] 
                    count +=1
                text += f'\n {count}: None of the above\n'
                validChoices +=[str(count)]
                validatedInput = userInput(text, validChoices, 5)
                if validatedInput == False or int(validatedInput) == count:
                    debugText(f'No user chosen',f'INFO-{device['id']}')
                    continue
                else:
                    userID = users['users'][int(validatedInput)-1]['id'] # Our count starts at 1, but list count starts a 0
                    userItem = [{'id':userID}]
                debugText(f'Found user, ID: {userID}',f'INFO-{device['id']}')
                break
    
    
    
    # Send information to Halo 
    debugText('Attempting to update asset',f'INFO-{device['id']}')
    
        # Attempt to update device if debug mode disabled
    if settings['debugOnly'] == False:
        debugText(f'{device['id']} updated successfully',f'INFO-{device['id']}')
        hAssets.update( # Device update payload
            _dontaddnewfields= True,
            isassetdetails=True,
            fields= baseList + optionalList,
            id=device['id'], # Device ID
            users= userItem if userItem != None else None)
    elif settings['debugOnly'] == True:
        debugText('Debug mode enabled, asset not upated',f'INFO-{device['id']}')

    
    if activeChecks == '1':
        
        invoices = hRecurrInv.search(
            pageinate= False,
            client_id= device['client_id'])
        
        if len(invoices['invoices']) > 0:
            print('client has an invoice')
        else:
            print(f'No invoice for {device['client_id']}')
            #input()
    else:
        print('no checks')
        