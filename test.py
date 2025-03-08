import requests
import json

from DrissionPage._pages.session_page import SessionPage
from bs4 import BeautifulSoup
from utils.ua_producer import ua_producer


a = "123 最近更新： 456"
print(a.split("最近更新： "))