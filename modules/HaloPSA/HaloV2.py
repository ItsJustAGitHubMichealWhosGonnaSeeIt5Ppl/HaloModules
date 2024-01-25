# Entirely re-written with classes



# Modules to interact with Halo.
# Some modules use specifc IDs, will try to clean this up as I go.

import requests as rqst
import urllib.parse
import json
import os


# CONSTANTS
HALO_CLIENT_ID = os.getenv("HALO_CLIENT_ID") 
HALO_SECRET = os.getenv('HALO_SECRET') 
HALO_API_URL = os.getenv('HALO_API_URL') 
HALO_AUTH_URL = os.getenv('HALO_AUTH_URL')


class HaloPSA():
    def __init__ (self,token):
        header = { # Header with token
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token
            }
        self.asset = self.assetC(self.header)
    
    class TEMPLATECLASS():
        """ Asset actions """
        def __init__(self):
            self.ll = HALO_API_URL + ''
            self.header = HaloPSA.header
            
        
    def responseCode(data):
        """ Work in Progress, halo code detection """
        code = data.status_code
        if code  in [200,201]:
            return data.content
        else:
            return f'{code} - Other failure'

    def getToken():
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
        request = rqst.post(HALO_AUTH_URL, headers=authheader, data=urllib.parse.urlencode(payload)) # Request auth token 
        return json.loads(HaloPSA.responseCode(request))['access_token'] 
    
    class assetC():
        """ Asset actions """
        def __init__ (self):
            self.asset = HALO_API_URL + '/asset/'
            
        def get(self,id):
            """Get a single halo assets details."""
            request = rqst.get(self.asset + str(id) +'?includedetails=True', headers = self.header)
            return json.loads(HaloPSA.responseCode(request))
        
        def getAll(self):
            """ Replaces Returns all Halo assets"""
            request = rqst.get(self.asset, headers = self.header)
            return json.loads(HaloPSA.responseCode(request))
        
        def search(self,query):
            """ Search Halo assets 
            DOES NOT DO ANYTHING RIGHT NOW """
            pass
        
        def update(self,payload):
            """ Update asset.  ID provided in Payload (for now.) 
            Payload should be formatted with json.dumps, will move that bit in here eventually."""
            request = rqst.post(self.asset, headers = self.header, data=payload)
            return HaloPSA.responseCode(request)
    class ticket():
        def createHaloTicket(payload):
            # Create ticket
            request = rqst.post(HALO_API_URL+ '/tickets/', headers = self.header, data=payload)
            return HaloPSA.responseCode(request)                


def createHaloTicket(payload, token):
    # Create ticket
    headers = { # Header with token
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
    }
    attemptUpdate = rqst.post(HALO_API_URL+ '/tickets/', headers = headers, data=payload)
    return attemptUpdate


def searchHaloTicket(query, token):
    """ Searches for a ticket """
    headers = { # Header with token
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
        }
    request = rqst.get(HALO_API_URL+ '/tickets?' + urllib.parse.urlencode(query), headers = headers)
    if request.status_code != 200:
        return 'Failed to get tickets'
    response = json.loads(request.content)
    return response

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
    attemptUpdate = rqst.post(HALO_API_URL+ '/CustomIntegration', headers = headers, data=payload)
    return attemptUpdate



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
        attemptUpdate = rqst.post(HALO_API_URL+ '/item', headers = headers, data=payload)
        return attemptUpdate.status_code

    request = rqst.get(HALO_API_URL+ '/item', headers = headers)
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
    request = rqst.get(HALO_API_URL+ '/users?' + urllib.parse.urlencode(query), headers = headers)
    if request.status_code != 200:
        return 'Failed to get users'
    response = json.loads(request.content)
    return response
    



def invoiceActivator(token,ids=None):
    """ Activate invoices by ID(s). If no IDs sent, activate all invoices """
    headers = { # Header with token
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
        }
    query = {
        'type': 54,
    }
    request = rqst.get(HALO_API_URL+ '/Template', headers = headers,params = query)
    if request.status_code != 200:
        return 'Failed to get Templates'
    response = json.loads(request.content)
    for invoice in response:
        print(invoice['id'])
        if invoice == 'more':
            invoice = invoice['more']
        if invoice['disabled'] == True:
            data = json.dumps([{
                'disabled': False,
                'end_date': '1901-01-01T00:00:00.000Z',
                'id':invoice['id']
                
            }])
            updateAttempt = rqst.post(HALO_API_URL+ '/Template', headers = headers,data = data)
            if updateAttempt.status_code !=[200,201]:
                print('Failed')
            else:
                print(f'Updated {invoice["id"]}')
    return response


