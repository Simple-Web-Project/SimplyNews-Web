from quart import Quart, render_template
from sites.links import *
from requests import HTTPError
import traceback
import json
import threading
from colorama import Fore, Back, Style

import utils.cache
import utils.config


def get_sites(sites_type):
    actual_sites = {}
    for link in sites[sites_type].keys():
        site = sites[sites_type][link]
        if site.identifier in actual_sites:
            continue
        actual_sites[site.identifier] = {
            "link": site.identifier,
            "name": site.site_title,
            "logo": site.site_logo if (hasattr(site, 'site_logo')) else '',
            "dir": site.site_dir if (hasattr(site, 'site_dir')) else 'ltr',
        }

    _actual_sites = []
    for k in actual_sites.keys():
        _actual_sites.append(actual_sites[k])
    return _actual_sites


app = Quart(__name__)


@app.route("/")
async def main():
    return await render_template("index.html", sites=get_sites('news'), type="news")


@app.route("/<string:var>")
async def sites_types(var):
    if var in sites.keys():
        sites_type = var
        return await render_template("index.html", sites=get_sites(sites_type), type=sites_type)

    elif var in sites_list.keys():
        hostname = var
        site_module = sites_list[hostname]
        recent_articles = utils.cache.get_recent_articles(site_module)
        if recent_articles:
            return await render_template(
                "site/recent_articles.html",
                site_module=site_module,
                recent_articles=recent_articles,
                type=sites_type_map[hostname]
            )
        return await render_template("site/wait.html"), 404

    return await render_template("site/not_found.html"), 404


@app.route("/<string:hostname>/<path:path>")
async def handle_page_url(hostname, path):
    if hostname in sites_list.keys():
        site_module = sites_list[hostname]
        article = utils.cache.get_article(site_module, path)
        if not article:
            print('article not found in cache, fetching it.')
            article = utils.cache.set_article(site_module, path)
        else:
            print('article found in cache')
        if article:
            return await render_template(
                "site/article.html",
                original_link=f"{site_module.base_url}/{path}",
                site_module=site_module,
                page=article,
                type=sites_type_map[hostname]
            )
    return await render_template("site/not_found.html"), 404

if __name__ == "__main__":

    r = threading.Thread(target=utils.cache.cache_interval)
    r.start()

    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )
