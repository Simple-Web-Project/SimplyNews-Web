import os
import shutil
import json
from sites.links import *
import hashlib
import utils.config
import threading
import datetime
import time
import urllib
from colorama import Fore, Back, Style

cache_path = './cache'

os.makedirs(cache_path, exist_ok=True)
shutil.rmtree(cache_path)


def set_recent_articles(site_module):
    path = f'{cache_path}/{site_module.identifier}'
    os.makedirs(path, exist_ok=True)
    recent_articles = site_module.get_recent_articles()
    with open(f'{path}/recent_articles.json', "w") as cache_file:
        data = json.dumps(recent_articles, ensure_ascii=False, indent=4)
        cache_file.write(data)
    return recent_articles


def get_recent_articles(site_module):
    path = f'{cache_path}/{site_module.identifier}'
    full_path = f'{path}/recent_articles.json'
    if os.path.isfile(full_path):
        with open(full_path, "r") as cache_file:
            return json.loads(cache_file.read())


def get_article(site_module, article_path):
    hashed_name = hashlib.md5(article_path.encode('utf-8')).hexdigest()
    path = f'{cache_path}/{site_module.identifier}/{hashed_name}.json'
    if os.path.isfile(path):
        with open(path, "r") as cache_file:
            return json.loads(cache_file.read())

def set_article(site_module, article_path):
    article = site_module.get_article(article_path)
    article_path = urllib.parse.unquote(article_path)
    hashed_name = hashlib.md5(article_path.encode('utf-8')).hexdigest()
    path = f'{cache_path}/{site_module.identifier}/{hashed_name}.json'
    os.makedirs(f'{cache_path}/{site_module.identifier}/', exist_ok=True)
    with open(path, "w") as cache_file:
        data = json.dumps(article, ensure_ascii=False, indent=4)
        cache_file.write(data)
    return article


def cache_interval():
    def get_site_articles_content(sites_module):
        old = get_recent_articles(sites_module)
        new = set_recent_articles(sites_module)
        if old != new:
            for article in new:
                set_article(sites_module, article['link'])

    while True:
        t1 = datetime.datetime.now().replace(microsecond=0)

        threads = []
        for identifier in sites_list.keys():
            threads.append(
                threading.Thread(
                    target=get_site_articles_content,
                    args=(sites_list[identifier],)
                )
            )
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        t2 = datetime.datetime.now().replace(microsecond=0)

        print(
            Fore.BLUE + f'Finished caching. It took: {int((t2-t1).total_seconds())}s' + Style.RESET_ALL)
        time_interval = int(utils.config.cfg["settings"]["timeInterval"]) * 60
        time.sleep(time_interval)
