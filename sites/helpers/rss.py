import feedparser
import urllib
from colorama import Fore, Back, Style

def default_feed_parser(feed_link):
    feed = feedparser.parse(feed_link)
    feed_ = []
    for entry in feed["entries"]:
        url = urllib.parse.urlparse(entry["link"])
        
        local_link = url.path.strip("/")  # Kill annoying slashes

        feed_.append({
            "title": entry["title"],
            "link": local_link,
        })
    print(Fore.GREEN + 'Fetched ' + Style.RESET_ALL + f'/{urllib.parse.unquote(feed_link)}')
    return feed_
