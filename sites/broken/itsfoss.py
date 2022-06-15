from bs4 import BeautifulSoup
import requests
import feedparser
import urllib
import datetime
from .helpers import utils

cache_refresh_time_delta = datetime.timedelta(days=1)
identifier = "itsfoss"
site_title = "ItsFoss"

rss_feed = "https://feeds.feedburner.com/ItsFoss"


def get_article(url):
    response = requests.get("https://itsfoss.com/{}".format(url))
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    article = soup.select_one("main.content > article.post")

    header = article.find("header", class_="entry-header")
    content = article.find("div", class_="entry-content")

    title = header.find("h1", class_="entry-title").text
    last_updated = header.find("time", class_="entry-modified-time").text
    author = header.find("span", class_="entry-author").text

    data = {}
    data["title"] = title
    data["subtitle"] = utils.get_subtitle(soup)
    data["last_updated"] = last_updated
    data["author"] = author

    c = []

    heading_image = utils.get_heading_image(soup)
    if heading_image is not None:
        c.append(heading_image)

    for element in content:
        el = {}
        if element.name == "p":
            el["type"] = "paragraph"
            el["value"] = element.text
        elif element.name == "div":
            if "class" in element.attrs:
                if "wp-block-image" in element["class"]:
                    el["type"] = "image"
                    img = element.find("img")
                    if img:
                        el["alt"] = img["alt"]
                        if "data-permalink" in img:
                            el["src"] = img["data-permalink"]
                        elif "src" in img:
                            el["src"] = img["src"]
                        else:
                            el["src"] = img["data-large-file"]

        elif element.name == "pre":
            if "class" in element.attrs:
                if "wp-block-code" in element["class"]:
                    el["type"] = "code"
                    el["value"] = element.text
        elif element.name == "ul":
            el["type"] = "unsorted list"
            entries = []
            for entry in element:
                if entry.name == "li":
                    entries.append({"value": entry.text})
            el["entries"] = entries
        elif (
            element.name == "h1"
            or element.name == "h2"
            or element.name == "h3"
            or element.name == "h4"
            or element.name == "h5"
            or element.name == "h6"
        ):
            el["type"] = "header"
            el["size"] = element.name
            el["value"] = element.text

        else:
            # if element.name is not None:
            #     print("Ignoring:", element.name)
            el = None

        if el is not None:
            c.append(el)

    # print(c)
    data["article"] = c

    return data


def get_recent_articles():
    feed = feedparser.parse(rss_feed)
    feed_ = []
    for entry in feed["entries"]:
        # The link provided by the feed is a google proxy link, i.e.
        # http://feedproxy.google.com/~r/ItsFoss/~3/wQc7h-hxYN4, we just want to know where it leads to
        response = requests.get(entry["link"], allow_redirects=False)
        response.raise_for_status()
        actual_link = response.headers["Location"]
        url = urllib.parse.urlparse(actual_link)
        local_link = url.path.strip("/")  # Kill annoying slashes

        feed_.append({"title": entry["title"], "link": local_link})

    return feed_


if __name__ == "__main__":
    # get_article("run-shell-script-linux")
    get_recent_articles()
