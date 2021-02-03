from quart import Quart, render_template
from simplynews_sites.links import sites
import config
import datetime
import json
import os

actual_sites = {}
for link in sites.keys():
    site = sites[link]
    if site.identifier in actual_sites:
        continue
    actual_sites[site.identifier] = {"link": link, "name": site.site_title}

_actual_sites = []
for key in sorted(actual_sites.keys()):
    _actual_sites.append(actual_sites[key])
actual_sites = _actual_sites

# Configuration
cfg = config.parse_config()

os.makedirs(
    os.path.expanduser(cfg["settings"]["cachePath"]),
    exist_ok=True,
)

app = Quart(__name__)


@app.route("/")
async def main():
    return await render_template("index.html", sites=actual_sites)


@app.route("/<string:site>/")
async def site_main(site):
    if site not in sites:
        return await render_template("site/not_found.html")

    ident = sites[site].identifier
    cache_file_path = os.path.join(
        os.path.expanduser(cfg["settings"]["cachePath"]),
        f"{ident}.json",
    )
    recent_articles = None

    if os.path.exists(cache_file_path):
        try:
            with open(cache_file_path, "r") as cache_file:
                recent_articles_cached = json.loads(cache_file.read())

            last_updated = recent_articles_cached["last_updated"]
            date_time = datetime.datetime.strptime(last_updated, "%Y-%m-%d %H:%M:%S.%f")
            if (datetime.datetime.now() - date_time) > sites[
                site
            ].cache_refresh_time_delta:
                recent_articles = None
            else:
                recent_articles = recent_articles_cached["recent_articles"]

        except Exception as e:
            print(f"Error loading cache for '{ident}':")
            print(str(e))

    if recent_articles is None:
        recent_articles = sites[site].get_recent_articles()
        cache_content = {
            "last_updated": str(datetime.datetime.now()),
            "recent_articles": recent_articles,
        }
        with open(cache_file_path, "w") as cache_file:
            cache_file.write(json.dumps(cache_content))

    return await render_template(
        "site/index.html", site=sites[site], recent_articles=recent_articles
    )


@app.route("/<string:site>/<path:path>")
async def handle_page_url(site, path):
    if site in sites:
        page = sites[site].get_page(path)
        if page == None:
            return await render_template("site/page_error.html")
        else:
            return await render_template(
                "site/page.html",
                original_link=f"https://{site}/{path}",
                sitename=site,
                site=sites[site],
                page=page,
            )
    else:
        return await render_template("site/not_found.html")


if __name__ == "__main__":
    app.run()
