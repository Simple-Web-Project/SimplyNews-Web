from bs4 import BeautifulSoup
import requests
from datetime import timedelta
from .helpers import rss, utils
from .helpers import constants

base_url = "https://androidauthority.com"

cache_refresh_time_delta = timedelta(hours=12)
identifier = "androidauthority"

site_title = "Android Authority"

rss_feed = f"{base_url}/feed/"


def get_page(url):
    response = requests.get(
        f"{base_url}/{url}", headers={"User-Agent": constants.USER_AGENT}
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    data = {
        "title": soup.find("h1", class_="main-title").text,
        "subtitle": utils.get_subtitle(soup),
        "author": soup.find("div", class_="author-name-block").find("a").text,
        "last_updated": soup.find("span", class_="publication-time").text,
    }

    c = []

    heading_image = utils.get_heading_image(soup)
    if heading_image is not None:
        c.append(heading_image)

    for element in soup.find("div", id="content-anchor-inner"):

        if element.name == "p":
            for sub_element in element:
                el = {}

                if sub_element.name == None:
                    el["type"] = "text"
                    el["value"] = sub_element
                elif sub_element.name == "a":
                    el["type"] = "link"
                    el["value"] = sub_element.text
                    el["href"] = sub_element["href"]
                elif sub_element.name == "img":
                    el["type"] = "image"
                    el["alt"] = sub_element["alt"]
                    el["src"] = sub_element["src"]
                elif sub_element.name == "em":
                    el["type"] = "em"
                    el["value"] = sub_element.text
                elif sub_element.name == "strong":
                    el["type"] = "strong"
                    el["value"] = sub_element.text
                else:
                    el = None

                if el is not None:
                    c.append(el)
            # its the end of a paragraph, therefore add a linebreak
            c.append({"type": "linebreak"})
        elif element.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            el["type"] = "header"
            el["size"] = element.name
            el["value"] = element.text
        # else:
        #     if element.name is not None:
        #         print("Ignoring:", element.name)

    data["article"] = c

    return data


def get_recent_articles():
    return rss.default_feed_parser(rss_feed)


if __name__ == "__main__":
    # page = get_page("pioneer-dolby-atmos-add-on-speakers-deal-1196972")
    page = get_recent_articles()
    print(page)
