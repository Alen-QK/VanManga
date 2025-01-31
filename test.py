import requests
import json

from DrissionPage._pages.session_page import SessionPage
from bs4 import BeautifulSoup
from utils.ua_producer import ua_producer


target_link = "https://dogemanga.com/m/TCBp0BWc"
response = None
drissionSession = SessionPage()


drissionSession.get(target_link)
response = drissionSession.response

soup = BeautifulSoup(response.text, "lxml")
dmac_modal = soup.find("h5", class_="modal-title")
if dmac_modal:
    if "DMCA" in dmac_modal.text:
        print(111111111)
else :
    print(222222222)

print(soup.prettify())
