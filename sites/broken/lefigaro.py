from .helpers import rss, utils
from datetime import timedelta, datetime
from bs4 import BeautifulSoup
import requests
import json
import bs4

cache_refresh_time_delta = timedelta(hours=3)
identifier = "lefigaro"
site_title = "Le Figaro"

base_url = "https://www.lefigaro.fr"
rss_feed = f"{base_url}/rss/figaro_actualites.xml"


def get_image(img):

    data_srcset = img.get("data-srcset")
    if data_srcset is not None:
        src = data_srcset.split()[0]
    else:
        src = img["src"]

    return {
        "type": "image",
        "src": src,
        "alt": img.get("alt")
    }


def get_article(url):
    response = requests.get(f"{base_url}/{url}")
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    title = soup.select_one("title").text
    subtitle = soup.select_one("meta[name=description]")["content"]

    post = soup.select_one("article")

    json_element = soup.find("script", type="application/ld+json")
    if json_element is not None:
        info_json = json.loads(json_element.next)

    if subtitle.endswith("..."):
        standfirst = post.select_one("p.fig-standfirst")
        if standfirst is not None:
            subtitle = standfirst.text

    for element in info_json:
        if element["@type"] == "NewsArticle":
            last_updated = element.get("dateModified")
            if last_updated is None:
                last_updated = element.get("datePublished")
            author_array = element.get("author")
            if author_array is not None:
                authors = []
                for author_obj in author_array:
                    authors.append(author_obj["name"])
                author = ", ".join(authors)
            else:
                author = "Unknown"

    last_updated_datetime = datetime.strptime(
        last_updated, "%Y-%m-%dT%H:%M:%S.%fZ")
    if last_updated_datetime is not None:
        last_updated = str(last_updated_datetime)

    data = {
        "title": title,
        "subtitle": subtitle,
        "author": author,
        "last_updated": last_updated
    }

    article = []

    heading_image = post.select_one(
        "article > figure.fig-media img") or soup.select_one("div.fig-wrapper figure.fig-media img")
    if heading_image is not None:
        article.append(get_image(heading_image))

    post_content = post.select_one("div.fig-content-body")

    if post_content is None:  # not a regular article
        poll_element = post.select_one("div.fig-poll")  # poll "article"
        if poll_element is not None:
            entries = []
            results = poll_element.select("div.fig-poll__result")
            for result in results:
                percentage = result.get("data-percentage")
                label = result.select_one("span.fig-poll__label").text

                entries.append({"value": "{} : {}%".format(label, percentage)})

            article.append({
                "type": "unsorted list",
                "entries": entries
            })

            votes = poll_element.get("data-voters")

            article.append({
                "type": "paragraph",
                "value": "{} votes".format(votes)
            })

            data["article"] = article
            return data

        live_messages = post.select("article.live-message")  # live "article"
        if live_messages is not None:
            for message in live_messages:
                message_title = message.select_one(".live-title")
                article.append({
                    "type": "header",
                    "size": "h2",
                    "value": message_title.text
                })
                date = message.select_one("time")
                if date is not None:
                    # date_time = datetime.fromisoformat(date["datetime"])
                    article.append({
                        "type": "paragraph",
                        "value": "Publié {}".format(date.text)
                    })

                message_body = message.select_one("div.live-article")
                for element in message_body:
                    el = get_element(element, True)
                    if el is not None and el != {}:
                        article.append(el)

        data["article"] = article
        return data

    for element in post_content:
        el = get_element(element)

        if el is not None and el != {}:
            article.append(el)

    data["article"] = article
    return data


def get_recent_articles():
    return rss.default_feed_parser(rss_feed)


def is_related_article(element):
    if element is None:
        return False

    text = element.text.lower()
    return text.startswith("à voir aussi") or "lire aussi -" in text or "lire notre article" in text


def get_element(element, is_live=False):
    el = {}

    if type(element) == bs4.element.NavigableString:
        el["type"] = "text"
        el["value"] = str(element)
        return el

    if element.name == "p":
        if is_live or (not is_live and utils.value_in_element_attr(element, "fig-paragraph")):
            strong = element.select_one("strong")
            if not is_related_article(strong) and not is_related_article(element):
                el["type"] = "paragraph"
                el["value"] = element.text.strip("\n").strip()
    elif element.name == "div" and utils.value_in_element_attr(element, "fig-premium-paywall"):
        # paywall. Display info (% left) without info encouraging to subscribe
        info = element.select_one("p.fig-premium-paywall__infos")
        if info is not None:
            el["type"] = "paragraph"
            el["value"] = info.text.strip("\n").strip()
    elif element.name == "figure":
        img = element.select_one("img")
        if img is not None:
            return get_image(img)
        blockquote = element.select_one("blockquote")
        if blockquote is not None:
            el["type"] = "blockquote"
            el["value"] = blockquote.text
            return el
        span = element.select_one("span")
        if span is not None and "data-html" in span.attrs:
            data_html = BeautifulSoup(span["data-html"], "lxml")
            iframe = data_html.select_one("iframe")
            if iframe is not None:
                el["type"] = "iframe"
                el["src"] = utils.fix_link(iframe["src"])
                el["width"] = iframe.get("width")
                el["height"] = iframe.get("height")
                return el

            img = data_html.select_one("img")
            if img is not None:
                el = get_image(img)

    elif element.name == "strong" and not is_related_article(element):
        el["type"] = "strong"
        el["value"] = element.text
    elif element.name == "em" or element.name == "i":
        el["type"] = "em"
        el["value"] = element.text
    elif element.name == "br":
        el["type"] = "linebreak"
    elif element.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
        el["type"] = "header"
        el["size"] = element.name
        el["value"] = element.text

    return el


if __name__ == "__main__":
    # page_url = "politique/menu-sans-viande-dans-les-cantines-de-lyon-darmanin-denonce-la-mesure-doucet-lui-repond-20210221"

    # page_url = "flash-actu/libye-le-ministre-de-l-interieur-echappe-a-une-tentative-d-assassinat-20210221"
    # not updated (yet)

    # page_url = "actualite-france/approuvez-vous-la-decision-du-maire-de-lyon-d-imposer-un-menu-sans-viande-dans-les-ecoles-20210221"
    # poll

    # page_url = "finances-perso/transmission-de-votre-patrimoine-immobilier-les-solutions-pour-alleger-la-facture-20210219"
    # paywall

    # page_url = "culture/les-mysteres-du-coffre-cache-depuis-le-xixe-siecle-dans-le-socle-d-une-statue-de-napoleon-a-rouen-20210221"
    # image, headers…

    # page_url = "vox/societe/didier-lemaire-a-trappes-nous-ne-sommes-plus-en-france-20210219"
    # subtitle cut

    # page_url = "sciences/en-direct-covid-19-les-alpes-maritimes-attendent-les-decisions-du-gouvernement-20210222"
    # "live" article

    page_url = "confinement-partiel-commerces-ce-qu-il-faut-retenir-des-mesures-de-restriction-dans-les-alpes-maritimes-20210222"
    # multiple authors

    page = get_article(page_url)
    print(page)
