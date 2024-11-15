# NAble modules
# Will eventually add some better documentation

# Imports
import requests
import xmltodict
import os
from urllib.parse import urlencode


# CONSTANTS
## N-Able
NABLE_KEY = os.getenv("NABLE_KEY") 


class nAble:
    def _responseParser(self,response):
        """Parses response from NAble

        Args:
            response (_type_): _description_

        Raises:
            ValueError: _description_
            Exception: _description_
            Exception: _description_
            Exception: _description_

        Returns:
            dict: Dictionary
        """
        if response.status_code == 403: # invalid URL
            print('Add an error here, URL is ad')
        elif response.status_code == 200: # Valid URL 
            content = xmltodict.parse(response.content)['result']
            try:
                status = content['@status']
            except KeyError: # Sometimes no status is sent, in which case assume its OK
                status = 'OK'
                
            
            if status == 'OK': # Valid key/request
                return content
            elif status == 'FAIL':
                if content['error']['errorcode'] == 3: # Login failed, invalid key
                    raise ValueError(f'Login failed, your API could may be wrong, or you could be using the wrong region')
                elif content['error']['errorcode'] == 4:
                    raise ValueError(f'{content['error']['message']}')
                else:
                    raise Exception(content['error']['message'])
            else:
                raise Exception(f'Unknown error: {status}')
        else:
            raise Exception(f'Unknown response code {response.status_code}')
    
    def __init__(self,region,key):
        
        
        dashboardURLS = {
            'americas': 'dashboard.am.remote.management', # Unverified
            'asia': 'dashboardasia.system-monitor.com', # Unverified
            'australia': 'dashboard.system-monitor.com', # Unverified
            'europe': 'dashboardeurope1.systemmonitor.eu.com', # Unverified
            ('france','fr'): 'dashboardfrance.systemmonitor.eu.com', # Unverified
            ('france1','fr1'): 'dashboardfrance1.systemmonitor.eu.com', # Unverified
            'germany': 'dashboardgermany1.systemmonitor.eu.com', # Unverified
            'ireland': 'dashboardireland.systemmonitor.eu.com', # Unverified
            'poland': 'dashboardpoland1.systemmonitor.eu.com', # Unverified
            ('united kingdom','uk','gb'): 'www.systemmonitor.co.uk', # Verified
            ('united states','us','usa'): 'www.systemmonitor.us' # Verified
        }
        regionURL = None
        for regionName, url in dashboardURLS.items(): # Search URLs for matching region
            
            if isinstance(regionName,tuple): # Allows tupled items to be properly checked, otherwise us can be seen in australia
                regionName =list(regionName)
            else:
                regionName = [regionName]
            
            if region in regionName:
                regionURL = url
                break
        if regionURL == None:
            raise ValueError(f'{region} is not a valid region')
        
        self.queryUrlBase = f"https://{regionURL}/api/?apikey={key}&service="
        
        try:
            testRequest = requests.get(self.queryUrlBase +'list_clients')
        except ConnectionError:
            raise Exception('The request URL is not valid, this is an issue with the module')
            
        self._responseParser(testRequest) # Test that key is valid.
        
    def _formatter(self,params):
        paramsToAdd = params # Shouldn't be needed, but had weird issues when it worked directly from the params before.
        
        popList = ['self','endpoint','includeDetails'] # Things that should not be added to the URL
        for popMe in popList:
            try: # Skips nonexistent keys
                paramsToAdd.pop(popMe)
            except KeyError: 
                continue
        formattedData = {}
        
        for item, value in paramsToAdd.items(): # Check params, add anything that isn't blank to the query
            if value !=None:
                formattedData.update({item : value})
        return urlencode(formattedData)
        
        
    def clients(self,
        devicetype:str=None,
        describe:bool=None):
        
        endpoint = 'list_clients'
        formattedInfo = self._formatter(locals().copy())
        url = self.queryUrlBase + endpoint + '&' + formattedInfo
        return self._responseParser(requests.get(url))['items']['client']

    def sites(self,
        clientid:int,
        describe:bool=None):
        
        endpoint = 'list_sites'
        formattedInfo = self._formatter(locals().copy())
        url = self.queryUrlBase + endpoint + '&' + formattedInfo
        return self._responseParser(requests.get(url))['items']

    
    def servers(self,
        siteid:int,
        describe:bool=None):
        
        endpoint = 'list_servers'
        formattedInfo = self._formatter(locals().copy())
        url = self.queryUrlBase + endpoint + '&' + formattedInfo
        return self._responseParser(requests.get(url))['items']
    def workstations(self,
        siteid:int,
        describe:bool=None):
        
        endpoint = 'list_workstations'
        formattedInfo = self._formatter(locals().copy())
        url = self.queryUrlBase + endpoint + '&' + formattedInfo
        return self._responseParser(requests.get(url))['items']['workstation']

    def listAgentlessAssets(self):
        pass

    def clientDevices(self,
        clientid:int,
        devicetype:str,
        describe:bool=None,
        includeDetails:bool=False):
        
        
        endpoint = 'list_devices_at_client'
        formattedInfo = self._formatter(locals().copy())
        url = self.queryUrlBase + endpoint + '&' + formattedInfo
        
        clientDevices = self._responseParser(requests.get(url))['items']['client']
        if includeDetails == True: # Return devices with details
            if isinstance(clientDevices['site'], dict): 
                clientDevices['site'] = [clientDevices['site']]
            for site in clientDevices['site']:
                if isinstance(site,dict):
                    site = [site]
                for siteDevices in site:
                    if isinstance(siteDevices['workstation'],dict):
                        siteDevices['workstation'] = [siteDevices['workstation']]
                        deviceList = []
                    for device in siteDevices['workstation']:
                        
                        #Items which are not returneed in device details, but are in the overview (Why is there a difference?)
                        devStatus = device['status']
                        checkCount = device['checkcount']
                        webProtect = device['webprotection']
                        riskInt = device['riskintelligence']
                        device = naybl.deviceDetails(deviceid=device['id'])
                        # Re-add mising items
                        device['status'] = devStatus
                        device['checkcount'] = checkCount
                        device['webprotection'] = webProtect
                        device['riskintelligence'] = riskInt
                        deviceList+= [device]
                    siteDevices['workstation'] = deviceList
                        
        return clientDevices
    def deviceDetails(self,
        deviceid:int,
        describe:bool=None):
        
        endpoint = 'list_device_monitoring_details'
        formattedInfo = self._formatter(locals().copy())
        url = self.queryUrlBase + endpoint + '&' + formattedInfo
        return self._responseParser(requests.get(url))['workstation']
    
    def addClient(self):
        pass
    
    def addSite(self):
        pass
    
    def siteInstallationPackage(self):
        pass
    
    
    
if __name__ == '__main__':
    naybl = nAble('uk',NABLE_KEY)
    if False: # Testing checks

    
    ### Check all devices for ?
    
    clients = naybl.clients()
    
    
    
    for client in clients:
        if int(client['device_count']) < 1: # Skip clients with no devices
            continue
        devices = naybl.clientDevices(clientid=client['clientid'],devicetype='workstation',includeDetails=True)
