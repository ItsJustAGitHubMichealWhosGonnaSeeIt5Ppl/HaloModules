# Invoice updater
from modules.HaloPSA.HaloV3 import assets, sites, clients, recurringInvoices
import modules.dmeModule as dme
import modules.gandiModules as gandi
from datetime import datetime,timezone # TIMEZONE IS USED


# Domain line item IDs
lineItemIDs = {
    'uk': 172,
    'co.uk': 172,
    'org.uk': 172,
    'com': 173,
    'info':176,
    'co': 175,
    'net': 177,
    'org':178,
    'other':179 # Any non-standard domains
    }

hAssets = assets()
hRecurring = recurringInvoices()

allDomainAssets = hAssets.search(order='client_name',assettype_id=137) # Get all domain assets, sorted by client


currentClientID = 0
clientDomains = {}
for domain in allDomainAssets['assets']:
    customDomain = False
    
    if domain['status_id'] != 1: # Skip expired/inactive domains
        print(f'[{domain['key_field']}] inactive/expired, skipping.')
        continue
    elif domain['key_field2'] not in lineItemIDs.keys():
        print(f'[{domain['key_field']}] No ID for {domain['key_field2']}, setting to custom')
        customDomain = True
    tldID = str(lineItemIDs[domain['key_field2']] if customDomain == False else 179)
    clientID = str(domain['client_id'])
    
    if clientID in clientDomains.keys() and tldID in clientDomains[clientID]:
        clientDomains[str(domain['client_id'])][tldID] += [domain]
        
    elif clientID in clientDomains.keys() and tldID not in clientDomains[clientID]:
        clientDomains[str(domain['client_id'])].update({tldID: [domain]})

    elif clientID not in clientDomains.keys():
        clientDomains[str(domain['client_id'])] = {tldID: [domain]}
        
    else:
        continue

print('test.')
debug = True
for client,domains in clientDomains.items():

    invoices = hRecurring.search(client_id=client,includelines=True) # Get client invoices
    
    for invoice in invoices['invoices']:
        if invoice['disabled'] == True: # Skip disabled invoices
            continue
        else:
            for item in invoice['lines']:
                domainString = ''
                if str(item['_itemid']) in domains.keys(): # Check if item is a domain item
                    for domain in domains[str(item['_itemid'])]:
                        domainString += '\n' + domain['key_field']
                    
                    newDesc = item['item_longdescription'].split('\n')[0] +  domainString
                    
                    print(newDesc)
                    
                    if debug == False:
                        hRecurring.updateLines(
                            customFields=[],
                            id=item['id'],
                            ihid=item['ihid'],
                            item_longdescription=newDesc)
                    
