import requests
import json
from bs4 import BeautifulSoup
from utils.ua_producer import ua_producer
from opencc import OpenCC

cc = OpenCC('t2s')
sample = "繁体中文asdsafas 111233"
result = cc.convert(sample)
print(result)


