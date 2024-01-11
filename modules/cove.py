import requests
import urllib.parse
import json
import os

partName = ''
username = ''
password = ''
BASE_URL = ''

def authCove():
    {
    "jsonrpc":"2.0",
    "method":"Login",
    "params":{
	    "partner":partName,
	    "username":username,
	    "password":password
    },
    "id":"1"
}
    
    
    
