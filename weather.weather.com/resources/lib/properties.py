## Properties Module
# -*- coding: UTF-8 -*-

from localize import Localize
import os


class Properties:
    """
        Class used to set window properties
    """
    # $MSG[* Properties are set on the "Weather" window.]$END_MSG
    # $SUB_MSG[Use: "Window(Weather).Property(<property>)"]$END_SUB_MSG

    def __init__(self, *args, **kwargs):
        # set our Addon class
        self.Addon = kwargs["addon"]
        # set our window object
        self.WINDOW = kwargs["window"]
        # set our key variables
        self.geolocation = kwargs["geolocation"]
        self.location_id = kwargs["locationId"]
        # set localize functions
        self.Localize = Localize()
        # set title & logo
        self._set_addon_info()

    def _set_addon_info(self):
        # $BEGIN_GROUP[Addon Info]
        # Id of addon (useful for customized logo's)
        self.WINDOW.setProperty("Addon.Id", self.Addon.getAddonInfo("Id"))
        # Full path to addon's icon.png file
        self.WINDOW.setProperty("Addon.Logo", self.Addon.getAddonInfo("Icon"))
        # Name of addon
        self.WINDOW.setProperty("Addon.Name", self.Addon.getAddonInfo("Name"))
        # $END_GROUP

        # $BEGIN_GROUP[Weather Provider Info]
        # Weather provider's name
        self.WINDOW.setProperty("WeatherProvider", self.Addon.getAddonInfo("Name"))
        # Full path to weather provider's logo file
        self.WINDOW.setProperty("WeatherProviderIcon", self.Addon.getAddonInfo("Icon"))
        # $END_GROUP

        # $BEGIN_GROUP[XBMC Internal]
        # Loop thru and set each location
        for count in range(1, int(self.Addon.getSetting("Locations")) + 1):
            # Available town selections ({count} = 1 thru 5)
            self.WINDOW.setProperty("Location{count}".format(count=count), self.Addon.getSetting("Location{count}".format(count=count)))
        # Total number of towns set
        self.WINDOW.setProperty("Locations", str(int(self.Addon.getSetting("Locations")) + 1))
        # $END_GROUP

    def set_status_properties(self, msg):
        # $BEGIN_GROUP[Status Messages]
        # Status message ('true'=successfully fetched weather, 'false'=currently fetching weather, 'error'=fetching weather failed)
        self.WINDOW.setProperty("Weather.IsFetched", msg)
        # $END_GROUP

    def set_geo_ip(self, id, ip):
        # TODO: maybe just remove this group
        # $BEGIN_GROUP[Addon Internal]
        # Current IP used for IP based GEO location to verify if location has changed
        self.WINDOW.setProperty("Location.IP", ip)
        # $END_GROUP
        self.location_id = id

    def set_properties(self, info):
        # $BEGIN_GROUP[Location Properties]
        # Last time weather.com updated current weather (e.g. 10/01/2010 10:00 AM EDT)
        self.WINDOW.setProperty("Updated", self.Localize.localize_unit(info["cc"][0], "datetime"))
        # Last time weather.com updated 5-day forecast (e.g. 10/01/2010 10:00 AM EDT)
        self.WINDOW.setProperty("Updated.5Day", self.Localize.localize_unit(info["days_updated"], "datetime"))
        # Town (e.g. New York, NY)
        self.WINDOW.setProperty("Location", "{geo}{location}".format(geo=["", "*"][self.geolocation], location=info["location"][1]))
        # Town's weather.com id (e.g. USNY0996)
        self.WINDOW.setProperty("Location.Id", self.location_id)
        """
        # Town's setting index (starts at 1)
        self.WINDOW.setProperty("Location.Index", sys.argv[1])
        """
        # Town's latitude (*see settings - e.g. N 40°42'36")
        self.WINDOW.setProperty("Location.Latitude", self.Localize.localize_unit(info["location"][3], "latitude", format=self.Addon.getSetting("coordinate_format")))
        # Town's longitude (*see settings - e.g. W 74°00'36")
        self.WINDOW.setProperty("Location.Longitude", self.Localize.localize_unit(info["location"][4], "longitude", format=self.Addon.getSetting("coordinate_format")))
        # Town's latitude and longitude (*see settings - e.g. N 40°42'36" W 74°00'36")
        self.WINDOW.setProperty("Location.Coordinates", u"{latitude} {longitude}".format(latitude=self.Localize.localize_unit(info["location"][3], "latitude", format=self.Addon.getSetting("coordinate_format")), longitude=self.Localize.localize_unit(info["location"][4], "longitude", format=self.Addon.getSetting("coordinate_format"))))
        # Town's local time when weather was fetched (e.g. 7:39 AM)
        self.WINDOW.setProperty("Location.Time", self.Localize.localize_unit(info["location"][2], "time"))
        # Observation Station (e.g. New York, NY)
        self.WINDOW.setProperty("Station", info["cc"][1])
        # $END_GROUP

        # $BEGIN_GROUP[Current Conditions]
        # Current condition description (e.g. Fair)
        self.WINDOW.setProperty("Current.Condition", " ".join([self.Localize.localize_text.get(word, word) for word in info["cc"][4].split(" ") if (word)]))
        # Current condition icon path (*see settings)
        self.WINDOW.setProperty("Current.ConditionIcon", os.path.join(self.Addon.getSetting("icon_path_weather"), info["cc"][5] + ".png"))
        # Current dew point (e.g. 46)
        self.WINDOW.setProperty("Current.DewPoint", self.Localize.localize_unit(info["cc"][16]))
        # Current condition icon code number (e.g. 34)
        self.WINDOW.setProperty("Current.FanartCode", info["cc"][5])
        # Current condition or location based fanart path (*see settings)
        self.WINDOW.setProperty("Current.FanartPath", ["", os.path.join(self.Addon.getSetting("fanart_path"), [info["cc"][5], self.location_id][int(self.Addon.getSetting("fanart_type"))])][self.Addon.getSetting("fanart_path") != ""])
        # Current feels like temperature (e.g. 62)
        self.WINDOW.setProperty("Current.FeelsLike", self.Localize.localize_unit(info["cc"][3]))
        # Current humidity (e.g. 49%)
        self.WINDOW.setProperty("Current.Humidity", "{value}%".format(value=info["cc"][12]))
        # Current moon phase description (e.g. New)
        self.WINDOW.setProperty("Current.Moon", " ".join([self.Localize.localize_text.get(word, word) for word in info["cc"][18].split(" ") if (word)]))
        # Current moon phase icon path (*see settings)
        self.WINDOW.setProperty("Current.MoonIcon", os.path.join(self.Addon.getSetting("icon_path_moon"), info["cc"][17] + ".png"))
        # Current barometric pressure (e.g. 30.25 in. ↑)
        self.WINDOW.setProperty("Current.Pressure", self.Localize.localize_unit(info["cc"][6], "pressure", status=info["cc"][7]))
        # Current sunrise (e.g. 7:39 AM)
        self.WINDOW.setProperty("Current.Sunrise", self.Localize.localize_unit(info["location"][5], "time"))
        # Current sunset (e.g. 7:02 PM)
        self.WINDOW.setProperty("Current.Sunset", self.Localize.localize_unit(info["location"][6], "time"))
        # Current temperature (e.g. 65)
        self.WINDOW.setProperty("Current.Temperature", self.Localize.localize_unit(info["cc"][2]))
        # Current UV index (e.g. 0 Low)
        self.WINDOW.setProperty("Current.UVIndex", ["{value} {description}".format(value=info["cc"][14], description=self.Localize.localize_text.get(info["cc"][15], info["cc"][15])), info["cc"][14]][info["cc"][14] == "N/A"])
        # Current visibility (e.g. 10.0 miles)
        self.WINDOW.setProperty("Current.Visibility", self.Localize.localize_unit(info["cc"][13], "distance"))
        # Current wind (e.g. From WNW at 10 mph)
        self.WINDOW.setProperty("Current.Wind", self.Localize.localize_unit(info["cc"][8], "wind", direction=info["cc"][11]))
        # Current wind (e.g. From the West Northwest at 10 mph)
        self.WINDOW.setProperty("Current.WindLong", self.Localize.localize_unit(info["cc"][8], "wind", direction=info["cc"][11], long=True))
        # Current wind direction in degrees (e.g. 300°)
        self.WINDOW.setProperty("Current.WindDegrees", "{value}°".format(value=info["cc"][10]))
        # Current wind direction (abbreviated) (e.g. WNW)
        self.WINDOW.setProperty("Current.WindDirection", self.Localize.localize_text_special.get(info["cc"][11], [info["cc"][11]])[0])
        # Current wind direction (e.g. West Northwest)
        self.WINDOW.setProperty("Current.WindDirectionLong", self.Localize.localize_text_special.get(info["cc"][11], [info["cc"][11]])[-1])
        # Current wind speed (e.g. 10 mph)
        self.WINDOW.setProperty("Current.WindSpeed", self.Localize.localize_unit(info["cc"][8], "speed"))
        # Current wind gust (e.g. Gust to 20 mph)
        self.WINDOW.setProperty("Current.WindGust", self.Localize.localize_unit(info["cc"][9], "wind", NA=True))
        # Current wind gust speed (e.g. 20 mph)
        self.WINDOW.setProperty("Current.WindGustSpeed", self.Localize.localize_unit(info["cc"][9], "speed", NA=True))
        # $END_GROUP

        # 5-day forecast - loop thru and set each day
        for day in info["days"]:
            # $BEGIN_GROUP[5 Day forecast]
            # Days name (e.g. Monday)
            self.WINDOW.setProperty("Day{day}.Title".format(day=day[0]), self.Localize.localize_text_special.get(day[1], [day[1]])[-1])
            # Days name (e.g. Monday)
            self.WINDOW.setProperty("Day{day}.Day".format(day=day[0]), self.Localize.localize_text_special.get(day[1], [day[1]])[-1])
            # Days abbreviated name (e.g. Mon)
            self.WINDOW.setProperty("Day{day}.DayShort".format(day=day[0]), self.Localize.localize_text_special.get(day[1], [day[1]])[0])
            # Days date (e.g. October 1)
            self.WINDOW.setProperty("Day{day}.Date".format(day=day[0]), self.Localize.localize_unit(day[2], "monthdate", long=True))
            # Days abbreviated date (e.g. Oct 1)
            self.WINDOW.setProperty("Day{day}.DateShort".format(day=day[0]), self.Localize.localize_unit(day[2], "monthdate"))
            # Days low temperature (e.g. 50)
            self.WINDOW.setProperty("Day{day}.LowTemp".format(day=day[0]), self.Localize.localize_unit(day[4]))
            # Days high temperature (e.g. 70)
            self.WINDOW.setProperty("Day{day}.HighTemp".format(day=day[0]), self.Localize.localize_unit(day[3]))
            # Days sunrise (e.g. 7:39 AM)
            self.WINDOW.setProperty("Day{day}.Sunrise".format(day=day[0]), self.Localize.localize_unit(day[5], "time"))
            # Days sunset (e.g. 7:02 PM)
            self.WINDOW.setProperty("Day{day}.Sunset".format(day=day[0]), self.Localize.localize_unit(day[6], "time"))
            # $END_GROUP

            # $BEGIN_GROUP[5 Day forecast (daytime)]
            # Daytime outlook icon code number (e.g. 34)
            self.WINDOW.setProperty("Day{day}.FanartCode".format(day=day[0]), day[7])
            # Daytime humidity (e.g. 58%)
            self.WINDOW.setProperty("Day{day}.Humidity".format(day=day[0]), "{value}%".format(value=day[15]))
            # Daytime outlook description (e.g. Mostly Sunny)
            self.WINDOW.setProperty("Day{day}.Outlook".format(day=day[0]), " ".join([self.Localize.localize_text.get(word, word) for word in day[8].split(" ") if (word)]))
            # Daytime outlook brief description (e.g. M Sunny) (Does NOT localize properly)
            self.WINDOW.setProperty("Day{day}.OutlookBrief".format(day=day[0]), " ".join([self.Localize.localize_text.get(word, word) for word in day[13].split(" ") if (word)]))
            # Daytime outlook icon path (*see settings)
            self.WINDOW.setProperty("Day{day}.OutlookIcon".format(day=day[0]), os.path.join(self.Addon.getSetting("icon_path_weather"), day[7] + ".png"))
            # Daytime chance of precipitation (e.g. 60)
            self.WINDOW.setProperty("Day{day}.Precipitation".format(day=day[0]), day[14])
            # Daytime wind (e.g. From WNW at 10 mph)
            self.WINDOW.setProperty("Day{day}.Wind".format(day=day[0]), self.Localize.localize_unit(day[9], "wind", direction=day[12]))
            # Daytime wind (e.g. From the West Northwest at 10 mph)
            self.WINDOW.setProperty("Day{day}.WindLong".format(day=day[0]), self.Localize.localize_unit(day[9], "wind", direction=day[12], long=True))
            # Daytime wind direction in degrees (e.g. 300°)
            self.WINDOW.setProperty("Day{day}.WindDegrees".format(day=day[0]), "{value}°".format(value=day[11]))
            # Daytime wind direction (abbreviated) (e.g. WNW)
            self.WINDOW.setProperty("Day{day}.WindDirection".format(day=day[0]), self.Localize.localize_text_special.get(day[12], [day[12]])[0])
            # Daytime wind direction (e.g. West Northwest)
            self.WINDOW.setProperty("Day{day}.WindDirectionLong".format(day=day[0]), self.Localize.localize_text_special.get(day[12], [day[12]])[-1])
            # Daytime wind speed (e.g. 10 mph)
            self.WINDOW.setProperty("Day{day}.WindSpeed".format(day=day[0]), self.Localize.localize_unit(day[9], "speed"))
            # Daytime wind gust (e.g. Gust to 20 mph)
            self.WINDOW.setProperty("Day{day}.WindGust".format(day=day[0]), self.Localize.localize_unit(day[10], "wind", NA=True))
            # Daytime wind gust speed (e.g. 20 mph)
            self.WINDOW.setProperty("Day{day}.WindGustSpeed".format(day=day[0]), self.Localize.localize_unit(day[10], "speed", NA=True))
            # $END_GROUP

            # $BEGIN_GROUP[5 Day forecast (nighttime)]
            # Nighttime outlook icon code number (e.g. 33)
            self.WINDOW.setProperty("Night{day}.FanartCode".format(day=day[0]), day[16])
            # Nighttime humidity (e.g. 49%)
            self.WINDOW.setProperty("Night{day}.Humidity".format(day=day[0]), "{value}%".format(value=day[24]))
            # Nighttime outlook description (e.g. Partly Cloudy)
            self.WINDOW.setProperty("Night{day}.Outlook".format(day=day[0]), " ".join([self.Localize.localize_text.get(word, word) for word in day[17].split(" ") if (word)]))
            # Nighttime outlook brief description (e.g. P Cloudy) (Does NOT localize properly)
            self.WINDOW.setProperty("Night{day}.OutlookBrief".format(day=day[0]), " ".join([self.Localize.localize_text.get(word, word) for word in day[22].split(" ") if (word)]))
            # Nighttime outlook icon path (*see settings)
            self.WINDOW.setProperty("Night{day}.OutlookIcon".format(day=day[0]), os.path.join(self.Addon.getSetting("icon_path_weather"), day[16] + ".png"))
            # Nighttime chance of precipitation (e.g. 60)
            self.WINDOW.setProperty("Night{day}.Precipitation".format(day=day[0]), day[23])
            # Nighttime wind (e.g. From WNW at 5 mph)
            self.WINDOW.setProperty("Night{day}.Wind".format(day=day[0]), self.Localize.localize_unit(day[18], "wind", direction=day[21]))
            # Nighttime wind (e.g. From the West Northwest at 5 mph)
            self.WINDOW.setProperty("Night{day}.WindLong".format(day=day[0]), self.Localize.localize_unit(day[18], "wind", direction=day[21], long=True))
            # Nighttime wind direction in degrees (e.g. 300°)
            self.WINDOW.setProperty("Night{day}.WindDegrees".format(day=day[0]), "{value}°".format(value=day[20]))
            # Nighttime wind direction (abbreviated) (e.g. WNW)
            self.WINDOW.setProperty("Night{day}.WindDirection".format(day=day[0]), self.Localize.localize_text_special.get(day[21], [day[21]])[0])
            # Nighttime wind direction (e.g. West Northwest)
            self.WINDOW.setProperty("Night{day}.WindDirectionLong".format(day=day[0]), self.Localize.localize_text_special.get(day[21], [day[21]])[-1])
            # Nighttime wind speed (e.g. 5 mph)
            self.WINDOW.setProperty("Night{day}.WindSpeed".format(day=day[0]), self.Localize.localize_unit(day[18], "speed"))
            # Nighttime wind gust (e.g. Gust to 10 mph)
            self.WINDOW.setProperty("Night{day}.WindGust".format(day=day[0]), self.Localize.localize_unit(day[19], "wind", NA=True))
            # Nighttime wind gust speed (e.g. 10 mph)
            self.WINDOW.setProperty("Night{day}.WindGustSpeed".format(day=day[0]), self.Localize.localize_unit(day[19], "speed", NA=True))
            # $END_GROUP
