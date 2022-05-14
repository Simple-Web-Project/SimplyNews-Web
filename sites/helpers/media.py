import requests
import hashlib
import re
from colorama import Fore, Back, Style


def save(url, path):
    data = requests.get(url).content
    file_format = re.search("\.([a-z0-9]{1,}$)", url)[1]
    media_hash = hashlib.md5(url.encode()).hexdigest()
    name = f"{media_hash}.{file_format}"

    with open(path+name, 'wb') as handler:
        handler.write(data)

    return name


if __name__ == "__main__":
    save('https://ajmn-aja-vod.akamaized.net/media/v1/pmp4/static/clear/665001584001/2485b9f5-238e-4364-9034-93be0e26e19c/baa44df9-d3a4-4a4c-9fd6-386b6f1b7a10/main.mp4', './')
