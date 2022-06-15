from .helpers import utils, constants
from datetime import timedelta, datetime, date
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import requests
import locale
import urllib

cache_refresh_time_delta = timedelta(hours=6)
identifier = "mediapart"
site_title = "Mediapart"
base_url = "https://www.mediapart.fr"
PAYWALL_TEXT = [
    {
        "type": "strong",
        "value": "Cet article est réservé aux abonnés."
    },
    constants.LINEBREAK,
    constants.LINEBREAK,
]


def format_date_short(date):
    return date.strftime("%d/%m/%Y à %Hh%M%z")


def format_date(date):
    return date.strftime("%d/%m/%Y")


def get_image(img):
    if img is None:
        return None

    return {
        "type": "image",
        "src": img["src"],
        "alt": img.get("alt"),
        "width": img.get("width"),
        "height": img.get("height")
    }


def fix_link(link):
    if link is None or "blogs.mediapart.fr" in link:
        return None

    link = utils.fix_link(link, domain="mediapart.fr")

    return link


def get_iframe(element):
    if element is None:
        return None

    iframe = element.find("iframe")
    if iframe:
        src = fix_link(iframe["src"])
        url = urlparse(src)
        params = parse_qs(url.query)
        if "src" in params:
            src = params["src"]
            if isinstance(src, list):
                src = src[0]

        return {
            "type": "iframe",
            "src": src,
            "with": iframe.get("width"),
            "height": iframe.get("height"),
            "title": iframe.get("title")
        }


def get_article(url):
    full_url = f"{base_url}/{url}"
    response = requests.get(full_url)
    soup = BeautifulSoup(response.text, "lxml")

    published = datetime.fromisoformat(
        soup.find("meta", property="og:article:published_time")["content"])
    published_text = format_date_short(published)

    last_updated = "Publié le {}".format(published_text)

    updated = soup.find("meta", property="og:article:modified_time")
    if updated:
        updated = datetime.fromisoformat(updated["content"])
        last_updated = "{}, mis à jour le {}".format(
            last_updated, format_date_short(updated))

    data = {
        "title": soup.find("meta", property="og:title")["content"],
        "subtitle": utils.get_subtitle(soup),
        "author": soup.select_one("meta[name=author]")["content"],
        "last_updated": last_updated
    }

    article = []

    paywall = soup.select_one("p.reserved-content")
    dossier = "/dossier/" in url
    if paywall:
        content = soup.select_one("div.content-article.content-restricted")

        portfolio = content.select_one(".portfolio-list")
        if portfolio:
            img = get_image(portfolio.select_one("div.media img"))
            if img:
                article.append(img)

            context = portfolio.select_one("div.context") or []
            for element in context:
                el = get_element(element)

                if el:
                    article.append(el)
        else:
            article.append({
                "type": "paragraph",
                "value": content.find("p").text
            })
        article.extend(PAYWALL_TEXT)

    elif dossier:
        # links to multiple articles
        articles = soup.select(".une-block div[data-type=article]") or []
        for art in articles:
            article_ = get_article(art)

            if article_:
                article.extend(article_)

        all_articles = soup.select("div.bullet-list.universe-journal ul li")
        if all_articles:
            article.append({
                "type": "header",
                "size": "h2",
                "value": "Tous les articles"
            })
            for art in all_articles:
                article_ = get_article(art)

                if article_:
                    article.extend(article_)

            article.append(constants.LINEBREAK)
            article.append(constants.LINEBREAK)

    else:
        content = soup.select_one("div.page-pane") or []
        for element in content:
            el = get_element(element)

            if el:
                article.append(el)

    data["article"] = article

    return data


def get_title_and_link(a, size="h3", generic_text=True):
    if a is None:
        return None

    href = fix_link(a["href"])
    if href is None:
        return None

    title = a.select_one(".title")
    if title:
        title = title.text
    else:
        title = a.text

    return [
        {
            "type": "header",
            "size": size,
            "value": title
        },
        {
            "type": "link",
            "href": href,
            "value": "Lien vers l'article." if generic_text else title
        }
    ]


def get_element(element):
    if element is None:
        return None

    el = {}

    if element.name == "p":
        iframe = get_iframe(element)
        if iframe:
            el = iframe
        else:
            el = {
                "type": "paragraph",
                "value": element.text
            }

    elif element.name == "div":
        el = get_iframe(element)

    # else:
    #     print("Ignored {}".format(element.name))

    return el


def get_article(art):
    if art is None:
        return None

    article = []
    for element in art:

        if utils.value_in_element_attr(element, "title"):
            a = element if element.name == "a" else element.find("a")
            title_and_link = get_title_and_link(a)
            if title_and_link:
                article.extend(title_and_link)

        elif utils.value_in_element_attr(element, "author"):
            time = element.find("time")
            if time:
                time = date.fromisoformat(time["datetime"])
                time = format_date(time)
                article.append({
                    "type": "text",
                    "value": "Publié le"
                })
                article.append({
                    "type": "strong",
                    "value": time
                })
                article.append({
                    "type": "text",
                    "value": "par"
                })
            else:
                article.append({
                    "type": "text",
                    "value": "Publié par"
                })

            article.append({
                "type": "strong",
                # author
                "value": element.select_one(".journalist").text
            })

        elif element.name == "div":
            img = get_image(element.find("img"))
            if img:
                article.append(constants.LINEBREAK)
                article.append(constants.LINEBREAK)
                article.append(img)

            p = element.find("p")
            if p:
                article.append({
                    "type": "paragraph",
                    "value": p.text
                })

    return article


def get_recent_articles():
    response = requests.get("https://www.mediapart.fr/journal/fil-dactualites")
    soup = BeautifulSoup(response.text, "lxml")

    feed = []

    for element in soup.select("div.simple-list ul li"):
        a = element.find("a")
        url = a["href"].strip("/")
        if "journal/" in url:
            feed.append({
                "title": a.text,
                "link": url,
            })
    return feed


if __name__ == "__main__":
    # page_url = "journal/france/060321/proportionnelle-bayrou-presse-macron-d-honorer-sa-promesse"
    # paywall

    # page_url = "journal/france/150720/l-air-libre-le-squale-operations-secretes"
    # no paywall

    # page_url = "journal/france/150720/l-air-libre-le-squale-operations-secretes"
    # embedly embed

    page_url = "journal/international/dossier/navalny-l-anti-poutine"
    # dossier

    # page = get_recent_articles()
    page = get_article(page_url)

    print(page)
