import configparser
import os

def parse_config():
    cfg = configparser.ConfigParser()
    cfg["settings"] = {
        "cachePath": "./cache",
    }

    for f in ["/etc/simple-web/simplynews.ini", "config.ini"]:
        if os.path.exists(f):
            cfg.read(f)
            break

    return cfg
