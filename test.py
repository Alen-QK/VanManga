import requests
from requests_ip_rotator import ApiGateway
from modules.ua_producer import ua_producer

AKey = 'AKIASNMDRWNVXZ2MOOOV'
Apwd = 'to4Tt69sO7wYUD4Bs2LAfPDgsfmlVRJODh7IzgyG'
headers = {'User-Agent': ua_producer()}

gateway = ApiGateway('https://www.dogemanga.com', access_key_id= AKey, access_key_secret= Apwd)
gateway.start()

session = requests.Session()
session.mount('https://www.dogemanga.com', gateway)

r = session.get('https://www.dogemanga.com', headers= headers)

print(r.status_code)
gateway.shutdown()