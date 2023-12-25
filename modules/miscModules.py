# This contains a bunch of function that are used in multiple scripts, but don't really fit anywhere else.  
# Ideally this will be deleted when I find every function a home.

# Imports
from datetime import datetime, date, timedelta


""" Created by ItsAGithubMichealWhosGonnaSeeIt5Ppl
 = = A few notes :) = = 
- The N-Able API is very slow, for around 300 devices it takes upwards of 5 minutes!!
- The N-Able API returns XML data, I hate XML and refused to learn more than the bare minimum to do this, so there is likely a better way to convert the tables.
"""


def toUnixInt(input,mode='date'): 
# Converts ISO date or date and time into a UNIX timecode. Work with string formatted ISO dates.
# TODO #25 Use this converter for all dates that need to be ISO, add ability to convert back as well.
    return int(str(datetime.fromisoformat(str(input)).timestamp())[:10])


def daysSince(day,value='day'):
    """ Input days to subtract.  Optionally, input 'time' to receive a datetime formatted response (default is date formatted)"""
    # Accepts INT input, returns todays date minus input number(days). Output can be used to compare to other date values.
    # value can be day or time. Time will return a full datetime string for comparison.
    return (date.today() - timedelta(days=day)) if value.lower() == 'day' else (datetime.now() - timedelta(days=day)) if value.lower() == 'time' else 'invalid request'


def valueExtract(customFields,IDs,fieldName):
    # Extract values from custom fields
    fieldsDict = {}
    for field in customFields:
        if field[fieldName[0]] in IDs and fieldName[1] in field:
            fieldsDict[field[fieldName[0]]] = field[fieldName[1]]
    return fieldsDict