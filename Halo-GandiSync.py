from modules.HaloPSA.HaloV3 import assets, clients
import modules.dmeModule as dme
import modules.gandiModules as gandi
from datetime import datetime,timezone # TIMEZONE IS USED
import json


expiredDomains  = [] # Expired Gandi Domains
ignoredDomains = [] # Add domains to be ignored by warning

hAssets = assets()
hClients = clients()
dmeData = dme.getAll()['data']
gandiData = gandi.getAll()

# Field IDs
typeID = 137 # Asset types ID
domainID = 167 # Domain Name ID
expID = 168 # Domain expiration IDs
tldID = 172
managedID = 170 # Domain Managed: Yes/No [1/2]
nameserversID = 171 # 
dmeLinkID = 173
gandiLinkID = 174


dmeDomains = {}
for domain in dmeData:
    dmeDomains.update({domain['name']:{'id': domain['id']}})



today = datetime.now(timezone.utc)

# 2024-10-17T12:00:00.000Z
# Exclude expired domains (puts them in a list for now)
for domain in gandiData:
    
    domainDetails = [] # List of data to be sent to Halo
    domainExpiration = datetime.fromisoformat(domain['dates']['registry_ends_at'])
    lastUpdated = datetime.fromisoformat(domain['dates']['updated_at'])
    
    
    assetSearch = hAssets.search( # Check if domain is already in Halo (asset search)
            pageinate=False,
            assettype_id=typeID,
            search=str(domain['fqdn']))
    
    clientSearch = hClients.search(
        search=domain['tags'][0]
    )
    
    if domainExpiration > today: # Check if domain exists in DME
        if domain['fqdn'] in dmeDomains.keys():
            managed = '1'
            dmeID = dmeDomains[domain['fqdn']]['id']
            domainDetails += [
                {'id': dmeLinkID, 'value': f'https://cp.dnsmadeeasy.com/dns/managed/{dmeID}'}]
        else:
            managed = '2'

        domainDetails += [
            {'id': domainID, 'value': domain['fqdn']}, # Domain name
            {'id': tldID, 'value': domain['tld']}, # 
            {'id': expID, 'value': domain['dates']['registry_ends_at']},
            {'id': managedID, 'value': managed},
            {'id': gandiLinkID, 'value': 'https://admin.gandi.net/domain/' + domain['fqdn']}
            ]
        

        
        hAssets.update(
        _dontaddnewfields= True,
        isassetdetails= True,
        assettype_id= typeID,
        fields=domainDetails,
        id= assetSearch['assets'][0]['id'] if assetSearch['record_count'] != 0 else None,
        client_id=clientSearch['clients'][0]['id'],
        inventory_number=domain['fqdn']
        )
        


    else:
        expiredDomains.append(domain['fqdn'])


