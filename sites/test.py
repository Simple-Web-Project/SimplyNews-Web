from bs4 import BeautifulSoup
import requests
import json
from datetime import timedelta
import urllib
import feedparser
import re




page = json.dumps(myList, ensure_ascii=False, indent=4)
with open('result.json', "w") as cache_file:
    cache_file.write(page)
