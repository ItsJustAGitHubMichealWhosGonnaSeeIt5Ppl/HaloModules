# Modules to interact with Halo.
# Some modules use specifc IDs, will try to clean this up as I go.

import requests
import urllib.parse
import json
import os
from .databaseModules import queryDB



# CONSTANTS
HALO_CLIENT_ID = os.getenv("HALO_CLIENT_ID") 
HALO_SECRET = os.getenv('HALO_SECRET') 
HALO_API_URL = os.getenv('HALO_API_URL') 
HALO_AUTH_URL = os.getenv('HALO_AUTH_URL')


"""
Note: Halo claims we can send the client ID and secret as many times as we like to get access, but the request below also sends a refresh token, so mayber we want to use that? 
Halo says dont use the refresh token. Im not bitch made so im gonna try anyway.
"""

def getHaloToken(): 
    """ Get authorisation token from Halo. 
    
    Valid for 48 hours.
    
    Requires: HALO_CLIENT_ID, HALO_SECRET, HALO_AUTH_URL
    Ceej says im allowed to send a new request every time
    """

    # Return auth token from Halo. 
    authheader = { # Required by Halo, don't ask me why
    'Content-Type': 'application/x-www-form-urlencoded'
    }

    payload = { # Create payload for Halo auth
    'grant_type': 'client_credentials',
    'client_id': HALO_CLIENT_ID,
    'client_secret': HALO_SECRET,
    'scope': 'all' 
    }

    tokenRequest = requests.post(HALO_AUTH_URL, headers=authheader, data=urllib.parse.urlencode(payload)) # Request auth token 
    if tokenRequest.status_code != 200: # TODO #1 Check for failure (aka make sure this works)
        return "authorisation failure"
    return json.loads(tokenRequest.content)['access_token'] 


def getHaloAssets(token,id=None): 
    """ Returns Halo Asset details.  If no ID is provided, returns list of all assets.
     
    NOTE: not all data is returned when all assets are queried.  Recommend querying all devices first, and then querying relevant devices with ID as needed."""
    #TODO #2 allow servers to be queried

    headers = { # Header with token
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': 'Bearer ' + token
    }   
    if id != None:
        assetRequest = requests.get(HALO_API_URL + "/asset/" + str(id) +'?includedetails=True', headers = headers)
    else:
        assetRequest = requests.get(HALO_API_URL + "/asset/", headers = headers)
    if assetRequest.status_code != 200:
        return 'Failed to retrieve asset(\'s)'
    return json.loads(assetRequest.content)


def updateHaloAsset(payload, token): 
    """ Update asset via ID.  ID must be provided in Payload for now. """
    # Update an asset by ID
    headers = { # Header with token
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
    }
    attemptUpdate = requests.post(HALO_API_URL+ '/asset/', headers = headers, data=payload)
    if attemptUpdate.status_code in [200,201]:
        return attemptUpdate.content
    else: # Leaves room for other codes to be indifivually tagged later
        return 'Failed to update Asset'


def createHaloTicket(payload, token):
    # Create ticket
    headers = { # Header with token
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
    }
    attemptUpdate = requests.post(HALO_API_URL+ '/tickets/', headers = headers, data=payload)
    return attemptUpdate



def manualTokenUpdate(key,token,id):
    """ Manually update tokens for halo integrations.

    Make sure you have the integration type set to bearer token :)"""
    headers = { # Header with token
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
        }
    payload = json.dumps([{
        "new_client_secret": str(key),
        "id": id 
    }])
    attemptUpdate = requests.post(HALO_API_URL+ '/CustomIntegration', headers = headers, data=payload)
    return attemptUpdate


# TODO #1 
# TODO #2 
def productUpdate(token,updateField,originalText,replacementText):
    """ Update a halo product by value. 
    Requires token, field to search on/update, text to search, text to replace with.
    """
    headers = { # Header with token
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
        }
    def updateItemByID(ID,originalStr):
        payload = json.dumps([{
        updateField: originalStr.replace(originalText,replacementText),
        "id": ID
        }])
        attemptUpdate = requests.post(HALO_API_URL+ '/item', headers = headers, data=payload)
        return attemptUpdate.status_code

    request = requests.get(HALO_API_URL+ '/item', headers = headers)
    itemsList = json.loads(request.content)['items']
    for item in itemsList:
        if item == 'more': # Shows only 100 by default, this allows it to cycle through the remaining ones 
            item = item['more']
        if updateField in item:
            if originalText in item[updateField]:
                print(f'[{item["id"]}] {item["name"]}\n - {item[updateField]}') # Original string
                attemptUpdate = updateItemByID(item["id"],item[updateField])
                print(attemptUpdate) # Status of attempted assetUpdate
                

def productDB():
    #TODO create DB for products to allow for easier searching, updating, etc.
    sqlQuery = "INSERT OR UPDATE OR IGNORE INTO (tbd) values=()"
    sqlData = ""
    pass

### Testing the above tool
# originalText = 'for (contract start date) - (contract end date) - billed monthly'
# newText = 'for contract period $CONTRACTSTARTDATE - $CONTRACTENDDATE (billed monthly)'
# productUpdate(getHaloToken(),'description',originalText,newText)



def userSearch(token,query):
    """ Searches for a user """
    headers = { # Header with token
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
        }
    request = requests.get(HALO_API_URL+ '/users?' + urllib.parse.urlencode(query), headers = headers)
    if request.status_code != 200:
        return 'Failed to get users'
    response = json.loads(request.content)
    return response
    
