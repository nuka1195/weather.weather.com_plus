## Shared constants among modules

import os
import xbmc

# weather.com partner id
PARTNER_ID = "1004124588"
# weather.com partner key
PARTNER_KEY = "079f24145f208494"
# base urls
BASE_URLS = {
    "geo": "http://www.dnsstuff.com/tools/ipall/",
    "weather": "http://xoap.weather.com/weather/local/{id}?cc=*&dayf=5&link=xoap&prod=xoap&unit=s&par={partnerid}&key={partnerkey}",
    "search": "http://xoap.weather.com/search/search?where={town}"
}
# set headers
HEADERS = {
    "User-Agent": "XBMC/{version}".format(version=xbmc.getInfoLabel("System.BuildVersion")),
    "Accept": "application/xml; charset=UTF-8"
}

def cache_source(path, source):
    # create dir if it doesn't exist
    if (not os.path.isdir(os.path.dirname(path))):
        os.makedirs(os.path.dirname(path))
    # save source
    open(path, "w").write(source.encode("UTF-8", "replace"))
