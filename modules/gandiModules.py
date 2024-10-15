import requests as rq
import urllib.parse
import json
from datetime import datetime, date, time,timezone
import os
import hmac
import hashlib



# Expires every 30 days
TOKEN = os.getenv('GANDI_TOKEN')
BASE_URL = 'https://api.gandi.net/v5/'
AUTH_INFO_URL = 'https://id.gandi.net/tokeninfo'

headers = { # Header with token
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' +  TOKEN
}

def checkToken():
    response = rq.get(AUTH_INFO_URL,headers=headers)
    return json.loads(response.content.decode('utf-8'))

def getAll():
    incomplete = True
    allDomains = []
    url = BASE_URL + 'domain/domains'
    while incomplete:
        
        load = requester(url)
        allDomains += load[0]
        if 'next' in load[2]:
            url = load[2]['next']['url']
        else:
            incomplete = False
    return allDomains

def getDetails(domain):
    url = BASE_URL+ 'domain/domains/' + str(domain)
    load = requester(url)
    return load[0]




    
def requester(url,header='Default'):
    if header == 'Default':
        header = { # Header with token
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' +  TOKEN,
    }

    try:
    
        response = rq.get(url, headers=header)
        # Format and return
        return json.loads(response.content.decode('utf-8')), response.headers, response.links
    except Exception as e:
        raise e
