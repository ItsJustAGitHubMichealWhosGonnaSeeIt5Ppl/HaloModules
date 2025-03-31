# // Imports
from datetime import datetime, date,timedelta
import json
from HaloPSA import Assets, Actions, Tickets
# Local modules
from modules.miscModules import daysSince, valueExtract, customFieldCheck
from modules.msoftModules import winCheck
from modules.macModules import macCheck
import os

HALO_TENANT = os.getenv('HALO_TENANT')
HALO_ID = os.getenv('HALO_CLIENT_ID')
HALO_SECRET = os.getenv('HALO_SECRET')

version = '0.0.3'
# Now checks for EDR and MAV
# Now checks for Bitlocker script and exports this data into Halo

# Goals
## TODO If device does not have checks, skip it
## TODO #11 Only scan devices in "hiatus" or with "no checks" on occasion 
## TODO Before making public, status IDs must be switched
##TODO #3 When creating macOS update tickets, note the device type in the ticket body.
#TODO if multiple devices have similar names, system doesn't seem to notice
#TODO count restart reminders (emails sent, not reminder generated)

today = datetime.today()
createTickets = True
restartCutoff = 12 # days. Over this amount, restart alert tickets WILL be generated
offlineCutoff = 30 # days. Over this amount, offline alert tickets WILL be generated

customFields = {
    'doNotContact': 161,
    'lastChecked': 159,
    'lastResponse': 158,
    'lastBoot': 157,
}

hAsset = Assets(HALO_TENANT,HALO_ID,HALO_SECRET)
hTickets = Tickets(HALO_TENANT,HALO_ID,HALO_SECRET)
hAction = Actions(HALO_TENANT,HALO_ID,HALO_SECRET)
#128 = synced assets ID
assets = hAsset.search(assettype_id=128)

for asset in assets['assets']:
    
    assetDetails = hAsset.get(id=asset['id'])
    
    needsRestart = False
    offlineTooLong = False
    doNotContact = False
    ignoreRestart = False 
    
    # Format relevant field information
    for field in assetDetails['fields']:
        if 'value' not in field.keys():
            continue # skip empty fields
        elif field['id'] == customFields['lastResponse']:
            if (today - datetime.fromisoformat(field['value'])) > timedelta(days=offlineCutoff):
                offlineTooLong = True
                ignoreRestart = True
                lastOnlineDate = field['value']
            elif (today - datetime.fromisoformat(field['value'])) > timedelta(days=5): # For devices thave have been offline for more than 5 days, but less than 30.
                ignoreRestart = True
        elif field['id'] == customFields['lastBoot']:
            if (today - datetime.fromisoformat(field['value'])) > timedelta(days=restartCutoff):
                needsRestart = True
                lastRestartDate = field['value']
        elif field['id'] == customFields['doNotContact']:
            doNotContact = True if field['value'] == 1 else False
    
    if doNotContact == True:
        continue # Skip
    
    
    tickets = hTickets.search(
        tickettype_id=21, # Alert tickets
        open_only=True, # Only get open tickets
        asset_id = asset['id'], # Client ID 
        )
    
    lastOnlineTicketID = None
    restartTicketID = None
    if tickets['record_count'] > 0:
        for ticket in tickets['tickets']:
            if ticket['summary'].startswith('Your computer requires a restart'):
                restartTicketID = ticket['id']
            elif ticket['summary'].startswith('Your computer was last online'):
                lastOnlineTicketID = ticket['id']
    
    if offlineTooLong == False and lastOnlineTicketID != None: # Close ticket
         hTickets.update(
            id = lastOnlineTicketID,
            status_id=20)
    elif offlineTooLong == True and lastOnlineTicketID != None:
        
        hAction.update(ticket_id= lastOnlineTicketID,
            note_html= 'Computer still offline',
            outcome_id = 7)
        hTickets.update(
            id = lastOnlineTicketID,
            status_id=23,
            summary = f'Your computer was last online {str(today - datetime.fromisoformat(lastOnlineDate)).split(',')[0]} ago')
        
    elif offlineTooLong == True and lastOnlineTicketID == None:
        hTickets.update(
                tickettype_id= 21,
                client_id = asset['client_id'], # Client ID 
                site_id = asset['site_id'], # Site ID
                summary = f'Your computer was last online {str(today - datetime.fromisoformat(lastOnlineDate)).split(',')[0]} ago',
                details_html = f"<p> Computer is offline </p>", # HTML formatted info
                assets = [{
                    "id": asset['id'],  # Asset
                    }],
                user_id = assetDetails['users'][0]['id'] if len(assetDetails['users']) > 0 else None)
    
    if needsRestart == False and restartTicketID !=None: # Close ticket
         hTickets.update(
            id = restartTicketID,
            status_id=20)
         
    elif ignoreRestart == True:
        continue # Skip computers that are offline right now
         
    elif needsRestart == True and restartTicketID != None:
        hAction.update(ticket_id = restartTicketID,
            note_html= 'Computer still needs restart',
            outcome_id = 7)
        hTickets.update(
            id = restartTicketID,
            status_id=23,
            summary = f'Your computer requires a restart. Last restarted {str(today - datetime.fromisoformat(lastRestartDate)).split(',')[0]} ago')
        
    elif needsRestart == True and restartTicketID == None:
        hTickets.update(
                tickettype_id= 21,
                client_id = asset['client_id'], # Client ID 
                site_id = asset['site_id'], # Site ID
                summary = f'Your computer requires a restart. Last restarted {str(today - datetime.fromisoformat(lastRestartDate)).split(',')[0]} ago',
                details_html = f"<p> Computer needs restart </p>", # HTML formatted info
                assets = [{
                    "id": asset['id'],  # Asset
                    }],
                user_id = assetDetails['users'][0]['id'] if len(assetDetails['users']) > 0 else None)