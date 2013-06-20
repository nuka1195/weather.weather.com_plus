## Main module for fetching and parsing weather info and setting window properties
# -*- coding: UTF-8 -*-

from constants import *
from properties import Properties
import os
import re
import time
import urllib2
import xbmc
from xbmcgui import Window

class Weather:
    """
        Fetches weather info from weather.com and
        sets window properties for skinners to use.
    """
    # weather window for setting weather properties
    WINDOW = Window(12600)
    # set refresh time in minutes
    REFRESH_TIME = 25

    def __init__(self, addon, index, refresh=False):
        # set our Addon class
        self.Addon = addon
        # get weather.com code, used to fetch proper weather info
        self.location_id = self.Addon.getSetting("Location{index}Id".format(index=index))
        # is this an IP based GEO location
        geolocation = (self.location_id == "*")
        # set our properties class
        self.properties = Properties(addon=self.Addon, window=self.WINDOW, geolocation=geolocation, locationId=self.location_id)
        # if IP based GEO location, fetch location
        if (geolocation):
            self._get_geo_location_id()
        # set force refresh
        self.refresh = refresh
        # set base path for source
        self.base_path = os.path.join(xbmc.translatePath(self.Addon.getAddonInfo("Profile")).decode("UTF-8"), u"source", u"weather-{id}.xml".format(id=self.location_id))
        # set status property to false to signify fetching...
        self.properties.set_status_properties(msg="false")

    def _get_geo_location_id(self):
        # FIXME: Remove if block and always search for mobile application (e.g. traveling) maybe have
        # a setting since every time you change locations it has to fetch IP, if not mobile leave if block.
        # get GEO location id (IP based GEO location-only once per session) for mobile based we need to always search if IP has changed
        if (self.WINDOW.getProperty("Location.IP")):
            print "USING EXISTING IP"
            self.location_id = self.Addon.getSetting("LocationGeoId")
        else:
            print "GETTING NEW IP"
            # search for town by IP
            from resources.lib import search
            self.location_id, ip = search.TownSearch(addon=self.Addon, index="Geo").get_geo_location()
            # set IP property and location ID
            self.properties.set_geo_ip(self.location_id, ip)

    def fetch_weather(self):
        # get the source files date if it exists
        try:
            date = time.mktime(time.gmtime(os.path.getmtime(self.base_path)))
        except:
            date = 0
        # set default expiration date
        expires = date + (self.REFRESH_TIME * 60)
        # see if necessary to refresh source
        refresh = ((time.mktime(time.gmtime())) > expires) or self.refresh
        try:
            print "RRRRRRRRRRRRRRRRRRRRRR"
            # do we need to fetch new source?
            if (refresh):
                print "YES"
                # request base url
                print BASE_URLS["weather"].format(id=self.location_id, partnerid=PARTNER_ID, partnerkey=PARTNER_KEY)
                request = urllib2.Request(BASE_URLS["weather"].format(id=self.location_id, partnerid=PARTNER_ID, partnerkey=PARTNER_KEY), headers=HEADERS)
                # get response
                response = urllib2.urlopen(request)
                # read source
                source = unicode(response.read(), "UTF-8")
                # if error raise error
                if (source.find("<error>") >= 0):
                    raise urllib2.URLError("Error fetching weather info!")
                # cache source
                cache_source(self.base_path, source)
            else:
                # open cached file
                source = unicode(open(self.base_path, "r").read(), "UTF-8")
        except urllib2.URLError as error:
            """
            # remove source
            if (os.path.isfile(self.base_path)):
                os.remove(self.base_path)
            """
            # set error message
            print error.reason
            msg = "error"
            # clear info
            info = self._clear_info()
        else:
            # set success message
            msg = "true"
            # parse info
            info = self._parse_source(source)
            # set properties
            self.properties.set_properties(info)
        # set status property
        self.properties.set_status_properties(msg=msg)
        # return message for other weather addons
        return msg

    def _parse_source(self, source):
        # regex's
        regex_location = re.compile("<loc.+?id=\"([^\"]+)\">.+?<dnam>([^<]+)</dnam>.+?<tm>([^<]+)</tm>.+?<lat>([^<]+)</lat>.+?<lon>([^<]+)</lon>.+?<sunr>([^<]+)</sunr>.+?<suns>([^<]+)</suns>.+?<zone>([^<]+)</zone>.+?</loc>", re.DOTALL + re.IGNORECASE)
        regex_current = re.compile("<cc>.+?<lsup>([^<]+)</lsup>.+?<obst>([^<]+)</obst>.+?<tmp>([^<]+)</tmp>.+?<flik>([^<]+)</flik>.+?<t>([^<]+)</t>.+?<icon>([^<]+)</icon>.+?<bar>.+?<r>([^<]+)</r>.+?<d>([^<]+)</d>.+?</bar>.+?<wind>.+?<s>([^<]+)</s>.+?<gust>([^<]+)</gust>.+?<d>([^<]+)</d>.+?<t>([^<]+)</t>.+?</wind>.+?<hmid>([^<]+)</hmid>.+?<vis>([^<]+)</vis>.+?<uv>.+?<i>([^<]+)</i>.+?<t>([^<]+)</t>.+?</uv>.+?<dewp>([^<]+)</dewp>.+?<moon>.+?<icon>([^<]+)</icon>.+?<t>([^<]+)</t>.+?</moon>.+?</cc>", re.DOTALL + re.IGNORECASE)
        regex_days_updated = re.compile("<dayf>.+?<lsup>([^<]+)</lsup>", re.DOTALL + re.IGNORECASE)
        regex_days = re.compile("<day.+?d=\"([^\"]+)\".+?t=\"([^\"]+)\".+?dt=\"([^\"]+)\">.+?<hi>([^<]+)</hi>.+?<low>([^<]+)</low>.+?<sunr>([^<]+)</sunr>.+?<suns>([^<]+)</suns>.+?<part.+?p=\"d\">.+?<icon>([^<]+)</icon>.+?<t>([^<]+)</t>.+?<wind>.+?<s>([^<]+)</s>.+?<gust>([^<]+)</gust>.+?<d>([^<]+)</d>.+?<t>([^<]+)</t>.+?</wind>.+?<bt>([^<]+)</bt>.+?<ppcp>([^<]+)</ppcp>.+?<hmid>([^<]+)</hmid>.+?</part>.+?<part.+?p=\"n\">.+?<icon>([^<]+)</icon>.+?<t>([^<]+)</t>.+?<wind>.+?<s>([^<]+)</s>.+?<gust>([^<]+)</gust>.+?<d>([^<]+)</d>.+?<t>([^<]+)</t>.+?</wind>.+?<bt>([^<]+)</bt>.+?<ppcp>([^<]+)</ppcp>.+?<hmid>([^<]+)</hmid>.+?</part>.+?</day>", re.DOTALL + re.IGNORECASE)
        # parse info
        location = regex_location.search(source).groups()
        cc = regex_current.search(source).groups()
        days_updated = regex_days_updated.search(source).group(1)
        days = regex_days.findall(source)
        # return results
        return {"location": location, "cc": cc, "days_updated": days_updated, "days": days}

    def _clear_info(self):
        # set dummy info (all blanks)
        return {
            "location": [""] * 8,
            "cc": [""] * 19,
            "days_updated": "",
            "days": [[count] + [""] * 24 for count in range(5)]
        }
