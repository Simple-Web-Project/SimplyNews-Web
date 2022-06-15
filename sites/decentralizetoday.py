from bs4 import BeautifulSoup
import requests
from datetime import timedelta
from .helpers import rss, utils

cache_refresh_time_delta = timedelta(days=1)
identifier = "dt.gl"
base = "https://dt.gl"

site_title = "Decentralize Today"
site_logo = "decentralizetoday.webp"

rss_feed = f"{base}/rss/"


def get_article(url):
    response = requests.get(f"{base}/{url}")
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    title = soup.find("h1", class_="post-title").text
    last_updated = soup.select_one(".global-meta > time").text
    author = soup.select_one(".global-meta > a").text

    content = soup.find("div", class_="post-content")

    data = {}
    data["title"] = title
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
        elif element.name == "figure":
            if "class" in element.attrs:
                if "kg-image-card" in element["class"]:
                    el["type"] = "image"
                    img = element.find("img")
                    if img:
                        el["alt"] = img.get("alt")
                        el["src"] = img["src"]
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
    return rss.default_feed_parser(rss_feed)


if __name__ == "__main__":
    print(get_recent_articles())
