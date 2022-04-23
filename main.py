from quart import Quart, render_template
from simplynews_sites.links import sites
from requests import HTTPError
import traceback
import config
import datetime
import json
import os
import threading
import time
from colorama import Fore, Back, Style
import datetime
from urllib.request import pathname2url, url2pathname
import uuid
import urllib


def get_sites(sites_type):
    actual_sites = {}
    for link in sites[sites_type].keys():
        site = sites[sites_type][link]
        if site.identifier in actual_sites:
            continue
        actual_sites[site.identifier] = {
            "link": sites_type + '/' + site.identifier,
            "name": site.site_title,
            "logo": site.site_logo if (hasattr(site, 'site_logo')) else '',
            "dir": site.site_dir if (hasattr(site, 'site_dir')) else 'ltr',
        }

    _actual_sites = []
    for k in actual_sites.keys():
        _actual_sites.append(actual_sites[k])
    return _actual_sites


# Configuration
cfg = config.parse_config()

cache_path = os.path.expanduser(cfg["settings"]["cachePath"])

os.makedirs(
    cache_path,
    exist_ok=True,
)
for sites_type in sites.keys():
    for site in sites[sites_type].keys():
        os.makedirs(
            f'{cache_path}/{sites_type}/{sites[sites_type][site].identifier}',
            exist_ok=True,
        )

app = Quart(__name__)


@app.route("/")
async def main():
    return await render_template("index.html", sites=get_sites('news'), type="news")


@app.route("/<string:sites_type>")
async def sites_types(sites_type):
    return await render_template("index.html", sites=get_sites(sites_type), type=sites_type)


@app.route("/<string:sites_type>/<string:site>")
async def site_main(sites_type, site):
    if site not in sites[sites_type]:
        return await render_template("site/not_found.html")

    recent_articles = get_recent_articles_from_cache(sites_type, site)
    if recent_articles:
        return await render_template(
            "site/index.html",
            site=sites[sites_type][site],
            recent_articles=recent_articles,
            type=sites_type
        )
    return await render_template("site/wait.html", site=site)


@app.route("/<string:sites_type>/<string:site>/<path:path>")
async def handle_page_url(sites_type, site, path):
    if site in sites[sites_type]:
        site_module = sites[sites_type][site]
        page = get_page_from_cache(sites_type, site, path)
        if page:
            return await render_template(
                "site/page.html",
                original_link=f"{site_module.base_url}/{path}",
                sitename=site,
                site=sites[sites_type][site],
                page=page,
                type=sites_type
            )
    return await render_template("site/not_found.html"), 404


def write_site_main_cache(sites_type, site):
    recent_articles = sites[sites_type][site].get_recent_articles()
    for article in recent_articles:
        article['id'] = uuid.uuid1().int
    cache_file_path = os.path.join(
        cache_path,
        f"{sites_type}/{sites[sites_type][site].identifier}/recent_articles.json",
    )
    with open(cache_file_path, "w") as cache_file:
        cache_file.write(json.dumps(recent_articles))
    return recent_articles


def get_page_from_cache(sites_type, site, path):
    local_link = urllib.parse.quote(path).lower()
    for item in get_recent_articles_from_cache(sites_type, site):
        if item['link'] == local_link:
            file_name = item['id']
            cache_file_path = os.path.join(
                cache_path,
                f"{sites_type}/{sites[sites_type][site].identifier}/{file_name}.json",
            )
            if os.path.exists(cache_file_path):
                with open(cache_file_path, "r") as cache_file:
                    page = json.loads(cache_file.read())
                    return page


def get_site_articles_content(sites_type, site):
    recent_articles = write_site_main_cache(sites_type, site)
    for article in recent_articles:
        handle_page_url_cache(sites_type, site, article['link'])


def get_recent_articles_from_cache(sites_type, site):
    cache_file_path = os.path.join(
        cache_path,
        f"{sites_type}/{sites[sites_type][site].identifier}/recent_articles.json",
    )
    if os.path.exists(cache_file_path):
        with open(cache_file_path, "r") as cache_file:
            recent_articles = json.loads(cache_file.read())
            return recent_articles


def handle_page_url_cache(sites_type, site, path):
    for item in get_recent_articles_from_cache(sites_type, site):
        if item['link'] == path:
            file_name = item['id']
            cache_file_path = os.path.join(
                cache_path,
                f"{sites_type}/{sites[sites_type][site].identifier}/{file_name}.json",
            )
            with open(cache_file_path, "w") as cache_file:
                site_module = sites[sites_type][site]
                page = site_module.get_page(item['link'])
                cache_file.write(json.dumps(page))
                return page


def write_site_main_cache_interval():
    while True:
        time_a = datetime.datetime.now().replace(microsecond=0)

        threads = []
        for sites_type in sites.keys():
            for site in sites[sites_type].keys():
                threads.append(
                    threading.Thread(
                        target=get_site_articles_content,
                        args=(sites_type, site)
                    )
                )

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        time_b = datetime.datetime.now().replace(microsecond=0)
        print(
            Fore.BLUE + f'Finished fetching cache. It took: {(time_b-time_a).total_seconds()}s' + Style.RESET_ALL)

        time_interval = int(cfg["settings"]["timeInterval"]) * 60
        time.sleep(time_interval)


if __name__ == "__main__":

    r = threading.Thread(target=write_site_main_cache_interval)
    r.start()
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )
