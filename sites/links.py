from . import gameinformer
from . import makeuseof
# from . import androidauthority
from . import heise
from . import theverge
# from . import itsfoss
from . import decentralizetoday
# from . import nypost
from . import theguardian
from . import shacknews
# from . import androidpolice
# from . import lefigaro
from . import franceinfo
from . import developpez
# from . import mediapart

from . import aljazeeranet

sites = {
    "gaming": {
        shacknews.identifier: shacknews,
        gameinformer.identifier: gameinformer,
    },
    "tech": {
        makeuseof.identifier: makeuseof,
        heise.identifier: heise,
        theverge.identifier: theverge,
        decentralizetoday.identifier: decentralizetoday,
        developpez.identifier: developpez,
    },
    "news": {
        theguardian.identifier: theguardian,
        aljazeeranet.identifier: aljazeeranet,
        franceinfo.identifier: franceinfo,
    }
    # "androidauthority.com": androidauthority,
    # "www.androidauthority.com": androidauthority,

    # "www.androidpolice.com": androidpolice,
    # "androidpolice.com": androidpolice,

    # "itsfoss.com": itsfoss,
    # "www.itsfoss.com": itsfoss,

    # "nypost.com": nypost,
    # "www.nypost.com": nypost,

    # "lefigaro.fr": lefigaro,
    # "www.lefigaro.fr": lefigaro,

    # "www.mediapart.fr": mediapart,
    # "mediapart.fr": mediapart
}

sites_list = {}
for site_type in sites.keys():
    for site in sites[site_type].keys():
        sites_list[site] = (sites[site_type][site])

sites_type_map = {}
for site_type in sites.keys():
    for site in sites[site_type].keys():
        sites_type_map[site] = site_type
