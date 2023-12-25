# Modules to interact with Halo.
# Some modules use specifc IDs, will try to clean this up as I go.

import requests
import urllib.parse
import json
import os



# CONSTANTS
## Halo
HALO_CLIENT_ID = os.getenv("HALO_CLIENT_ID") 
HALO_SECRET = os.getenv('HALO_SECRET') 
HALO_API_URL = os.getenv('HALO_API_URL') 
HALO_AUTH_URL = os.getenv('HALO_AUTH_URL')


"""
Note: Halo claims we can send the client ID and secret as many times as we like to get access, but the request below also sends a refresh token, so mayber we want to use that? 
Halo says dont use the refresh token. Problem is im not bitch made so im gonna try.
"""

def getHaloToken(): 
    # Return auth token from Halo. Ceej says im allowed to do it every time
    authheaders = { # Required by Halo, don't ask me why
    'Content-Type': 'application/x-www-form-urlencoded'
    }

    payload = { # Create payload to get credentials
    'grant_type': 'client_credentials',
    'client_id': HALO_CLIENT_ID,
    'client_secret': HALO_SECRET,
    'scope': 'all' 
    }

    tokenRequest = requests.post(HALO_AUTH_URL, headers=authheaders, data=urllib.parse.urlencode(payload)) # Request auth token 
    if tokenRequest.status_code != 200: # TODO #1 Check for failure (aka make sure this works)
        return "authorisation failure"
    requestContent = json.loads(tokenRequest.content)
    return requestContent['access_token'] 


def getHaloAssets(token,id=False): 
    """ Returns halo Asset details
    If no ID is provided, returns list of all assets. """
    #TODO #2 allow servers to be queried
    headers = { # Header with token
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': 'Bearer ' + token
    }   
    if id !=False:
        id = str(id)
        assetRequest = requests.get(HALO_API_URL + "/asset/" + id, headers = headers)
    else:
        assetRequest = requests.get(HALO_API_URL + "/asset/", headers = headers)
    if assetRequest.status_code != 200:
        return 'Failed to retrieve asset(S)'
    assetList = json.loads(assetRequest.content)
    return assetList 


def updateHaloAsset(payload, token): 
    # Update an asset by ID
    headers = { # Header with token
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
    }
    attemptUpdate = requests.post(HALO_API_URL+ '/asset/', headers = headers, data=payload)
    return attemptUpdate


def createHaloTicket(payload, token):
    # Create ticket
    headers = { # Header with token
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
    }
    attemptUpdate = requests.post(HALO_API_URL+ '/tickets/', headers = headers, data=payload)
    return attemptUpdate



def manualTokenUpdate(key,token):
    """ Manually update tokens for halo integrations. 
    Make sure you have the integration type set to bearer token :)"""
    headers = { # Header with token
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
        }
    payload = json.dumps([{
        "new_client_secret": str(key),
        "id": "6" # Set your custom integration ID here
    }])
    attemptUpdate = requests.post(HALO_API_URL+ '/CustomIntegration', headers = headers, data=payload)
    return attemptUpdate



def productUpdate():
    """ Update a halo product """
    pass