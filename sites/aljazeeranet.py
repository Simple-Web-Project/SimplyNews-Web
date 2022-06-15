from bs4 import BeautifulSoup
import requests
import json
from datetime import timedelta
import urllib
import feedparser
import re
# import sites.helpers.media as media

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from colorama import Fore, Back, Style

identifier = "aljazeera.net"
cache_refresh_time_delta = timedelta(hours=12)
base_url = "https://www.aljazeera.net"

site_title = "الجزيرة نت"
site_logo = "aljazeera.webp"
site_dir = "rtl"

rss_feed = f"{base_url}/aljazeerarss/a7c186be-1baa-4bd4-9d80-a84db769f779/73d0e1b4-532f-45ef-b135-bfdff8b8cab9"

options = Options()
options.headless = True
options.binary_location = './drivers/ungoogled-chromium_101.0.4951.41-1.1_linux/chrome'
options.add_argument(
    'user-agent="Mozilla/5.0 (Android 4.4.4; Tablet; rv:68.0) Gecko/68.0 Firefox/68.0"')
service = Service('./drivers/chromedriver')

# https://www.aljazeera.net/aljazeerarss/a7c186be-1baa-4bd4-9d80-a84db769f779/73d0e1b4-532f-45ef-b135-bfdff8b8cab9


def get_article(url):
    print(
        Fore.GREEN + 'Fetching ' + Style.RESET_ALL +
        f"{base_url}/{urllib.parse.unquote(url)}"
    )
    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(f"{base_url}/{url}")
    except:
        print('aljazeera.net: Error in driver')
        return

    # Header title
    title = None
    for e in driver.find_elements(By.XPATH, '//header[@class="article-header"]/h1'):
        title = e.text
        break

    source = None
    for e in driver.find_elements(By.CLASS_NAME, 'article-source'):
        source = e.text
        break

    published = None
    for e in driver.find_elements(By.CLASS_NAME, 'article-dates__published'):
        published = e.text
        break

    article = []
    # Header Video
    for video in driver.find_elements(By.XPATH, '//figure[@class="article-featured-video"]//video'):
        # proxied_src = media.save(video.get_attribute("src"), cache_path)
        article.append({
            "type": "video",
            "src": video.get_attribute("src"),
        })
        break

    # Header image
    for image in driver.find_elements(By.XPATH, '//figure[@class="article-featured-image"]//img'):
        article.append({
            'type': 'image',
            'src': image.get_attribute('src'),
            'alt': image.get_attribute('alt')
        })
        break

    # Small summary body
    _article_excerpt = driver.find_elements(
        By.CLASS_NAME, 'article-excerpt')
    if len(_article_excerpt) > 0 and _article_excerpt[0].text.strip() != '':
        article.append({
            "type": "paragraph",
            "value": _article_excerpt[0].text
        })

    for element in driver.find_elements(By.XPATH, '//div[contains(@class, "wysiwyg")]/*'):
        if element.tag_name == "p" and len(element.find_elements(By.TAG_NAME, 'img')) > 0:
            for image in element.find_elements(By.TAG_NAME, 'img'):
                article.append({
                    'type': 'image',
                    'src': base_url + image.get_attribute('src'),
                    'alt': image.get_attribute('alt')
                })
                break

        elif element.tag_name == 'figure':
            for image in element.find_elements(By.TAG_NAME, 'img'):
                article.append({
                    'type': 'image',
                    'src': image.get_attribute('src'),
                    'alt': image.get_attribute('alt')
                })
                break
            for video in element.find_elements(By.CLASS_NAME, 'vjs-tech'):
                article.append({
                    'type': 'video',
                    "src": video.get_attribute("src"),
                })
                break

        elif element.tag_name == "p":
            if len(element.find_elements(By.TAG_NAME, 'a')) > 0:
                myList = re.findall(
                    r"(?:(.*)<a.*href=\"(.*)\">(.*)<\/a>(.*)){1,}",
                    element.get_attribute('innerHTML')
                )
                children = []
                for i in range(0, len(myList[0])):
                    if i % 3 == 0:
                        children.append({
                            "type": "paragraph",
                            "value": myList[0][i]
                        })
                    elif i % 3 == 1:
                        children.append({
                            "type": "link",
                            "href": myList[0][i],
                            "value": myList[0][i+1],
                        })
                article.append({
                    "type": "paragraph_advanced",
                    "children": children
                })
            else:
                article.append({
                    "type": "paragraph",
                    "value": element.text,
                })

        elif element.tag_name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            article.append({
                "type": "header",
                "size": element.tag_name,
                "value": element.text
            })

        elif element.tag_name == 'div' and 'twitter-tweet' in element.get_attribute("class").split():
            article.append({
                "type": "iframe",
                "src":  element.find_element(By.TAG_NAME, 'iframe').get_attribute('src').replace('platform.twitter.com', 'nitter.pussthecat.org'),
                "width": 500,
                "height": 500
            })

        elif element.tag_name == 'div' and 'jetpack-video-wrapper' in element.get_attribute("class").split():
            article.append({
                "type": "iframe",
                "src":  element.find_element(By.TAG_NAME, 'iframe').get_attribute('src'),
                "width": 770,
                "height": 434,
            })

        elif element.tag_name == 'blockquote':
            article.append({
                "type": "blockquote",
                "value":  element.text,
            })
        break

    data = {
        "title": title,
        "author": source,
        "last_updated": published,
        "article": article
    }
    driver.quit()
    return data


def get_recent_articles():
    webpage = requests.get(
        'https://news.google.com/publications/CAAqBwgKMI25oAkwsKpw?hl=ar&gl=AE&ceid=AE%3Aar')
    soup = BeautifulSoup(webpage.content, "html.parser")
    myList = []
    for element in soup.find_all('div', class_='NiLAwe'):

        title = element.find('h3')
        if title:
            title = title.text

        image = element.find('img')
        if image:
            image = image['src']

        date = element.find('div', class_='SVJrMe')
        if date:
            date = date.text

        link = element.find('a')
        if link:
            redirect = requests.get(
                'https://news.google.com' + link['href'][1:])
            link = urllib.parse.urlparse(redirect.url).path.strip("/")

        myList.append({
            'title': title,
            'image': image,
            'date': date,
            'link': link
        })
    return myList


if __name__ == "__main__":
    # page = get_recent_articles()
    # page_url = "news/2022/4/23/بلينكن-بكييف-الأحد-زيلينسكي-يدعو"
    # page_url = "news/2022/4/23/%D8%A8%D9%84%D9%8A%D9%86%D9%83%D9%86-%D8%A8%D9%83%D9%8A%D9%8A%D9%81-%D8%A7%D9%84%D8%A3%D8%AD%D8%AF-%D8%B2%D9%8A%D9%84%D9%8A%D9%86%D8%B3%D9%83%D9%8A-%D9%8A%D8%AF%D8%B9%D9%88"
    # https://www.aljazeera.net/news/2022/4/23/%D8%A8%D9%84%D9%8A%D9%86%D9%83%D9%86-%D8%A8%D9%83%D9%8A%D9%8A%D9%81-%D8%A7%D9%84%D8%A3%D8%AD%D8%AF-%D8%B2%D9%8A%D9%84%D9%8A%D9%86%D8%B3%D9%83%D9%8A-%D9%8A%D8%AF%D8%B9%D9%88
    # page = json.dumps(get_article(page_url), ensure_ascii=False, indent=2)
    page = json.dumps(get_recent_articles(), ensure_ascii=False, indent=4)
    with open('result.json', "w") as cache_file:
        cache_file.write(page)
