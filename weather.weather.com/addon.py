## The Weather Channel (weather.com)

import sys
import xbmcaddon

ADDON_ID = "weather.weather.com"


if (__name__ == "__main__"):

    # Addon class
    Addon = xbmcaddon.Addon(id=ADDON_ID)

    # text viewer
    if (sys.argv[1].startswith("viewer=")):
        import resources.lib.viewer as viewer
        viewer.Viewer(addon=Addon, function=sys.argv[1].split("=")[1])
    # utilities
    elif (sys.argv[1].startswith("util=")):
        import resources.lib.utils as utils
        utils.Utilities(addon=Addon, function=sys.argv[1].split("=")[1])
    # search for new town
    elif (sys.argv[1].startswith("search=")):
        import resources.lib.search as search
        search.TownSearch(addon=Addon, index=sys.argv[1].split("=")[1]).get_town()
    # fetch weather
    else:
        import resources.lib.weather as weather
        weather.Weather(addon=Addon, index=sys.argv[1]).fetch_weather()#, refresh=sys.argv[2]
