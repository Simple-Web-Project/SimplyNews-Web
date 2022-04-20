from quart import Quart, render_template
from simplynews_sites.links import sites
from requests import HTTPError
import traceback
import config
import datetime
import json
import os


def get_sites(sites_type):
    actual_sites = {}
    for link in sites[sites_type].keys():
        site = sites[sites_type][link]
        if site.identifier in actual_sites:
            continue
        actual_sites[site.identifier] = {
            "link": sites_type + '/' + link,
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

os.makedirs(
    os.path.expanduser(cfg["settings"]["cachePath"]),
    exist_ok=True,
)

app = Quart(__name__)


@app.route("/")
async def main():
    return await render_template("index.html", sites=get_sites('news'), type="news")


@app.route("/<string:sites_type>/")
async def sites_types(sites_type):
    print('Hello sites_types!')
    return await render_template("index.html", sites=get_sites(sites_type), type=sites_type)


@app.route("/<string:sites_type>/<string:site>/")
async def site_main(sites_type, site):
    print('Hello site_main!')
    if site not in sites[sites_type]:
        return await render_template("site/not_found.html")

    ident = sites[sites_type][site].identifier
    # cache_file_path = os.path.join(
    #     os.path.expanduser(cfg["settings"]["cachePath"]),
    #     f"{ident}.json",
    # )
    recent_articles = None

    # if os.path.exists(cache_file_path):
    #     try:
    #         with open(cache_file_path, "r") as cache_file:
    #             recent_articles_cached = json.loads(cache_file.read())

    #         last_updated = recent_articles_cached["last_updated"]
    #         date_time = datetime.datetime.strptime(
    #             last_updated, "%Y-%m-%d %H:%M:%S.%f")
    #         if (datetime.datetime.now() - date_time) > sites[
    #             site
    #         ].cache_refresh_time_delta:
    #             recent_articles = None
    #         else:
    #             recent_articles = recent_articles_cached["recent_articles"]

    #     except Exception as e:
    #         print(f"Error loading cache for '{ident}':")
    #         print(str(e))

    if recent_articles is None:
        recent_articles = sites[sites_type][site].get_recent_articles()

        # cache_content = {
        #     "last_updated": str(datetime.datetime.now()),
        #     "recent_articles": recent_articles,
        # }
        # with open(cache_file_path, "w") as cache_file:
        #     cache_file.write(json.dumps(cache_content))
    return await render_template(
        "site/index.html", site=sites[sites_type][site], recent_articles=recent_articles, type=sites_type
    )


@app.route("/<string:sites_type>/<string:site>/<path:path>")
async def handle_page_url(sites_type, site, path):
    if site in sites[sites_type]:
        try:
            site_module = sites[sites_type][site]
            page = site_module.get_page(path)

        except HTTPError as e:
            response = e.response
            sitename = site_module.site_title

            if response.status_code == 404:
                return await render_template(
                    "site/not_found.html",
                    original_link=response.url,
                    site_link=f"/{site}",
                    sitename=sitename
                ), 404
            else:
                return await render_template(
                    "site/page_httperror.html",
                    reason=response.reason,
                    status_code=response.status_code,
                    original_link=response.url,
                    site_link=f"/{site}",
                    sitename=sitename,
                ), response.status_code
        except Exception as e:
            stacktrace = traceback.format_exc()
            sitename = site_module.site_title
            return await render_template(
                "site/page_exception.html",
                reason=str(e.args[0]),
                stacktrace=stacktrace,
                original_link=f"https://{site}/{path}",
                site_link=f"/{site}",
                sitename=sitename,
            ), 500

        if page == None:
            return await render_template("site/page_error.html"), 500
        else:
            return await render_template(
                "site/page.html",
                original_link=f"https://{site}/{path}",
                sitename=site,
                site=sites[sites_type][site],
                page=page,
                type=sites_type
            )
    else:
        return await render_template("site/not_found.html"), 404


if __name__ == "__main__":
    app.run()
