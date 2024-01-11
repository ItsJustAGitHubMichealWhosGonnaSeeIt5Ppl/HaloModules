import requests as rq
import json
import os
from datetime import date, datetime, timezone,timedelta

BASE_URL = 'https://admin.googleapis.com/admin/reports/v1'
REFRESH_URL = 'https://oauth2.googleapis.com/token'
CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
SECRET = os.getenv('GOOGLE_SECRET')
REFRESH_TOKEN = os.getenv('GOOGLE_REFRESH_TOKEN')

driveReportsAPI = '/activity/users/all/applications/drive'


def refreshGoogleToken():
    data = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'client_id': CLIENT_ID,
        'client_secret':SECRET,
        'refresh_token': REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    }
    tokenRequest = rq.post(REFRESH_URL, data=data)
    if tokenRequest.status_code != 200:
        return 'Failed to refresh'
    else:
        return json.loads(tokenRequest.content)['access_token']



def driveDataCheck(token, **extras):
    """ Return audit logs from Google Drive """
    timeNow = datetime.now(timezone.utc)
    timeNow = timeNow - timedelta(1) 
    
    headers = { # Header with token
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
    }
    params = {
       'startTime': timeNow.isoformat(),
       'eventName': extras['eventName']
    }
    data = rq.get(BASE_URL+driveReportsAPI, headers = headers,params=params)
    dataTemp = json.loads(data.content)
    return json.loads(data.content)
    


def DriveDataFilter(data,**extra):
    """ Filter data """
    accountList = extra['accountList']
    dictIDs = {}
    for user in accountList:
        dictIDs.update({user+'@'+extra['domain']:{
            'upload': False,
            'edit': False,
            'download': False
        }})
    for event in data.values():
        for item in event['items']:
            if item == 'more': # Shows only 100 by default, this allows it to cycle through the remaining ones 
                event = item['more']
                continue
            if item['actor']['email'] in dictIDs.keys():
                dictIDs[item['actor']['email']].update({item['events'][0]['name']: True})
    return dictIDs


## Sources
# RFC 3339 in python
# https://stackoverflow.com/questions/8556398/generate-rfc-3339-timestamp-in-python
