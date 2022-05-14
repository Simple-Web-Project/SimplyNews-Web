from bs4 import BeautifulSoup
import requests
from datetime import timedelta
from .helpers import rss

cache_refresh_time_delta = timedelta(hours=1)
identifier = "nypost"
base_url = "https://nypost.com"

site_title = "New York Post"

rss_feed = f"{base_url}/feed/"


def get_page(url):
    response = requests.get(f"{base_url}/{url}")
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    last_updated_p = soup.find("p", class_="byline-date").text.split("|")
    last_updated = " ".join(
        (
            last_updated_p[0].strip("\n").strip("\t"),
            last_updated_p[1].strip("\n").strip("\t"),
        )
    )

    data = {
        "title": soup.select_one(".article-header h1").text.strip('\n').strip(),
        "author": soup.select_one("#author-byline .byline").text.replace("By ", ""),
        "last_updated": last_updated,
    }

    c = []
    standard_article_image = soup.find("img", id="standard-article-image")
    if standard_article_image:
        c.append(
            {
                "type": "image",
                "src": standard_article_image["src"],
                "alt": standard_article_image["alt"],
            }
        )

    for element in soup.find("div", class_="entry-content"):
        el = {}

        if element.name == "p":
            el["type"] = "paragraph"
            el["value"] = element.text
        elif element.name == "figure":
            el["type"] = "image"
            if "class" in element.attrs:
                if "wp-block-image" in element["class"]:
                    image = element.find("img")
                    el["src"] = image["data-srcset"].split(" ")[0]
                    el["alt"] = image["alt"]
        elif element.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            el["type"] = "header"
            el["size"] = element.name
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
    # get_page("2021/01/30/john-chaneys-kindness-wont-be-forgotten/")
