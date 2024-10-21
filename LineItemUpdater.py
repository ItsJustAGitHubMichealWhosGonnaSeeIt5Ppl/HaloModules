# Invoice updater
from modules.HaloPSA.HaloV3 import assets, sites, clients, recurringInvoices
import modules.dmeModule as dme
import modules.gandiModules as gandi
from datetime import datetime,timezone # TIMEZONE IS USED


#TODO alert if a domain does not have a valid invoice.
#TODO Add field in asset to exclude a domain from invoicing, with a reason
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
for domain in allDomainAssets['assets']: # Format data 
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
    typesToBeInvoiced = list(domains.keys())
    typesInvoiced = [] # Domain types invoiced.
    invoices = hRecurring.search(client_id=client,includelines=True) # Get client invoices
    if invoices['record_count'] == 0:
        print(f'no invoices on record for client ID: {client}')
        input('press any key to continue')
        continue
        
    for invoice in invoices['invoices']:
        if invoice['disabled'] == True: # Skip disabled invoices
            continue
        else:
            for item in invoice['lines']:
                domainString = ''
                if str(item['_itemid']) in domains.keys(): # Check if item is a domain item
                    typesInvoiced += [str(item['_itemid'])]
                    
                    if len(domains[str(item['_itemid'])]) != item['qty_order']:
                        print(f'[{invoice['client_name']}]: Invoice {invoice['id']} quantity for {item['nominal_code']} is wrong. Should be {len(domains[str(item['_itemid'])])}, currently {item['qty_order']}')
                        input('press any key to continue')
                    for domain in domains[str(item['_itemid'])]:
                        domainString += '\n' + domain['key_field']
                    
                    newDesc = item['item_longdescription'].split('\n')[0] +  domainString
            
                    if debug == False: # send request
                        hRecurring.updateLines(
                            customFields=[],
                            id=item['id'],
                            ihid=item['ihid'],
                            item_longdescription=newDesc)
                    else:
                        print(f'=============\nDebug enabled, old description was:\n{item['item_longdescription']}\nNew line item would have been: \n{newDesc}')
    remainingIDs = list(set(typesToBeInvoiced) -  set(typesInvoiced)) # Should be zero
    if len(remainingIDs) != 0:
        print(f'{invoices['invoices'][0]['client_name']} is missing lineitem(s) for {remainingIDs}')
        input('press any key to continue')

