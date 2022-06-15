from bs4 import BeautifulSoup
import requests
from datetime import timedelta
from .helpers import rss

base_url = "https://gameinformer.com"

cache_refresh_time_delta = timedelta(hours=12)
identifier = "gameinformer.com"
site_title = "GameInformer"
site_logo = "gameinformer.webp"

rss_feed = f"{base_url}/rss.xml"

def get_article(url):
    full_url = f"{base_url}/{url}"
    response = requests.get(full_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    author = "None"
    last_updated = "None"
    el_idx = 0
    for element in soup.find('div', class_='author-details'):
        if el_idx == 1:
            author = element.text
        elif el_idx == 2:
            last_updated = element
        el_idx += 1

    data = {
        'title': soup.find('h1', class_='page-title').text.strip('\n'),
        'author': author,
        'last_updated': last_updated,
    }

    c = []

    title_img = soup.select_one('.region-content > .ds-full-width > .field > .layout > .layout__region > .full-width > .field > img')
    src = title_img['src']
    if src.startswith('/'):
        src = f"{base_url}{src}"

    c.append({
        'type': 'image',
        'alt': title_img['alt'],
        'src': src
    })


    main = soup.find('div', class_='ds-main')
    for element in main.select('*'):
        el = {}
        if element.name == 'p':
            el['type'] = 'paragraph'
            el['value'] = element.text
        elif element.name == 'img':
            src = element['src']
            if src.startswith('/'):
                src = f"{base_url}{src}"
            el['type'] = 'image'
            el['alt'] = element['alt']
            el['src'] = src
        elif element.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            el["type"] = "header"
            el["size"] = element.name
            el["value"] = element.text
        elif element.name == 'div':
            if 'class' in element.attrs:
                # we don't need anything below that point
                if 'author-footer' in element['class']:
                    break
        else:
            # if element.name is not None:
            #     print("Ignoring:", element.name)
            el = None
        
        if el is not None:
            c.append(el)

    data['article'] = c
    return data

def get_recent_articles():
    return rss.default_feed_parser(rss_feed)

if __name__ == "__main__":
    print(get_recent_articles())
    #get_article("2021/01/26/the-lord-of-the-rings-gollum-gets-delayed-to-2022")
    #get_article("2021/01/29/what-it-would-really-take-to-get-me-back-into-pokemon")
