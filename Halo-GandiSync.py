from modules.HaloPSA.HaloV2 import asset
import modules.dmeModule as dme
import modules.gandiModules as gandi
from datetime import datetime,timezone # TIMEZONE IS USED
import json


expiredDomains  = [] # Expired Gandi Domains
ignoredDomains = [] # Add domains to be ignored by warning

hAssets = asset()
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
    domainDetails = []
    domainExpiration = datetime.fromisoformat(domain['dates']['registry_ends_at'])
    lastUpdated = datetime.fromisoformat(domain['dates']['updated_at'])
    # Search for asset
    queryLoad = {
            'pageinate':'false',
            'count': 1,
            'assettype_id': typeID,
            'search': str(domain['fqdn'])
        }
    assetSearch = hAssets.search(queryLoad)
    
    # Check if domain exists in DME
    if domainExpiration > today:
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
        

        
        if assetSearch['record_count'] == 0:
            payload = json.dumps([{ # Device update payload
            "_dontaddnewfields": True,
            "isassetdetails": True,
            'assettype_id': typeID,
            "fields": domainDetails,
            }])
        else:
            assetID = assetSearch['assets'][0]['id']
            payload = json.dumps([{ # Device update payload
            "_dontaddnewfields": True,
            "isassetdetails": True,
            'assettype_id': typeID,
            "fields": domainDetails,
            'id': assetID
            }])
        
        hAssets.update(payload)


    else:
        expiredDomains.append(domain['fqdn'])


