from modules.HaloPSA.HaloV3 import assets, sites, clients, recurringInvoices
import modules.dmeModule as dme
import modules.gandiModules as gandi
from datetime import datetime,timezone # TIMEZONE IS USED
import json


expiredDomains  = [] # Expired Gandi Domains
ignoredDomains = [] # Add domains to be ignored by warning

hAssets = assets()
hSites = sites()
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
lastCheckedID = 159


dmeDomains = {}
for domain in dmeData:
    dmeDomains.update({domain['name']:{'id': domain['id']}})



today = datetime.now(timezone.utc)

# 2024-10-17T12:00:00.000Z
# Exclude expired domains (puts them in a list for now)

domainAssets = hAssets.search(
    pageinate=False,
    assettype_id=typeID,
)
count = 0
for domain in gandiData:
    
    domainDetails = [] # List of data to be sent to Halo
    domainExpiration = datetime.fromisoformat(domain['dates']['registry_ends_at'])
    gandiLastUpdated = datetime.fromisoformat(domain['dates']['updated_at'])
    
    noMatch = True
    for haloDetails in domainAssets['assets']:
        if haloDetails['inventory_number'] == domain['fqdn']:
            noMatch = False
            assetDetails = haloDetails
            break
            
            
    forceUpdate = True
    if noMatch == False and assetDetails['key_field3'] != '': # Check that asset exists and that the last updated field is not empty
        haloLastUpdated = datetime.strptime(str(assetDetails['key_field3']+ ' +0100'), '%d/%m/%Y %H:%M:%S %z') # Jank solution to get a timezone added, needs work. 
        if gandiLastUpdated < haloLastUpdated and forceUpdate == False:
            print(f'no changes to {domain['fqdn']} have been made since last check, skipping')
            continue
        
    
    if noMatch == False and assetDetails['client_id'] != 1: # If asset already has client/site info skip.
        clientID = assetDetails['client_id']
        siteID = assetDetails['site_id']
    
    else:
        clientSearch = hClients.search(
            search=domain['tags'][0],
            )
        
        if clientSearch['record_count'] != 0: # get details of client (gets main site)
            clientID = clientSearch['clients'][0]['id']
            clientDetails = hClients.get(
                id=clientSearch['clients'][0]['id'],
                includedetails=True
            )
            siteID = clientDetails['main_site_id']
        else:
            print('Cannot find matching client for ' + domain['tags'][0])
            clientID = None
            siteID = None
    
    
    if domain['fqdn'] in dmeDomains.keys(): # Check if domain exists in DME
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
        {'id': gandiLinkID, 'value': 'https://admin.gandi.net/domain/' + domain['fqdn']},
        {'id': lastCheckedID, 'value': str(datetime.now())}
        ]


    hAssets.update(
    _dontaddnewfields = True,
    isassetdetails = True,
    id = assetDetails['id'] if noMatch == False else None,
    assettype_id = typeID,
    fields = domainDetails,
    client_id = clientID,
    site_id = siteID,
    inventory_number = domain['fqdn'],
    status_id = 1 if domainExpiration > today else 4,
    queueMode='queue'
    )
    print(domain['fqdn']+ ' has been queued for update')
    hAssets.update(queueMode='update')
hAssets.update(queueMode='update')
print('assets have been updated')


input()
