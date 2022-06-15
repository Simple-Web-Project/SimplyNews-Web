from .helpers import rss, utils
from bs4 import BeautifulSoup
from html import unescape
import requests
import json
import feedparser
import urllib
from colorama import Fore, Back, Style

identifier = "francetvinfo.fr"
site_title = "Franceinfo"
site_logo = "francetvinfo.webp"

base_url = "https://www.francetvinfo.fr"
rss_feed = f"{base_url}/titres.rss"

# https://www.francetvinfo.fr/titres.rss

def get_image(img):
    if img is None:
        return None

    if "data-src" in img.attrs:
        src = "{}{}".format(base_url, img["data-src"])
    else:
        src = img["src"]

    # ignore The Conversation's pixel tracking
    if "count.gif" in src:
        return None

    return {
        "type": "image",
        "src": src,
        "alt": img.get("alt") or img.get("title")
    }

def get_iframe(iframe):
    if iframe is None:
        return None

    el = {}

    if "data-src" in iframe.attrs:
        src = iframe["data-src"]
    else:
        src = iframe["src"]

    el["type"] = "iframe"
    el["src"] = src
    el["width"] = iframe.get("width")
    el["height"] = iframe.get("height")
    return el


def get_article(url):
    response = requests.get(f"{base_url}/{url}")
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    title = soup.select_one("title").text
    subtitle = soup.select_one("meta[name=description]")["content"]
    subtitle = unescape(subtitle)

    json_element = soup.find("script", type="application/ld+json")
    info = json.loads(json_element.next)

    author = info["author"]
    authors = []
    if isinstance(author, list):
        for auth in author:
            authors.append(auth["name"])
    elif isinstance(author, dict):
        authors.append(author["name"])
    else:
        print("could not get author")
    author = ", ".join(authors)

    post = soup.select_one("article")
    aside = post.select_one("aside")

    if aside:
        heading_image = post.select_one("div.left-wrapper > figure img")
        post_content = post.select_one("div.text")
    else:
        heading_image = post.select_one("div.c-cover figure img")
        post_content = post.select_one("div.c-body")

    data = {
        "title": title,
        "subtitle": subtitle,
        "author": author,
    }

    article = []

    if heading_image:
        article.append(get_image(heading_image))

    heading_video = post.select_one(
        ".c-cover > .resp-video") or post.select_one("figure.video")
    if heading_video:
        iframe_element = heading_video.select_one("iframe")
        iframe = get_iframe(iframe_element)
        if iframe:
            article.append(iframe)

    heading_video = post.select_one(
        ".c-cover > figure.francetv-player-wrapper") or post.select_one("figure.player-video")
    if heading_video:
        if info and "video" in info:
            video = info["video"]

            if isinstance(video, list):
                video = video[0]

            src = video.get("embedUrl") or video.get("embedURL")
            width = video.get("width")
            if width:
                width = width.get("value")
            height = video.get("height")
            if height:
                height = height.get("value")

            article.append({
                "type": "iframe",
                "src": src,
                "title": video.get("name"),
                "width": width,
                "height": height
            })

        # else: embedded live stream, but it's not using iframe and blob src url for <video> then hard to extract

    for element in post_content:
        el = {}

        if element.name == "p":
            iframe = element.select_one("iframe")
            img = element.select_one("img")
            if iframe:
                el["type"] = "iframe"
                el["src"] = iframe["src"]
                style = iframe.get("style")
                if style:
                    styles = style.split(";")
                    for value in styles:
                        stripped = value.strip(" ;")
                        if stripped.startswith("height:"):
                            el["height"] = stripped.replace("height: ", "")
            elif img:
                el = get_image(img)

            elif ">>" not in element.text:  # ignore related article links
                el = get_paragraph(element.text)

        elif element.name == "blockquote":
            el["type"] = "blockquote"
            el["value"] = element.text
            if utils.value_in_element_attr(element, "twitter-tweet"):
                article.append(el)
                links = element.select("a")
                for link in links:
                    el = {
                        "type": "link",
                        "href": link["href"],
                        "value": link.text
                    }
                    article.append(el)

                el = {}

        elif element.name == "span":
            el = get_paragraph(element.text)

        elif element.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            el["type"] = "header"
            el["size"] = element.name
            el["value"] = element.text

        elif element.name == "figure":
            iframe = get_iframe(element.select_one("iframe"))
            if iframe:
                el = iframe

        elif element.name == "ul":
            el["type"] = "unsorted list"
            entries = []
            for entry in element:
                if entry.name == "li":
                    entries.append({"value": entry.text})
            el["entries"] = entries

        if el:
            article.append(el)

    if utils.value_in_element_attr(post, "content-slideshow"):
        for element in post.select(".photo") or []:
            img = get_image(element.find("img"))
            if img:
                article.append(img)
            caption = element.find("figcaption")
            if caption:
                article.append(get_paragraph(caption.text))

    data["article"] = article
    return data


def get_paragraph(text):
    cleaned = text.strip("\n")
    if cleaned == "":
        return None
    else:
        return {
            "type": "paragraph",
            "value": cleaned
        }


def get_recent_articles():
    feed = feedparser.parse(rss_feed)
    feed_ = []
    for entry in feed["entries"]:
        url = urllib.parse.urlparse(entry["link"])

        local_link = url.path.strip("/")  # Kill annoying slashes

        feed_.append({
            "title": entry["title"],
            "link": local_link,
            "image": entry['links'][1]['href']
        })
        print(Fore.GREEN + 'Fetched ' + Style.RESET_ALL +
              f'{base_url}/{urllib.parse.unquote(local_link)}')
    return feed_


if __name__ == "__main__":
    # page = get_recent_articles()

    # page_url = "sante/maladie/coronavirus/vaccin/direct-covid-19-la-vaccination-accelere-mais-reste-inegale-entre-les-pays-riches-et-pauvres_4305451.html"
    # "live" article, multiple authors

    # page_url = "sante/maladie/coronavirus/covid-19-le-medecin-jerome-marty-appelle-a-des-frappes-chirurgicales-contre-lepidemie-avec-des-mesures-localisees_4305769.html"
    # blockquote

    # page_url = "sante/maladie/coronavirus/video-covid-19-ne-venez-pas-ce-n-est-pas-le-moment-lance-aux-touristes-christian-estrosi-le-maire-de-nice_4305491.html"
    # heading_video, dailymotion iframe

    # page_url = "sante/maladie/coronavirus/covid-19-le-masque-en-creche-gene-t-il-la-sociabilisation-des-tout-petits_4303509.html"
    # YouTube iframe

    # page_url = "sante/maladie/coronavirus/confinement/alpes-maritimes-les-mesures-envisagees-par-le-gouvernement-face-a-l-envolee-des-cas-decovid-19_4305859.html"
    # heading_video, akamaidh iframe

    # page_url = "sciences/mars-curiosity/premier-son-capte-sur-mars-le-concepteur-d-un-des-micros-de-perseverance-explique-pourquoi-il-est-important-d-ecouter-la-planete-rouge_4308091.html"
    # twitter blockquote

    # Franceinfo (tv) livestream embedded (endend and shows replay now)
    # page_url = "sante/maladie/coronavirus/direct-covid-19-jean-castex-va-s-exprimer-a-18-heures-au-sujet-de-la-dizaine-de-departements-juges-preoccupants_4310813.html"

    # page_url = "sante/maladie/coronavirus/carte-covid-19-decouvrez-les-20-departements-places-en-surveillance-renforcee_4310887.html"
    # iframe

    # page_url = "sante/maladie/coronavirus/infographies-covid-19-cinq-graphiques-pour-comprendre-la-situation-epidemique-en-france_4310757.html"
    # infographies

    # page_url = "sante/maladie/coronavirus/vaccin/video-covid-19-les-plus-de-65-ans-pourront-se-faire-vacciner-a-partir-de-debut-avril-assure-jean-castex_4310939.html"
    # multiple videos in json

    # page_url = "sante/maladie/coronavirus/covid-19-le-passeport-vaccinal-evoque-par-la-commission-europeenne-est-il-juridiquement-possible_4317149.html"
    # The Conversation pixel tracking

    # page_url = "sante/maladie/coronavirus/confinement/dedans-avec-les-miens-dehors-en-citoyen-la-campagne-de-communication-du-gouvernement-sur-les-gestes-barrieres-devoilee-par-jean-castex_4343313.html"
    # ul

    page_url = "monde/afrique/afrique-du-sud/afrique-du-sud-pour-ne-plus-etre-des-cibles-les-femmes-prennent-les-armes_4354289.html"
    # slideshow

    page = get_article(page_url)

    print(page)
