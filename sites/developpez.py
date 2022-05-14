from .helpers import rss, utils, constants
from datetime import timedelta, datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
import bs4


cache_refresh_time_delta = timedelta(hours=3)
identifier = "developpez"
site_title = "Developpez.com"
site_logo = "developpez.jpg"

base_url = "https://www.developpez.com"

rss_feed = f"{base_url}/rss"


QUOTATION_SIGN = ""
# invisible on some editors, firefox, chrome, …
# visible with gedit, vim


def get_page(url):
    response = requests.get(f"{base_url}/{url}")
    response.raise_for_status()
    response_text = response.text.replace(QUOTATION_SIGN, "'")

    soup = BeautifulSoup(response_text, "lxml")

    post = soup.select_one("article.contenuActu")

    titles = post.select("h1 div")
    title = titles[0].text
    subtitle = titles[1].text

    time = post.select_one(".date > time")
    last_updated = datetime.fromisoformat(time["datetime"])

    data = {
        "title": title,
        "subtitle": subtitle,
        "author": soup.select_one("a[itemprop=creator]").text,
        "last_updated": str(last_updated)
    }

    article = []

    content = soup.select_one(".content")

    for element in content:
        el = {}

        if isinstance(element, bs4.NavigableString):
            el["type"] = "text"
            el["value"] = str(element)
        elif element.name == "img":
            el = get_image(element)
        elif element.name == "b":
            el["type"] = "strong"
            el["value"] = element.text
        elif element.name == "br":
            el = constants.LINEBREAK
        elif element.name == "div":
            img = element.find("img")
            if img:
                el = get_image(img)

        elif element.name == "a":
            el["type"] = "link"

            href = element["href"]
            url = urlparse(href)
            if url.hostname == "www.developpez.com":
                href = "/{}{}".format(url.hostname, url.path)

            el["href"] = href
            el["value"] = element.text

        if el:
            article.append(el)
        # else:
        #     print("ignored {}".format(element.name))

    article.append(constants.LINEBREAK)
    article.append(constants.LINEBREAK)

    data["article"] = article
    return data


def get_recent_articles():
    return rss.default_feed_parser(rss_feed)


def get_image(img):
    if img is None:
        return None

    width = None
    height = None
    title = None

    if "style" in img.attrs:
        width = "60"
        height = "60"
    else:
        title = img.get("title")
        if title == ":fleche:":
            width = "15"
            height = "15"

    return {
        "type": "image",
        "src": img["src"],
        "width": width,
        "height": height,
        "alt": title or img.get("alt")
    }


if __name__ == "__main__":
    # page_url = "actu/313622/Richard-Stallman-revient-au-conseil-d-administration-de-la-Free-Software-Foundation-apres-avoir-demissionne-en-2019-et-declare-qu-il-n-a-pas-l-intention-de-demissionner-une-seconde-fois/"

    page_url = "actu/313361/Le-projet-GNU-de-Richard-Stallman-ne-veut-plus-de-code-JavaScript-non-libre-envoye-aux-navigateurs-par-les-sites-Web-et-invite-des-volontaires-a-creer-des-extensions-libres-pour-les-remplacer/"

    page = get_page(page_url)

    print(page)
