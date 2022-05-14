from .helpers import rss
from .helpers import constants
from datetime import timedelta
from bs4 import BeautifulSoup
import requests

cache_refresh_time_delta = timedelta(hours=12)
identifier = "androidpolice"
site_title = "Android Police"

base_url = "https://www.androidpolice.com"

rss_feed = f"{base_url}/rss"


def get_image(image):
    data = {}

    if image is None:
        return data

    if image.name == "a":
        img = image.find("img")
        src = image["href"]
        alt = img["alt"] if "alt" in img else ""
    elif image.name == "img":
        src = image["src"]
        alt = image["alt"]
    else:
        return data

    return {
        "type": "image",
        "src": src,
        "alt": alt
    }


def get_page(url):
    response = requests.get(
        f"{base_url}/{url}", headers={"User-Agent": constants.USER_AGENT}
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    post = soup.select_one(".post")
    header = post.select_one("header.post-header")

    title_element = header.select_one("h2[itemprop=name]")

    title = title_element.find("a").text
    subtitle_element = title_element.select_one("div.subtitle")
    if subtitle_element is None:
        subtitle = None
    else:
        subtitle = subtitle_element.find("a").text

    post_meta = header.select_one("div.post-meta")

    author = post_meta.select_one("a.author-name").text

    time = post_meta.select_one("time.timeago")
    # for exact time use time["datetime"]
    last_updated = time.text

    data = {
        "title": title,
        "subtitle": subtitle,
        "author": author,
        "last_updated": last_updated
    }

    article = []

    article.append(get_image(post.select_one("a.post-hero")))

    post_content = post.select_one("div.post-content")

    for element in post_content:
        el = {}
        if element.name == "p":
            if "style" in element.attrs:
                a = element.find("a")
                if a is not None:
                    for image in a:
                        el = get_image(image)
                        article.append(el)
                        el = {}
            else:
                if element.text != "":
                    el["type"] = "paragraph"
                    el["value"] = element.text
        elif element.name == "div":
            if "class" in element.attrs:
                if "note-wrapper" in element["class"]:
                    note = element.select_one("div.note")
                    for elt in note:
                        if elt.name == "p":
                            el["type"] = "paragraph"
                            el["value"] = elt.text
                            article.append(el)
                            el = {}

        elif element.name == "ol" or element.name == "ul":
            el["type"] = "unsorted list"
            entries = []
            for entry in element:
                if entry.name == "li":
                    entries.append({"value": entry.text})
            el["entries"] = entries
        else:
            el = None

        if el is not None and el != {}:
            article.append(el)

    data["article"] = article

    return data


def get_recent_articles():
    return rss.default_feed_parser(rss_feed)


if __name__ == "__main__":

    # page_url = "2021/02/18/android-12-developer-preview-1-downloads-are-live-heres-how-to-get-them/"
    # article with a warning note

    # page_url = "2021/02/18/android-12s-screenshot-editor-is-getting-a-lot-better"
    # article with image galery

    page_url = "2021/02/18/the-first-android-12-preview-lands-today-with-more-changes-than-we-expected"
    # no subtitle

    page = get_page(page_url)
    # page = get_recent_articles()

    print(page)
