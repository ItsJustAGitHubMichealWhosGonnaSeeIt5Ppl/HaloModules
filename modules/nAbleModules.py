# NAble modules
# Will eventually add some better documentation

# Imports
import requests
import xmltodict
import os



# CONSTANTS
## N-Able
NABLE_KEY = os.getenv("NABLE_KEY") 
NABLE_API_URL = f"https://www.systemmonitor.co.uk/api/?apikey={NABLE_KEY}&service=" # Only works with UK instances.


def getN_AbleInfo(deviceID):
    # Returns N-Able device information. Input deviceID.
    # Halo stores the deviceID as 'third party ID'
    # TODO #29 Allow this to query servers as well 
    nAbleDetails = requests.get(NABLE_API_URL+ "list_device_monitoring_details&deviceid=" + str(deviceID))
    if xmltodict.parse(nAbleDetails.content)["result"]["@status"] != 'OK':  # Failure detection
        print("N-Able failed to process result")
        return False 
    else: # Reformat into dictionary with device information
        return xmltodict.parse(nAbleDetails.content)["result"]["workstation"] 