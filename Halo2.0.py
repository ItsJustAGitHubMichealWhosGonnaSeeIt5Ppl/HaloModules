# // Imports
from datetime import datetime, date
import json

# Local modules
import modules.HaloPSA.HaloV2 as Halo
from modules.miscModules import daysSince, valueExtract, customFieldCheck
from modules.msoftModules import winCheck
from modules.nAbleModules import getN_AbleInfo
from modules.macModules import macCheck


version = '0.0.2'
# Now checks for EDR and MAV
# Now checks for Bitlocker script and exports this data into Halo


# TODO #11 Only scan devices in "hiatus" or with "no checks" on occasion 
#TODO Before making public, status IDs must be switched

#TODO #3 When creating macOS update tickets, note the device type in the ticket body.

settings = {
    'createAlertTickets': False, # Enable ticket creation
    'osChecking': False, # Enable checking of OS version
    'forceUpdate': False, #Update assets even if they have already been checked today
    'existingOnly': False, # Only update existing asset tickets, do not scan an asset if there is no currently active ticket.
    'currencyUpdate': False,
    'debugOnly': False, # Disable asset updating
}

settingsTextFriendly = {
    'createAlertTickets': 'Should alert tickets be created/updated?', 
    'existingOnly': 'Should only existing alert tickets be updated?',
    'osChecking': 'Should the OS version/status be checked?', 
    'forceUpdate': 'Should devices be re-checked, even if they were checked in the last 24 hours?', 
    'currencyUpdate': 'Should currency updates be done on items?',
    'debugOnly': 'DEBUG MODE?',
}

print(f'Halo-Python script tool Version: {version}')
print('N-Able asset sync settings\n')
for setting, text in settingsTextFriendly.items():
    needValidInput = True
    while needValidInput == True:
        userInput = input(text + ' Y/N: ')
        if userInput.capitalize() in ['Y','N']:
            needValidInput = False
    settings[setting] = False if userInput.capitalize() == 'N' else True

# // Code
# Global Variables used to check how long a device has been online (day only)
today = date.today()
noneDate = date.fromisoformat("1970-01-01")

# Halo.invoiceActivator()
# Create Halo Variables
hAssets = Halo.asset()
hTickets = Halo.ticket()
assetList = hAssets.getAll()


if settings['currencyUpdate'] == True:
    # requires string in Internal Reference
    # EG USD:P15C15
    # Update currency on items
    # Currently assumes item is recurring
    hCurrency = Halo.currency()
    hItem = Halo.items()
    
    usdOnlyQuery = {
        'pageinate':'false',
        'order':'name',
        'advanced_search': [{
            'filter_name':'internalreference',
            'filter_type':4,
            'filter_value':'USD'
        }]}
        
    usdItems = hItem.search(usdOnlyQuery)
    
    ## 1 / (Exchange rate) will give correct currency conversion
    
    for currency in hCurrency.getAll():
        if currency['code'] == 'USD':
            USDtoGBP = 1 / currency['conversion_rate']
            break
    
    
    
    for product in usdItems['items']:
        gbpCost = str(int(product['internalreference'].split('C')[1]) * USDtoGBP)[0:5]
        gbpPrice = str(int(product['internalreference'].split('C')[0].replace('USD:P','')) * USDtoGBP)[0:5]
        newPayload = {
            'id': product['id'],
            'costprice': gbpCost,
            "recurringcost": gbpCost,
            
            "baseprice": gbpPrice,
            "recurringprice": gbpPrice,
            
            "update_recurring_invoice_price": 'true',
            "update_recurring_invoice_cost": 'true',
            }
        updateAttempt = hItem.update(newPayload)
        print(updateAttempt) 


for device in assetList['assets']:

    print(f'{datetime.now()}: Starting next device')
    
    optionalList = [] # Used for all optional checks 
    
    if device['third_party_id'] == 0 or device['assettype_name'] == 'Server': # Skip invalid devices (servers)
        print(f'{datetime.now()}: Skipping device')
        continue

    # Get additional asset information from Halo
    print(f'{datetime.now()}: Attempting to get more details about device from Halo')
    haloDetailExpanded  = hAssets.get(device['id'])
    haloFieldNames = ['id','value']
    
    print(f'{datetime.now()}: Got details from Halo')
    if settings['existingOnly'] == True and haloDetailExpanded['open_ticket_count'] == 0:
        print(f'{datetime.now()}: existingOnly is enabled and this asset has no tickets, skipping')
        continue
    
    try: # Skips recently checked dvices. Reduces API requests to NAble, which can be quite slow.
        if settings['forceUpdate'] == False and  datetime.fromisoformat(valueExtract(haloDetailExpanded['fields'],[159],haloFieldNames)[159]) > daysSince(1,'time'):
            print(f'Skipped {device["id"]}')
            continue
    except: # Try except used in case field does not have any data
        pass
    print(f'{datetime.now()}: Attempting to get n-Able asset details...')
    nAbleDetails = getN_AbleInfo(device['third_party_id'])
    if  nAbleDetails == False: # Skip device if N-Able returns an error
        continue
    print(f'{datetime.now()}: Got details from N-Able')

  
    """ List of Halo custom fields
    156 = HasAV - 1/Yes, 2/No
    160 = hasChecks - 1/Yes, 2/No
    164 = Bitlocker Identifier - [text]
    165 = Bitlocker Key - [text]
    """

    print(f'{datetime.now()}: Re-formatting data')
    
    avCheck = '1' if int(nAbleDetails['mavbreck']) == 1 else '2' # Check for bitdefender
    
    # Needed for bitlocker check
    bitID = None
    bitKey = None
    
    if int(nAbleDetails['checks']['@count']) > 0:
        for check in nAbleDetails['checks']['check']:
            if isinstance(check,str):
                continue
            
            # Get bitlocker keys from script check
            if check['description'] == 'Script Check - Enable and Collect Bitlocker Keys' and check['extra'] != None:
                extraData = check['extra'].splitlines()

                for dataLine in extraData:
                    if 'Encrypted Drive Found - 1 - Identifier: ' in dataLine:
                        bitID = dataLine.split('{')[1].strip('}')
                    elif 'Encrypted Drive Found - 1 - Key::' in dataLine:
                        bitKey = dataLine.split('Key:: ')[1]
                ## extra
                
            # Check for EDR since there isnt a "feature" to check for this in the API
            if check['description'] == 'Integration Check - EDR - Agent Health Status':
                avCheck = '1'
                
    
    # Format output from workstations for Halo
    activeChecks = '1' if int(nAbleDetails['checks']['@count']) > 0 else '2' # Active checks on device (1 = yes)

    # AV Checks (1 = yes)
    optionalList += customFieldCheck(156,avCheck)
    
    # Active Checks (1 = yes)
    optionalList += customFieldCheck(160,activeChecks)

    # Date checks, commenting these out will likely cause chaos
    lastResponse = date.fromisoformat(nAbleDetails['lastresponse'][:10]) if nAbleDetails['lastresponse'] != '0000-00-00 00:00:00' else "Not Available"
    lastBoot =  date.fromisoformat(nAbleDetails['lastboot'][:10])
    if lastBoot == noneDate:
        lastBootString = 'Not Available'
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
    print(f'{datetime.now()}: Finished initial data reformat')
    

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

    
    print(f'{datetime.now()}: Getting relevant information from asset')
    # Run value extract on devices (Halo, then nAble)
    haloValues = valueExtract(haloDetailExpanded['fields'],haloCustomFIDs,haloFieldNames)
    nAbleValues = valueExtract(nAbleDetails['checks']['check'],nAbleCheckIDs,nAbleFieldNames) if int(nAbleDetails['checks']['@count']) > 0 else 'No checks'
    print(f'{datetime.now()}: Got information, checking OS')


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
        if nAbleValues != 'No checks' and 'Windows' in osMain and nAbleCheckIDs[0] in nAbleValues.keys() and nAbleValues[nAbleCheckIDs[0]] not in [None,'Script awaiting download','Script timed out']:
            print(f'{datetime.now()}: Checking Windows versions')
            winDetails = winCheck(nAbleValues[nAbleCheckIDs[0]])
            osVersion = winDetails[1]
            osDetails = winDetails[0]
        elif 'macOS' in osMain:
            print(f'{datetime.now()}: Checking MacOS versions')
            macDetails = macCheck(nAbleDetails["os"].split(" ")[1],haloValues[51] if 51 in haloValues else 'Unknown',haloValues[162] if 162 in haloValues else 'Unknown')
            osVersion = nAbleDetails["os"].split(" ")[1]
            osDetails = macDetails[0]
            osMain += macDetails[1] # Not inline to allow this to be used in later alert
        else:
            print(f'{datetime.now()}: Unknown OS, skipping')
            osVersion = 'Unknown'
            osDetails = 'Unknown'
        # TODO #33 Only append this field if data exists, do not overwrite existing information. 
        print(f'{datetime.now()}: OS checking comepleted')
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


    print(f'{datetime.now()}: Checking if asset already has a user')
    ### THIS SHOULD BE ItS OWN MODULE ###
    # Create ticket for devices that need reboot
    userItem = None
    if  len(haloDetailExpanded['users']) != 0: # Asset already has a user
        print(f'{datetime.now()}: Device already has a user')
        userID = haloDetailExpanded['users'][0]['id']
        
    else: # Asset does not have a user
        print(f'{datetime.now()}: Device does not have a user, trying to match')
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
            user = Halo.userSearch(queryLoad)
            if user['record_count'] > 0:
                userID = user['users'][0]['id']
                userItem = [{'id':userID}]
                break 
    print(f'{datetime.now()}: User check complete')

    print(f'{datetime.now()}: Attempting to update asset...')
    # Send information to Halo 
    
    payload = json.dumps([{ # Device update payload
        "_dontaddnewfields": True,
        "isassetdetails": True,
        "fields": baseList + optionalList,
        "id": f"{device['id']}", # Device ID
        "users": userItem if userItem != None else ''}])
        # Attempt to update device if debug mode disabled
    if settings['debugOnly'] == False:
        hAssets.update(payload)
        print(f'{datetime.now()}: Asset updated')
    
    def ticketPayloadCreator(ticketString,existingTicketID=False,action='alert'): # Sends payload to halo and creates ticket
        if existingTicketID is not False:
            payload = json.dumps([{
            'id': existingTicketID[0],
            "summary": ticketString,
            'apply_rules': 'true',
            "details": f"Previous Summary {existingTicketID[1]}", # HTML formatted info
            'status_id':'23', # Needs update
            }])
        else:
            payload = json.dumps([{
                "tickettype_id": "21" if action == 'alert' else action, # Alert ticket type
                "client_id": device['client_id'], # Client ID 
                "site_id": device['site_id'], # Site ID
                "summary": ticketString, #Ticket Subject
                "details_html": f"<p> </p>", # HTML formatted info
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
        hTickets.create(payload)
        
        print(existingTicketID)


    def openTicketMatch():
        """ Find existing open tickets related to an asset """
        assetQuery = {
                'pageinate':'false',
                'open_only': 'true',
                ''
                "asset_id": device['id'], # Client ID 
            }
        openTickets = hTickets.search(assetQuery)
        restart = []
        offline = []
        update = []
        if openTickets['record_count'] > 0: 
            for ticket in openTickets['tickets']:
                if ticket['status_id'] == 20: # Previously completed tickets
                    print(f'{datetime.now()}: Ticket is completed')
                    continue # Skip
                if 'restart' in ticket['summary']:
                    if lastResponse > daysSince(5) and lastBoot > daysSince(19):
                        hTickets.updateStatus(ticket['id']) # Close ticket if issue no longer present
                    if restart == []:
                        restart = [
                        {'rID': ticket['id'], 
                        'rSMRY': ticket['summary']}]
                    else:
                        if int(restart[0]['rID']) > int(ticket['id']):
                            newID = restart[0]['rID']
                            oldID = ticket['id']
                        else:
                            oldID = restart[0]['rID']
                            newID = ticket['id']
                        hTickets.merge(oldID,newID)
                elif 'online' in ticket['summary']:
                    if lastResponse > daysSince(30):
                        hTickets.updateStatus(ticket['id'])
                    if offline == []:
                        offline = [
                        {'oID': ticket['id'], 
                        'oSMRY': ticket['summary']}]
                    else:
                        if int(offline[0]['oID']) > int(ticket['id']):
                            newID = offline[0]['oID']
                            oldID = ticket['id']
                        else:
                            oldID = offline[0]['oID']
                            newID = ticket['id']
                            offline = [
                            {'oID': ticket['id'], 
                            'oSMRY': ticket['summary']}]
                        hTickets.merge(oldID,newID)
                elif 'running an' in ticket['summary'] or 'no longer supported' in ticket['summary'] or 'computer is' in ticket['summary']:
                    if ['osChecking'] == True and osDetails not in [2,3,4]:
                        hTickets.updateStatus(ticket['id'])
                    if update == []:
                        update = [
                        {'uID': ticket['id'], 
                        'uSMRY': ticket['summary']}]
                    else:
                        if int(update[0]['uID']) > int(ticket['id']):
                            newID = update[0]['uID']
                            oldID = ticket['id']
                        else:
                            oldID = update[0]['uID']
                            newID = ticket['id']
                        hTickets.merge(oldID,newID)
                    
        return restart if restart != [] else False, offline if offline != [] else False, update if update != [] else False
    
    # ^ Terrible awful please fix ^
    
    print(f'{datetime.now()}: Checking open tickets for asset')
    deviceTickets = openTicketMatch()

    # Check that DNC isnt true, the device has active checks, and tickets should be created.
    if lastBootString != 'Not Available' and activeChecks == "1" and (haloValues[161] if 161 in haloValues else 2)   != 1 and settings['createAlertTickets'] == True: 

        genericString = 'Your computer'
        if settings['osChecking'] == True and osDetails in [2,3,4]: # Out of date device tickets
            baseString = f'{device["key_field"]} '
            
            osStrings =  {
                '2': f'is no longer supported and should be replaced',
                '3': f'is running an unsupported version of {osMain}',
                '4': f'is running an outdated version of {osMain} and needs to be updated',
            }
            
            # Does not alert for possibly unsupported for now.
            ticketPayloadCreator(genericString + ' ' + osStrings[str(osDetails)], existingTicketID=False)
        if lastResponse > daysSince(5) and lastBoot < daysSince(19):
            print("Restart overdue") # DEBUG
            ticketPayloadCreator(f"{genericString} requires a restart. Last restarted {lastBootString}", existingTicketID=False)
        elif lastResponse < daysSince(30):
            print("Has not responded") # DEBUG
            ticketPayloadCreator(f"{genericString} was last online {lastResponseString} ", existingTicketID=False)
        else: #Skip remaining code 
            continue
    print(f'{datetime.now()}: Device complete')
