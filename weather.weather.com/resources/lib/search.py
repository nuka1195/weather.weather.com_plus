## Utility to search weather.com for town codes

from constants import *
import os
import re
import urllib2
import xbmc
import xbmcgui


class InvalidTown(Exception):
    pass


class TownSearch:
    """
        Searches for a town from weather.com and
        sets the weather.com town code in settings.
    """
    # set regex's
    regex_geo = re.compile("Your IP Address: <strong>(.+?)</strong><br />\s.+?Located near: <strong>(.+?)</strong>", re.IGNORECASE)
    regex_town = re.compile("<dnam>([^<]+)</dnam>")
    regex_location_list = re.compile("<loc.+?id=\"([^\"]+)\".+?type=\"([^\"]+)\">([^<]+)</loc>")

    def __init__(self, addon, index):
        # set our Addon class
        self.Addon = addon
        # setting index id
        self.index = index

    def get_geo_location(self):
        try:
            # fetch location source
            source = self._fetch_source()
            # get location name
            result = self.regex_geo.search(source).groups(1)
            # if IP has not changed return old values
            if (result[0] == self.Addon.getSetting("LocationGeoIP")):
                return self.Addon.getSetting("LocationGeoId"), result[0]
            # get new town
            town = self.get_town(text=result[1])
            # raise error if None so we use fallback?
            if (town is None):
                raise Exception
        except:
            # use our fallback for any errors
            return self.Addon.getSetting("LocationGeoFallbackId"), ""#self.Addon.getSetting("LocationGeoFallback")
        else:
            # set new IP
            self.Addon.setSetting("LocationGeoIP", result[0])

            return town[1], result[0]

    def get_town(self, text=None):
        # get search text
        if (text is None):
            text = self._get_search_text(heading=self.Addon.getLocalizedString(30901))
            # skip if user cancels keyboard
            if (text is None): return
        try:
            town = None
            # fetch source
            source = self._fetch_source(text)
            # select town
            town = self._select_town(source, text.upper())
            # raise an error if no results were found
            if (town is None and self.index == "Geo"):
                raise InvalidTown
        except urllib2.URLError:
            # inform user for non IP based GEO location searches only, IP based GEO searches have a fallback
            if (self.index != "GeoFallback"):
                ok = xbmcgui.Dialog().ok(self.Addon.getLocalizedString(30000), self.Addon.getLocalizedString(30910))
        except InvalidTown:
            #FIXME: What do we want to return
            # put msg up about none found if it wasn't a cancelled keyboard
            pass
        else:
            # only set if user selected a town
            if (town is not None):
                self.Addon.setSetting("Location{index}".format(index=self.index), town[0])
                self.Addon.setSetting("Location{index}Id".format(index=self.index), town[1])

        return town

    def _get_search_text(self, default="", heading="", hidden=False):
        """ shows a keyboard and returns a value """
        # show keyboard for input
        keyboard = xbmc.Keyboard(default, heading, hidden)
        keyboard.doModal()
        # return user input unless canceled
        if (keyboard.isConfirmed() and keyboard.getText() != ""):
            return keyboard.getText()
        # user cancelled or entered blank
        return None

    def _fetch_source(self, text=None):
        # return text if IP based GEO location
        if (text == "*"): return text
        # IP based GEO location search
        if (text is None):
            url = BASE_URLS["geo"]
        # check for a valid weather.com code and set appropriate url
        elif (len(text) == 8 and text[: 4].isalpha() and text[4 :].isdigit()):
            # valid id's are uppercase
            url = BASE_URLS["weather"].format(id=text.upper(), partnerid=PARTNER_ID, partnerkey=PARTNER_KEY,)
        else:
            # search
            url = BASE_URLS["search"].format(town=text.replace(" ", "+"),)
        # request base url
        request = urllib2.Request(url, headers=HEADERS)
        # get response
        response = urllib2.urlopen(request)
        # read source
        source = unicode(response.read(), "UTF-8")

        return source

    def _select_town(self, source, text):
        # return if IP based GEO location
        if (text == "*"): return source, text
        # parse for a town name if valid weather.com id was entered
        if (len(text) == 8 and text[: 4].isalpha() and text[4 :].isdigit()):
            # parse town name and add id
            town = [self.regex_town.search(source).group(1), text]
            # set base path for source
            path = os.path.join(xbmc.translatePath(self.Addon.getAddonInfo("Profile")).decode("UTF-8"), u"source", u"weather-{id}.xml".format(id=text))
            # cache source
            cache_source(path, source)
        else:
            # parse town list
            towns = dict([[town, [town, id, type]] for id, type, town in self.regex_location_list.findall(source)])
            # inform user if no list found
            if (not towns):
                return None
            # set titles for select dialog
            titles = towns.keys()
            # if only one result return it
            if (len(titles) == 1):
                choice = 0
            else:
                # initialize to blank in case no selection
                town = ""
                # sort titles (dict() scrambles them)
                titles.sort()
                # get user selection
                choice = xbmcgui.Dialog().select(self.Addon.getLocalizedString(30900), titles)
            # set town
            if (choice >= 0):
                town = towns[titles[choice]]

        return town
