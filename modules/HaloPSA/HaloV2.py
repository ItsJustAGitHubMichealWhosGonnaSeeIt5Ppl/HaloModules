# Entirely re-written with classes

# Apparently this is very, very bad

# Modules to interact with Halo.
# Some modules use specifc IDs, will try to clean this up as I go.

import requests
import urllib.parse
import json
import os
from modules.miscModules import gentleError

# CONSTANTS
HALO_CLIENT_ID = os.getenv("HALO_CLIENT_ID") 
HALO_SECRET = os.getenv('HALO_SECRET') 
HALO_API_URL = os.getenv('HALO_API_URL') 
HALO_AUTH_URL = os.getenv('HALO_AUTH_URL')

assetURL = HALO_API_URL+ '/asset/'


# Confirm variables are present
nodata = [None,'']
if HALO_CLIENT_ID in nodata or HALO_SECRET in nodata or HALO_API_URL in nodata or HALO_AUTH_URL in nodata:
    gentleError('Missing env file, Fill out "example.env" and rename to ".env"')  




def responseParser(request,Verbose=False):
    """ Halo Response parser(?)

    Args:
        request (requests.models.Response): Halo API request
        Verbose (bool, optional): Return extra details about response. Defaults to False.

    Returns:
        any: API content and non critical error messages
    """
    code = request.status_code
    
    # Invalid URL
    if code in [404]:
        gentleError(f'404 -  The specified URL is invalid. URL: {request.url}')
    content = json.loads(request.content)
    
    # Success
    if code in [200,201]:
        if Verbose==True:
            return 'Success', content
        else:
            return content

    elif code in [401]:
        
        # Return clearer errors
        if content["error_description"] == 'The specified client credentials are invalid.':
            # Specify it is the client secret that is wrong, not the client ID.
            gentleError('The specified \'client_secret\' is invalid')
        else:
            gentleError(content["error_description"])
            
    # Add unique failures as found
    # If secret, client ID, or URL are wrong, error 401 is returned
    else:
        if Verbose==True:
            return 'Error',f'{code} - Other failure'
        else:
            return f'{code} - Other failure'


def createToken():
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
    
    request = requests.post(HALO_AUTH_URL, headers=authheader, data=urllib.parse.urlencode(payload)) # Request auth token
    response = responseParser(request,True)
    if response[0] == 'Success':
        return response[1]['access_token']
    else:
        return response

mainToken = createToken()


class asset():
    """ Asset actions 
    Initialize by running this once on its own, then run actions"""
    def __init__(self):
        token = createToken() # Maybe this can be moved out?
        self.token = token
        self.headerJSON = { # Header with token
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' +  token
            }
    
    def get(self,id):
        """Get a single halo asset's details.
        ID = Asset ID"""
        request = requests.get(assetURL + str(id) +'?includedetails=True', headers = self.headerJSON)
        return responseParser(request)

    
    def getAll(self):
        """ Replaces Returns all Halo assets"""
        request = requests.get(assetURL, headers = self.headerJSON)
        return responseParser(request)
    
    def search(self,query):
        """ Search Halo assets 
        DOES NOT DO ANYTHING RIGHT NOW """
        pass
    
    def update(self,payload):
        """ Update asset.  ID provided in Payload (for now.) 
        Payload should be formatted with json.dumps, will move that bit in here eventually."""
        request = requests.post(assetURL, headers = self.headerJSON, data=payload)
        return responseParser(request)

    
    
           
class ticket():
    def __init__(self):
        token = createToken()
        self.token = token
        self.headerJSON = { # Header with token
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' +  token
            }
    
    def create(self, payload):
        """ Create a ticket 
        Payload must be formatted for now, will create a formatting tool later"""
        request = requests.post(HALO_API_URL+ '/tickets/', headers = self.headerJSON, data=payload)
        return responseParser(request)

    def search(self,query):
        """ Search ticket using Query (Later query will be its own thing so its easier to use) """
        query = urllib.parse.urlencode(query)
        request = requests.get(HALO_API_URL+ '/tickets?' + query, headers = self.headerJSON)
        return responseParser(request)





def productUpdate(updateField,originalText,replacementText):
    """ Update a halo product by value. 
    Requires token, field to search on/update, text to search, text to replace with.
    """
    headers = { # Header with token
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + mainToken
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



def userSearch(query):
    """ Searches for a user """
    headers = { # Header with token
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + mainToken
        }
    request = requests.get(HALO_API_URL+ '/users?' + urllib.parse.urlencode(query), headers = headers)
    if request.status_code != 200:
        return 'Failed to get users'
    response = json.loads(request.content)
    return response
    



def invoiceActivator(ids=None):
    """ Set invoices to Active
    If no IDs sent, all invoices will be set to Active """
    headers = { # Header with token
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + mainToken
        }
    query = {
        'type': 54,
    }
    request = requests.get(HALO_API_URL+ '/Template', headers = headers,params = query)
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
            updateAttempt = requests.post(HALO_API_URL+ '/Template', headers = headers,data = data)
            if updateAttempt.status_code !=[200,201]:
                print('Failed')
            else:
                print(f'Updated {invoice["id"]}')
    return response


def manualTokenUpdate(key,id):
    """ Manually update tokens for halo integrations.

    Make sure you have the integration type set to bearer token :)"""
    headers = { # Header with token
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + mainToken
        }
    payload = json.dumps([{
        "new_client_secret": str(key),
        "id": id 
    }])
    attemptUpdate = requests.post(HALO_API_URL+ '/CustomIntegration', headers = headers, data=payload)
    return attemptUpdate