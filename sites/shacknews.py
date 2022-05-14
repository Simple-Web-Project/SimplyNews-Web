from bs4 import BeautifulSoup
import requests
from datetime import timedelta
from .helpers import rss, utils

cache_refresh_time_delta = timedelta(hours=12)
identifier = "shacknews"
base_url = "https://shacknews.com"

site_title = "Shack News"
site_logo = "shacknews.webp"

rss_feed = f"{base_url}/feed/rss"


def get_page(url):
    response = requests.get(f"{base_url}/{url}")
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    data = {
        'title': soup.find('h1', class_='article-title').text,
        'subtitle': soup.find('div', class_='article-lead-bottom-content').find('description').text,
        'author': soup.find('div', class_='article-lead-bottom').find('div', class_='by-line').find('a').text,
        'last_updated': soup.find('div', class_='time-stamp').text
    }

    c = []

    heading_image = utils.get_heading_image(soup)
    if heading_image is not None:
        c.append(heading_image)

    for element in soup.find('section', class_='article-content').find('main'):
        el = {}
        if element.name == 'p':
            vid = element.find('iframe')
            if vid is not None:
                print()
                el['type'] = 'iframe'
                el['src'] = utils.fix_link(vid['src'])
                el["width"] = vid.get("width")
                el["height"] = vid.get("height")
            else:
                el['type'] = 'paragraph'
                el['value'] = element.text
        elif element.name == 'blockquote':
            el["type"] = "blockquote"
            el['value'] = element.text
        elif element.name in ("h1", 'h2', 'h3', 'h4', 'h5', 'h6'):
            el['type'] = 'header'
            el['size'] = element.name
            el['value'] = element.text
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
    # page = get_recent_articles()

    page_url = "article/122896/watch-nasas-perseverance-rovers-new-video-and-images-here"
    # youtube iframe

    page = get_page(page_url)
