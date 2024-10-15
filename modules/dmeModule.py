## DNSMade Easy calls
# 150 requests per 5 minutes.

import requests as rq
import urllib.parse
import json
from datetime import datetime, date, time,timezone
import os
import hmac
import hashlib

API_KEY = os.getenv('DME_KEY')
API_SECRET = os.getenv('DME_SECRET')
BASE_URL = 'https://api.dnsmadeeasy.com/V2.0/'

# Create formatted date for request
requestDate = datetime.now(timezone.utc).strftime('%a, %d %b %Y %X %Z')
try:
    hmac = hmac.new(
        bytes(API_SECRET, "UTF-8"),
        bytes(requestDate, "UTF-8"),
        hashlib.sha1,
    ).hexdigest()
except Exception as e:
    raise e

headers = {
    "Content-Type": "application/json",
    "x-dnsme-hmac": hmac,
    "x-dnsme-apiKey": API_KEY,
    "x-dnsme-requestDate": requestDate,
}

def getAll():
    """Get all records in accounts

    Raises:
        e: Error

    Returns:
        json.load: All domains in account.
        
    """
    try:
        response = rq.get(BASE_URL + 'dns/managed/', headers=headers)
        # Format and return
        return json.loads(response.content.decode('utf-8'))
    except Exception as e:
        raise e
