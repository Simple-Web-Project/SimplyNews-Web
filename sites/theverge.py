from bs4 import BeautifulSoup
import requests
from datetime import timedelta
import feedparser
import urllib
import re
from colorama import Fore, Back, Style

cache_refresh_time_delta = timedelta(hours=12)
identifier = "theverge"
site_title = "theverge.com"
site_logo = "the_verge.webp"

base_url = "https://theverge.com"

rss_feed = f"{base_url}/rss/index.xml"


def get_page(url):
    response = requests.get(f"{base_url}/{url}")
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    data = {
        "title": soup.find("h1", class_="c-page-title").text,
        "subtitle": soup.select_one("p.c-entry-summary").text,
        "author": soup.find("span", class_="c-byline__author-name").text,
        "last_updated": soup.find("time", class_="c-byline__item").text.strip('\n').strip(),
    }

    title_image = soup.find("picture", class_="c-picture").find("img")
    c = []
    c.append({"type": "image", "src": title_image["src"]})

    for element in soup.find("div", class_="c-entry-content"):
        el = {}
        if element.name == "p":
            el["type"] = "paragraph"
            el["value"] = element.text
        elif element.name == "blockquote":
            el["type"] = "blockquote"
            el["value"] = element.text
        else:
            # if element.name is not None:
            #     print("Ignoring:", element.name)
            el = None

        if el is not None:
            c.append(el)
    data["article"] = c

    return data


def get_recent_articles():
    feed = feedparser.parse(rss_feed)
    feed_ = []
    for entry in feed["entries"]:
        url = urllib.parse.urlparse(entry["link"])
        # if url.hostname in links.sites:
        local_link = url.path.strip("/")  # Kill annoying slashes
        image = re.findall(r"<img.*src=\"(.*)\".*\/>",
                           entry["content"][0]["value"])[0]

        date = re.findall("(..*)T(.*?:.*?):", entry["updated"])
        
        updated = 'last updated ' + date[0][0] + ', ' + date[0][1]
        
        feed_.append({
            "title": entry["title"],
            "link": local_link,
            "image": image,
            "date": updated,
            "author": entry['author'],
        })
        print(Fore.GREEN + 'Fetched ' + Style.RESET_ALL + f'{base_url}/{urllib.parse.unquote(local_link)}')
    return feed_


if __name__ == "__main__":
    print(get_page("2021/1/30/22257721/whatsapp-status-privacy-facebook-signal-telegram/"))
    # print(get_recent_articles())
