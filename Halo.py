# // Imports
from datetime import datetime, date
import json

# Local modules
from modules.haloModules import getHaloToken, getHaloAssets, updateHaloAsset, createHaloTicket, userSearch
from modules.miscModules import daysSince, valueExtract
from modules.msoftModules import winCheck
from modules.nAbleModules import getN_AbleInfo
from modules.macModules import macCheck
from modules.databaseModules import queryDB
# TODO #11 Only scan devices in "hiatus" or with "no checks" on occasion 
#TODO Before making public, status IDs must be switched


# Toggles #TODO #10 Find a better place for these(webUI?)
createAlertTickets = True # Enable ticket creation
osChecking = True # Enable checking of OS version
debugOnly = False # Disable asset updating
forceUpdate = True #Update assets even if they have already been checked today



# // Code
# Global Variables used to check how long a device has been online (day only)
today = date.today()
noneDate = date.fromisoformat("1970-01-01")


# Create token for Halo
sessionToken = getHaloToken()
assetList = getHaloAssets(sessionToken)


for device in assetList['assets']:
    optionalList = [] # Used for all optional checks 
    if device['third_party_id'] == 0 or device['assettype_name'] == 'Server': # Skip invalid devices (servers)
        continue

    # Get additional asset information from Halo
    haloDetailExpanded = getHaloAssets(sessionToken,device['id'])
    haloFieldNames = ['id','value']

    
    try: # Skips recently checked dvices. Reduces API requests to NAble, which can be quite slow.
        if forceUpdate == False and  datetime.fromisoformat(valueExtract(haloDetailExpanded['fields'],[159],haloFieldNames)[159]) > daysSince(1,'time'):
            print(f'Skipped {device["id"]}')
            continue
    except: # Try except used in case field does not have any data
        pass

    nAbleDetails = getN_AbleInfo(device['third_party_id'])
    if  nAbleDetails == False: # Skip device if N-Able returns an error
        continue
    



  
    """ List of Halo custom fields
    156 = HasAV - 1/Yes, 2/No
    160 = hasChecks - 1/Yes, 2/No
    """

    # Format output from workstations for Halo
    avCheck = '1' if int(nAbleDetails['mavbreck']) == 1 else '2' # Check for bitdefender #TODO #32 add detection for other AVs
    activeChecks = '1' if int(nAbleDetails['checks']['@count']) > 0 else '2' # Active checks on device (1 = yes)

    # AV Checks (1 = yes)
    optionalList += [{"id": "156", 
                    "value": '1' if int(nAbleDetails['mavbreck']) == 1 else '2'}]
    # Active Checks (1 = yes)
    optionalList += [{"id": "160", 
                    "value": '1' if int(nAbleDetails['checks']['@count']) > 0 else '2'}]
    

    # Date checks, commenting these out will likely cause chaos
    lastResponse = date.fromisoformat(nAbleDetails['lastresponse'][:10]) if nAbleDetails['lastresponse'] != '0000-00-00 00:00:00' else "Not Available"
    lastBoot =  date.fromisoformat(nAbleDetails['lastboot'][:10])
    if lastBoot == noneDate: lastBootString = 'Not Available'
    else: lastBootString = 'Today' if lastBoot == today else str(today - lastBoot).replace('0:00:00', '').replace(', ', '') + " ago"
    lastResponseString = 'Today' if lastResponse == today else str(today - lastResponse).replace('0:00:00', '').replace(', ', '') + " ago"  if lastResponse != "Not Available" else "Not Available"    

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
            "value": nAbleDetails['lastboot'] if lastBootString != "Not Available" else None}]

    

    # Halo asset fields to check
    haloCustomFIDs = [51,161,162]
    haloFieldNames = ['id','value']
    """ Halo Custom Fields
    51-STR = Device Model 
    161-INT = Do Not Contact Value
    162-INT = Supported Value
    """

    # N-Able asset fields to check
    nAbleCheckIDs = ['Script Check - Full Build Number']
    nAbleFieldNames = ['description','extra']
    """ nAble Custom Fields
    ?-STR = Windows full version (if windows device)
    """

    # Run value extract on devices (Halo, then nAble)
    haloValues = valueExtract(haloDetailExpanded['fields'],haloCustomFIDs,haloFieldNames)
    nAbleValues = valueExtract(nAbleDetails['checks']['check'],nAbleCheckIDs,nAbleFieldNames) if int(nAbleDetails['checks']['@count']) > 0 else 'No checks'
 

    # OS Type/version 
    if 'macOS' in nAbleDetails["os"]:
        osMain = 'macOS ' # macOS version is added later
        osMainRaw = osMain.strip() # Clean version of macOS, idk if we need this
    elif 'Microsoft' in nAbleDetails["os"]:
        osMain = 'Windows ' + str(nAbleDetails["os"].split(' ')[2])
    else:
        osMain = 'Unknown'

    # Windows and macOS checks
    if osChecking == True: # Confirm OS checking is enabled, check if current device is a mac
        if nAbleValues != 'No checks' and 'Windows' in osMain and nAbleCheckIDs[0] in nAbleValues.keys() and nAbleValues[nAbleCheckIDs[0]] not in [None,'Script awaiting download','Script timed out']:
            winDetails = winCheck(nAbleValues[nAbleCheckIDs[0]])
            osVersion = winDetails[1]
            osDetails = winDetails[0]
        elif 'macOS' in osMain:
            macDetails = macCheck(nAbleDetails["os"].split(" ")[1],haloValues[51] if 51 in haloValues else 'Unknown',haloValues[162] if 162 in haloValues else 'Unknown')
            osVersion = nAbleDetails["os"].split(" ")[1]
            osDetails = macDetails[0]
            osMain += macDetails[1] # Not inline to allow this to be used in later alert
        else:
            osVersion = 'Unknown'
            osDetails = 'Unknown'
        # TODO #33 Only append this field if data exists, do not overwrite existing information. 
        optionalList += [
            {"id": "162", #OS Status
                "value": osDetails},
            {"id": "102", # OS version
                "value": osVersion},
            {"id": "163", # Os "Type" (Windows 10, macOS,)
                "value": osMain}]

        """ OS Statuses - Sent back from macCheck system
        1 - Possibly Unsupported
        2 - Unsupported
        3 - OS Unsupported
        4 - Out of date
        5 - Up to date
        """

        """Asset Type IDs - This causes too many issues DO NOT USE FOR NOW
        133 - macOS 
        136 - Windows
        128 - Workstation"""
        """     {"id": "161", # If device is marked DO NOT CONTACT, only check every ?? #TODO #19 Confirm how oftern hiatus and DNC devices should be checked?
            "value": dncValue}        """


    # Send information to Halo 
    payload = json.dumps([{ # Device update payload
        "_dontaddnewfields": True,
        "isassetdetails": True,
        "fields": baseList + optionalList,
        "id": f"{device['id']}"}]) # Device ID
    
    # Attempt to update device if debug mode disabled
    if debugOnly == False:
        attemptUpdate = updateHaloAsset(payload,sessionToken)

    ### THIS SHOULD BE ItS OWN MODULE ###
    # Create ticket for devices that need reboot
    if 'id' not in haloDetailExpanded['users']: # Asset does not have user
        userID = None
        queries = {
        'deviceName':nAbleDetails['name'].split(' ')[0],
        'deviceDescription':nAbleDetails['description'].split(' ')[0],
        'deviceUser':nAbleDetails['username'],
        }
        for term in queries.values():
            queryLoad = {
                'pageinate':'false',
                "client_id": device['client_id'], # Client ID 
                # "site_id": device['site_id'], # Site ID
                'count': 3,
                'search':term
            }
            user = userSearch(sessionToken,queryLoad)
            if user['record_count'] > 0:
                userID = user['users'][0]['id']
                break
            
                
    else:
        userID = haloDetailExpanded['users'][0]['id']
    
    # Check that DNC isnt true, the device has active checks, and tickets should be created.
    if lastBootString != 'Not Available' and activeChecks == "1" and (haloValues['161'] if '161' in haloValues else 2) == 2 and createAlertTickets == True: 
        def ticketPayloadCreator(ticketString,ticType='alert'): # Sends payload to halo and creates ticket
            payload = json.dumps([{
                "tickettype_id": "21" if ticType == 'alert' else ticType, # Alert ticket type
                "client_id": device['client_id'], # Client ID 
                "site_id": device['site_id'], # Site ID
                "summary": ticketString, #Ticket Subject
                "details_html": "<p> </p>", # HTML formatted device
                "assets": [
                    {
                        "id": device['id'],  # Asset
                    }
                ],
                "user_id": userID,
                "donotapplytemplateintheapi": True, # Is this needed
                "form_id": "newticketf3f2abad-8df2-48b4-90ba-39b073c27c84", # Is this needed
                "dont_do_rules": True, # Is this needed
                }])
            createHaloTicket(payload,sessionToken)
            
            
            
        genericString = 'Your computer '
        if osChecking == True and osDetails in [2,3,4]: # Out of date device tickets
            baseString = f'{device["key_field"]} '
            
            osStrings =  {
                '2':f'is no longer supported and should be replaced',
                '3': f'is running an unsupported version of {osMainRaw}',
                '4': f'is running an outdated version of {osMain} and needs to be updated',
            }
            
            # Does not alert for possibly unsupported for now.
            ticketPayloadCreator(genericString + osStrings[str(osDetails)])
        if lastResponse > daysSince(5) and lastBoot < daysSince(19):
            print("Restart overdue") # DEBUG
            ticketPayloadCreator(f"{genericString} requires a restart. Last restarted {lastBootString}" )
        elif lastResponse < daysSince(30):
            print("Has not responded") # DEBUG
            ticketPayloadCreator(f"{genericString} was last online {lastResponseString} ")
        else: #Skip remaining code 
            continue
