from bs4 import BeautifulSoup
import requests
from datetime import timedelta
from .helpers import rss

base_url = "https://heise.de"

cache_refresh_time_delta = timedelta(hours=12)
identifier = "heise.de"
site_title = "heise online"
site_logo = "heise.webp"

rss_feed = f"{base_url}/rss/heise-atom.xml"


def get_article(url):
    response = requests.get(f"{base_url}/{url}?seite=all")
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    data = {
        "title": soup.find("h1", class_="a-article-header__title").text.strip("\n"),
        "author": soup.find("ul", class_="a-creator__names").text.strip("\n"),
        "last_updated": soup.find("time", class_="a-publish-info__datetime")[
            "datetime"
        ],
    }

    c = []
    header_lead_text = soup.find("p", class_="a-article-header__lead")

    c.append({"type": "paragraph", "value": header_lead_text.text.strip("\n")})

    article_title_image = soup.find(
        "div", class_="article-image__gallery-container"
    ).find("img")
    c.append(
        {
            "type": "image",
            "alt": article_title_image["alt"],
            "src": article_title_image["src"],
        }
    )

    for element in soup.find("div", class_="article-content"):
        el = {}
        if element.name == "p":
            el["type"] = "paragraph"
            el["value"] = element.text.strip()
        elif element.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            el["type"] = "header"
            el["size"] = element.name
            el["value"] = element.text
        elif element.name == "figure":
            if "class" in element.attrs:
                if "video" in element["class"]:
                    vid = element.find("embetty-video")
                    if vid:
                        if vid["type"] == "youtube":
                            el["type"] = "video"
                            el["src"] = "https://www.youtube.com/watch?v={}".format(
                                vid["video-id"])

        elif element.name == "a-paid-content-teaser":
            el["type"] = "header"
            el["size"] = "h3"
            el["value"] = "um weiterzulesen, brauchen sie heise+"
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
    # get_article(
    #    "hintergrund/Missing-Link-Roboter-Androide-ueber-Maschinenwesen-und-ihre-Vermenschlichung-5040488.html"
    # )
    print(get_recent_articles())
