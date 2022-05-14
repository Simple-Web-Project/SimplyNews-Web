import bs4


def value_in_element_attr(element, value, attr: str = "class"):
    if not type(element) == bs4.element.Tag:
        return False
    else:
        attrs = element.attrs
        if attrs is not None and attrs != {}:
            return value in attrs.get(attr)
        else:
            return False


def fix_link(link, domain=None):
    if link.startswith("//"):
        return "https:{}".format(link)
    elif link.startswith("/") and domain:
        return "/{}{}".format(domain, link)
    else:
        return link


def get_property(element, attribute: str):
    """
    Safely get property
    """
    if element is None:
        return None
    else:
        return element.get(attribute)


def get_heading_image(soup: bs4.BeautifulSoup):
    heading_image = soup.find(
        "meta", property="og:image")
    if heading_image is not None:
        image_width = soup.find("meta", property="og:image:width")
        image_height = soup.find("meta", property="og:image:height")
        image_alt = soup.find("meta", property="og:image:alt")

        alt = get_property(image_alt, "content")
        if alt is None:
            alt = "heading image"

        return {
            "type": "image",
            "src": heading_image["content"],
            "alt": alt,
            "width": get_property(image_width, "content"),
            "height": get_property(image_height, "content")
        }
    else:
        return None


def get_subtitle(soup: bs4.BeautifulSoup):
    subtitle = soup.find("meta", property="description") or soup.find(
        "meta", property="og:description")
    if subtitle is None:
        return None
    else:
        return subtitle["content"]
