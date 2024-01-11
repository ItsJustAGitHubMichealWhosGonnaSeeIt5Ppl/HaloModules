import json
import requests as r

AUTO_BASE = 'https://developer.api.autodesk.com'

def autoCalls(header,url,extra=None):
    data = extra if extra !=None else ''
    request = r.get(AUTO_BASE + url + data, headers=header)
    if request.status_code == 200:
        return request.json()
    





class statusCheck:
    def __init__(self, code):
        self.code = code
    def halo(self):
        if self.code == 200:
            return 'Success'
        




statCode = 200

print(statusCheck(statCode).halo())