# This contains a bunch of function that are used in multiple scripts, but don't really fit anywhere else.  
# Ideally this will be deleted when I find every function a home.

# Imports
from datetime import datetime, date, timedelta
import requests 


""" Created by ItsAGithubMichealWhosGonnaSeeIt5Ppl
 = = A few notes :) = = 
- The N-Able API is very slow, for around 300 devices it takes upwards of 5 minutes!!
- The N-Able API returns XML data, I hate XML and refused to learn more than the bare minimum to do this, so there is likely a better way to convert the tables.
"""


def toUnixInt(input,mode='date'): 
# Converts ISO date or date and time into a UNIX timecode. Work with string formatted ISO dates.
# TODO #25 Use this converter for all dates that need to be ISO, add ability to convert back as well.
    try:
        date = int(str(datetime.fromisoformat(str(input)).timestamp())[:10])
        return date
    except:
        print('Failed to convert ' + str(input))
        return None
     


def daysSince(day,value='day'):
    """ Input days to subtract.  Optionally, input 'time' to receive a datetime formatted response (default is date formatted)"""
    # Accepts INT input, returns todays date minus input number(days). Output can be used to compare to other date values.
    # value can be day or time. Time will return a full datetime string for comparison.
    return (date.today() - timedelta(days=day)) if value.lower() == 'day' else (datetime.now() - timedelta(days=day)) if value.lower() == 'time' else 'invalid request'


def valueExtract(customFields,IDs,fieldName):
    # Extract values from custom fields
    fieldsDict = {}
    
    # Fix for single check devices
    if isinstance(customFields,dict):
            if customFields[fieldName[0]] in IDs and fieldName[1] in customFields:
                fieldsDict[customFields[fieldName[0]]] = customFields[fieldName[1]]
    else:
        for field in customFields:
            if field[fieldName[0]] in IDs and fieldName[1] in field:
                fieldsDict[field[fieldName[0]]] = field[fieldName[1]]
    return fieldsDict

def customFieldCheck(id,value):
    """ 
    Adds custom field to be used when updating asset ticket, etc
    
    :param id: Custom field ID
    :param value: Custom field value
    :return: Returns a list item to be added to your main list of fields
    """
    listItem = [
        {"id": id, 
        "value": value}]
    return listItem

# Exit the script early with some text
def gentleError(Text='Undefined Error'):
    print('[ERROR]',Text)
    exit()
    
def requestSend(rType,data):
    while attempts < 5 and processed == False:
            try:
                if rType == 'post':
                    request = requests.post(data)
                elif rType =='get':
                    request = requests.get(data)
                processed = True
            except(ConnectionError):
                attempts +=1
    if processed != True:
        gentleError('Connection error')
    else:
        return request
    
def userInput(text:str,validInputs:list,timeout:int=None):
    """collect and validate user input

    Args:
        text (str): Text to be displayed when requesting input 
        validInputs (list): Valid inputs list (must be lowercase)
        timeout (int): maximum tries before giving up

    Returns:
        (any): validated input or False if no valid input could be collected
    """
    count = 0
    while True:
        if timeout !=None and timeout < count:
            return False
        else:
            userInput = input(f'{text}: ')
        
        if str(userInput).lower() in validInputs:
            return userInput
        else:
            count+=1
            print('Invalid choice')
        