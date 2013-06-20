"""
    weather.com api client module
"""

# main imports
import sys
import os

try:
    import xbmc
    DEBUG = False
except:
    DEBUG = True

import urllib2
from urllib import urlencode
import md5
import re
import time

# TODO: maybe use xbmc language strings for brief outlook translation
def _translate_text( text, translate ):
    # base babelfish url
    url = "http://babelfish.yahoo.com/translate_txt"
    try:
        # trick for translating T-Storms, TODO: verify if this is necessary
        text = text.replace( "T-Storms", "Thunderstorms" )
        # data dictionary
        data = { "ei": "UTF-8", "doit": "done", "fr": "bf-home", "intl": "1", "tt": "urltext", "trtext": text, "lp": translate, "btnTrTxt": "Translate" }
        # request url
        request = urllib2.Request( url, urlencode( data ) )
        # add a faked header, we use ie 8.0. it gives correct results for regex
        request.add_header( "User-Agent", "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727)" )
        # open requested url
        usock = urllib2.urlopen( request )
        # read htmlSource
        htmlSource = usock.read()
        # close socket
        usock.close()
        # find translated text
        text = re.findall( "<div id=\"result\"><div style=\"[^\"]+\">([^<]+)", htmlSource )[ 0 ]
    except Exception, e:
        # TODO: add error checking?
        pass
    # return translated text
    return text

def _normalize_outlook( outlook ):
    # if we're debugging xbmc module is not available
    tid = "F"
    sid = "mph"
    if ( not DEBUG ):
        tid = xbmc.getRegion( id="tempunit" )[ -1 ]
        sid = xbmc.getRegion( id="speedunit" )
    # enumerate thru and localize values
    for count, tmp_outlook in enumerate( outlook ):
        if ( tid == "C" ):
            # calculate the localized temp if C is required
            temps = re.findall( "[0-9]+F", tmp_outlook )
            for temp in temps:
                tmp_outlook = re.sub( temp, _localize_unit( temp ) + tid, tmp_outlook, 1 )
            # calculate the localized temp ranges if C is required
            temps = re.findall( "[low|mid|high]+ [0-9]+s", tmp_outlook )
            add = { "l": 3, "m": 6, "h": 9 }
            for temp in temps:
                new_temp = _localize_unit( str( int( re.findall( "[0-9]+", temp )[ 0 ] ) + add.get( temp[ 0 ], 3 ) ) )
                temp_int = int( float( new_temp ) / 10 ) * 10
                temp_rem = int( float( new_temp ) % 10 )
                temp_text = ( "low %ds", "mid %ds", "high %ds", )[ ( temp_rem >= 4 ) + ( temp_rem >= 6 ) ]
                tmp_outlook = re.sub( temp, temp_text % ( temp_int, ), tmp_outlook, 1 )
        if ( sid != "mph" ):
            # calculate the localized wind if C is required
            winds = re.findall( "[0-9]+ to [0-9]+ mph", tmp_outlook )
            for wind in winds:
                speeds = re.findall( "[0-9]+", wind )
                for speed in speeds:
                    wind = re.sub( speed, _localize_unit( speed, "speed" ).split( " " )[ 0 ], wind, 1 )
                tmp_outlook = re.sub( "[0-9]+ to [0-9]+ mph", wind.replace( "mph", sid ), tmp_outlook, 1 )
        # add our text back to the main variable
        outlook[ count ] = tmp_outlook
    # return normalized text
    return outlook

def _localize_unit( value, unit="temp" ):
    # grab the specifier
    value_specifier = value.split( " " )[ -1 ]
    # replace any invalid characters
    value = value.replace( chr(176), "" ).replace( "&deg;", "" ).replace( "mph", "" ).replace( "miles", "" ).replace( "mile", "" ).replace( "in.", "" ).replace( "F", "" ).replace( "AM", "" ).replace( "PM", "" ).replace( "am", "" ).replace( "pm", "" ).strip()
    # do not convert invalid values
    if ( not value or value.startswith( "N/A" ) ):
        return value
    # time conversion
    if ( unit == "time" or unit == "time24" ):
        # format time properly
        if ( ":" not in value ):
            value += ":00"
        # set default time
        time = value
        # set our default temp unit
        id = ( "H:mm", "h:mm:ss xx", )[ unit == "time" ]
        # if we're debugging xbmc module is not available
        if ( not DEBUG and unit == "time" ):
            id = xbmc.getRegion( id="time" )
        # 24 hour ?
        if ( id.startswith( "H" ) ):
            hour = int( value.split( ":" )[ 0 ] )
            hour += ( 12 * ( value_specifier == "PM" and int( value.split( ":" )[ 0 ] ) != 12 ) )
            hour -= ( 12 * ( value_specifier == "AM" and int( value.split( ":" )[ 0 ] ) == 12 ) )
            time = "%d:%s" % ( hour, value.split( ":" )[ 1 ], )
        # add am/pm if used
        if ( id.endswith( "xx" ) ):
            time = "%s %s" % ( time, value_specifier, ) 
        # return localized time
        return time
    else:
        # we need a float
        value = float( value )
        # temp conversion
        if ( unit == "temp" or  unit == "tempdiff" ):
            # set our default temp unit
            id = "F"
            # if we're debugging xbmc module is not available
            if ( not DEBUG ):
                id = xbmc.getRegion( id="tempunit" )[ -1 ]
            # calculate the localized temp if C is required
            if ( id == "C" ):
                # C/F difference or temperature conversion
                if ( unit == "tempdiff" ):
                    # 9 degrees of F equal 5 degrees of C
                    value = round( float( 5 * value ) / 9 )
                else:
                    # convert to celcius
                    value = round( ( value - 32 ) * ( float( 5 ) / 9 ) )
            # return localized temp
            return "%s%d" % ( ( "", "+", )[ value >= 0 and unit == "tempdiff" ], value )
        # speed conversion
        elif ( unit == "speed" ):
            # set our default temp unit
            id = "mph"
            # if we're debugging xbmc module is not available
            if ( not DEBUG ):
                id = xbmc.getRegion( id="speedunit" )
            # calculate the localized speed
            if ( id == "km/h" ):
                value = round( value * 1.609344 )
            elif ( id == "m/s" ):
                value = round( value * 0.45 )
            elif ( id == "ft/min" ):
                value = round( value * 88 )
            elif ( id == "ft/s" ):
                value = round( value * 1.47 )
            elif ( id == "yard/s" ):
                value = round( value * 0.4883 )
            # return localized speed
            return "%d %s" % ( value, id, )
        # depth conversion
        elif ( unit == "depth" ):
            # set our default depth unit
            id = "in."
            # if we're debugging xbmc module is not available
            if ( not DEBUG ):
                id = ( "in.", "cm.", )[ xbmc.getRegion( id="tempunit" )[ -1 ] == "C" ]
            # calculate the localized depth
            if ( id == "cm." ):
                value = float( value * 2.54 )
            # return localized depth
            return "%.2f %s" % ( value, id, )
        # pressure conversion
        elif ( unit == "pressure" ):
            # set our default pressure unit
            id = "in."
            # if we're debugging xbmc module is not available
            if ( not DEBUG ):
                id = ( "in.", "mb.", )[ xbmc.getRegion( id="tempunit" )[ -1 ] == "C" ]
            # calculate the localized pressure
            if ( id == "mb." ):
                value = float( value * 33.8637526 )
            # return localized pressure
            return "%.2f %s" % ( value, id, )
        # distance conversion
        elif ( unit == "distance" ):
            # set our default distance unit
            id = "mile"
            # if we're debugging xbmc module is not available
            if ( not DEBUG ):
                id = ( "kilometer", "mile", )[ xbmc.getRegion( id="speedunit" ) == "mph" ]
            # calculate the localized distance
            if ( id == "kilometer" ):
                value = float( value * 1.609344 )
            # pluralize for values != 1
            if ( value != 1.0 ):
                id += "s"
            # return localized distance
            return "%.1f %s" % ( value, id, )


class WeatherAlert:
    def __init__( self, htmlSource ):
        self.alert = ""
        self.title = ""
        self.alert_rss = ""
        try:
            self._get_alert( htmlSource )
        except:
            pass

    def _get_alert( self, htmlSource ):
        # regex patterns
        pattern_alert = "<h1>([^<]+)</h1>"
        pattern_expires = "<p>(<b>.+?</b>[^<]+)</p>"
        pattern_issuedby = "<p class=\"alIssuedBy\">(.+?)</p>"
        pattern_narrative = "<p class=\"alNarrative\">(.*?)</p>"
        pattern_moreinfo = "<h2>([^<]+)</h2>\n.+?<p class=\"alSynopsis\">"
        pattern_synopsis = "<p class=\"alSynopsis\">(.+?)</p>"
        # fetch alert
        alert = re.findall( pattern_alert, htmlSource )[ 0 ]
        # fetch expires
        try:
            expires = re.findall( pattern_expires, htmlSource )[ 0 ].replace( "<b>", "" ).replace( "</b>", "" )
        except:
            expires = ""
        # fetch issued by
        try:
            issuedby_list = re.findall( pattern_issuedby, htmlSource, re.DOTALL )[ 0 ].split( "<br>" )
            issuedby = "[I]"
            for item in issuedby_list:
                issuedby += item.strip()
                issuedby += "\n"
            issuedby += "[/I]"
            # fetch narrative
            description_list = re.findall( pattern_narrative, htmlSource, re.DOTALL )
            narrative = ""
            for item in description_list:
                narrative += "%s\n\n" % ( item.strip(), )
            try:
                # fetch more info
                moreinfo = re.findall( pattern_moreinfo, htmlSource )[ 0 ]
                moreinfo = "[B]%s[/B]" % ( moreinfo, )
                # fetch sysnopsis
                description_list = re.findall( pattern_synopsis, htmlSource, re.DOTALL )
                synopsis = ""
                for item in description_list:
                    synopsis += "%s\n\n" % ( item.strip(), )
            except:
                moreinfo = ""
                synopsis = ""
        except:
            try:
                narrative = ""
                synopsis = ""
                issuedby = re.findall( "<p>(.+)?</p>", htmlSource )[ 0 ]
                items =  re.findall( "<B>(.+)?</B>\s.*\s.*\s.*\s.+?<IMG SRC=\"[^>]+> <B>([^<]+)</B><BR>Type: (.+)", htmlSource )[ 0 ]
                moreinfo = "\nType: %s (%s)\nLevel: %s" % ( items[ 0 ], items[ 2 ], items[ 1 ], )
            except:
                pass
        try:
            # create our alert string
            self.alert = "[B]%s[/B]\n%s\n\n%s\n%s\n\n%s\n\n%s" % ( alert, expires, issuedby, narrative.strip(), moreinfo, synopsis.strip(), )
            self.alert = "%s\n%s\n\n" % ( self.alert.strip(), "-"*100, )
            # we use this for adding titles at the begining of the alerts text for multiple alerts
            self.title = "[B]%s[/B]" % ( alert, )
            # set the alert rss
            self.alert_rss = "[COLOR=rss_headline]%s:[/COLOR] %s %s - %s" % ( alert, alert, expires, issuedby.replace( "\n", " " ), )
        except:
            self.alert = None
            self.title = ""
            self.alert_rss = ""

class Forecast36HourParser:
    def __init__( self, htmlSource, translate=None ):
        self.forecast = []
        self.extras = []
        self.alerts = []
        self.video_location = []
        self.translate = translate
        # only need to parse source if there is source
        if ( htmlSource ):
            self._get_forecast( htmlSource )

    def _get_forecast( self, htmlSource ):
        # regex patterns
        pattern_locstate = "var omn_locstate=\"([^\"]+)\""
        pattern_video_location = ">Watch the ([A-Za-z ]+) Forecast<"
        pattern_alerts = "alertArray\[[0-9]+\] = new alertObj\('([^']+)','([^']+)','([^']+)'"
        pattern_days = "from=[^\"]+\" class=\"[^\"]+\"><B>([^<]+)</font></B></A></td>"
        pattern_icon = "<img src=\"http://image.weather.com/web/common/wxicons/[0-9]+/([0-9]+)\.gif\?[^\"]+\" alt=\""
        pattern_forecast_brief = "<font CLASS=\"[^\"]+\">([^<]+)</font>"
        pattern_temp = "<td valign=\"middle\" align=\"[^\"]+\"><font CLASS=\"[^\"]+\">([^<]+)<br>[^<]+<font class=\"[^\"]+\"><[^<]+>([^<]+)<[^<]+></font>"
        pattern_precip_title = "<TD valign=\"[^\"]+\" width=\"[^\"]+\" class=\"[^\"]+\" align=\"[^\"]+\">([A-Za-z]+[^<]+)</td>"
        pattern_precip_amount = "<TD valign=\"[^\"]+\" width=\"[^\"]+\" class=\"[^\"]+\" align=\"[^\"]+\">([0-9]+[^<]+)</td>"
        pattern_outlook = "<DIV STYLE=\"padding:5px 5px 5px 0px;\">([^\n|^<]*)"
        pattern_daylight = "<TD valign=\"[^\"]+\" align=\"[^\"]+\" class=\"[^\"]+\">([^<]+)</TD>"
        pattern_extra_info = "<div class=\"crow\"><div class=\"crowli\">Pressure:</div><div class=\"crowval\">([^<]+)<[^<]+<IMG SRC=\"http://image.weather.com/web/common/icons/([^\"]+)\"></div></div>.*?\
.+?\
[^<]+<div class=\"crow\"><div class=\"crowli\">Visibility:</div><div class=\"crowval\">([^<]+)</div></div>\
[^<]+<div class=\"crow\"><div class=\"crowli\">Sunrise:</div><div class=\"crowval\">([^<]+)</div></div>\
[^<]+<div class=\"crow\"><div class=\"crowli\">Sunset:</div><div class=\"crowval\">([^<]+)</div></div>"
        # fetch days
        days = re.findall( pattern_days, htmlSource )
        # enumerate thru and combine the day with it's forecast
        if ( len( days ) ):
            try:
                # fetch state
                locstate = re.findall( pattern_locstate, htmlSource )[ 0 ].lower()
                # fetch video location
                self.video_location = ( re.findall( pattern_video_location, htmlSource )[ 0 ].lower().replace( " ", "" ), locstate, )
            except:
                pass
            # fetch alerts
            self.alerts = re.findall( pattern_alerts, htmlSource )
            print self.alerts
            # fetch icon
            icon = re.findall( pattern_icon, htmlSource )
            # fetch brief description
            brief = re.findall( pattern_forecast_brief, htmlSource )
            # fetch temperature
            temperature = re.findall( pattern_temp, htmlSource )
            # fetch precip title
            precip_title = re.findall( pattern_precip_title, htmlSource )
            # fetch precip title
            precip_amount = re.findall( pattern_precip_amount, htmlSource )
            # fetch forecasts
            outlook = re.findall( pattern_outlook, htmlSource )
            # fetch daylight
            daylight = re.findall( pattern_daylight, htmlSource )
            # fetch extra info
            extras = re.findall( pattern_extra_info, htmlSource, re.DOTALL )
            # localize our extra info
            if ( extras ):
                self.extras += [ u"%s %s" % ( _localize_unit( extras[ 0 ][ 0 ].replace( "&nbsp;", " " ), "pressure" ), { "up_pressure.gif": u"\u2191", "down_pressure.gif": u"\u2193", "steady_pressure.gif": u"\u2192" }[ extras[ 0 ][ 1 ] ], ) ]
                self.extras += [ _localize_unit( extras[ 0 ][ 2 ], "distance" ) ]
                self.extras += [ _localize_unit( extras[ 0 ][ 3 ], "time" ) ]
                self.extras += [ _localize_unit( extras[ 0 ][ 4 ], "time" ) ]
            # convert outlook wind/temp values
            outlook = _normalize_outlook( outlook )
            # translate brief and outlook if user preference
            if ( self.translate is not None ):
                # we only need outlook and brief. the rest the skins or xbmc language file can handle
                # we separate each item with single pipe
                text = "|".join( outlook )
                # separator for different info
                text += "|||||"
                # we separate each item with single pipe
                text += "|".join( brief )
                # translate text
                text = _translate_text( text, self.translate )
                # split text into it's original list
                outlook = text.split( "|||||" )[ 0 ].split( "|" )
                brief = text.split( "|||||" )[ 1 ].split( "|" )
            for count, day in enumerate( days ):
                # make icon path
                iconpath = "/".join( [ "special://temp", "weather", "128x128", icon[ count ] + ".png" ] )
                # add result to our class variable
                self.forecast += [ ( day, iconpath, brief[ count ], temperature[ count ][ 0 ], _localize_unit( temperature[ count ][ 1 ] ), precip_title[ count ], precip_amount[ count ].replace( "%", "" ), outlook[ count ].strip(), daylight[ count ].split( ": " )[ 0 ], _localize_unit( daylight[ count ].split( ": " )[ 1 ], "time" ), ) ]


class ForecastHourlyParser:
    def __init__( self, htmlSource, translate ):
        self.forecast = []
        self.translate = translate
        # only need to parse source if there is source
        if ( htmlSource ):
            self._get_forecast( htmlSource )

    def _get_forecast( self, htmlSource ):
        # regex patterns
        #pattern_headings = "<div class=\"hbhTD[^\"]+\"><div title=\"[^>]+>([^<]+)</div></div>"
        pattern_date = "<div class=\"hbhDateHeader\">([^<]+)</div>"
        pattern_sunrise = "<img src=\"http://i.imwx.com/web/local/hourbyhour/icon_sunrise.gif\"[^>]+>([^<]+)"
        pattern_sunset = "<img src=\"http://i.imwx.com/web/local/hourbyhour/icon_sunset.gif\"[^>]+>([^<]+)"
        # use this to grab the 15 minutes details
        # pattern_info = "<div class=\"hbhTDTime[^>]+><div>([^<]+)</div></div>\
        # use this to grab only 1 hour details
        pattern_info = "<div class=\"hbhTDTime\"><div>([^<]+)</div></div>\
[^<]+<div class=\"hbhTDConditionIcon\"><div><img src=\"http://i.imwx.com/web/common/wxicons/[0-9]+/(gray/)?([0-9]+).gif\"[^>]+></div></div>\
[^<]+<div class=\"hbhTDCondition\"><div><b>([^<]+)</b><br>([^<]+)</div></div>\
[^<]+<div class=\"hbhTDFeels\"><div>([^<]*)</div></div>\
[^<]+<div class=\"hbhTDPrecip\"><div>([^<]*)</div></div>\
[^<]+<div class=\"hbhTDHumidity\"><div>([^<]*)</div></div>\
[^<]+<div class=\"hbhTDWind\"><div>([^<]*)(<br>)?([^<]*)</div></div>"
        """
        pattern_time = "<div class=\"hbhTDTime[^>]+><div>([^<]+)</div>"
        pattern_icon = "<div class=\"hbhTDConditionIcon\"><div><img src=\"http://i.imwx.com/web/common/wxicons/[0-9]+/(gray/)?([0-9]+).gif\""
        pattern_brief = "<div class=\"hbhTDCondition\"><div><b>([^<]+)</b><br>([^<]+)</div>"
        pattern_feels = "<div class=\"hbhTDFeels\"><div>([^<]*)</div>"
        pattern_precip = "<div class=\"hbhTDPrecip\"><div>([^<]*)</div>"
        pattern_humidity = "<div class=\"hbhTDHumidity\"><div>([^<]*)</div>"
        pattern_wind = "<div class=\"hbhTDWind\"><div>([^<]*)<br>([^<]*)</div>"
        """
        # fetch info
        info = re.findall( pattern_info, htmlSource )
        # fetch dates
        dates = re.findall( pattern_date, htmlSource )
        # hack for times when weather.com, does not display date
        dates += [ ", " ]
        # fetch sunrise
        sunrises = re.findall( pattern_sunrise, htmlSource )
        # fetch sunset
        sunsets = re.findall( pattern_sunset, htmlSource )
        # enumerate thru and create heading and forecast
        if ( len( info ) ):
            # we convert wind direction to full text
            windir = {    
                            "From N": "From the North",
                            "From NNE": "From the North Northeast",
                            "From NE": "From the Northeast",
                            "From ENE": "From the East Northeast",
                            "From E": "From the East",
                            "From ESE": "From the East Southeast",
                            "From SE": "From the Southeast",
                            "From SSE": "From the South Southeast",
                            "From S": "From the South",
                            "From SSW": "From the South Southwest",
                            "From SW": "From the Southwest",
                            "From WSW": "From the West Southwest",
                            "From W": "From the West",
                            "From WNW": "From the West Northwest",
                            "From NW": "From the Northwest",
                            "From NNW": "From the North Northwest"
                        }
            brief = []
            wind = []
            for item in info:
                wind += [ windir.get( item[ 8 ], item[ 8 ] ) ]
                brief += [ item[ 4 ] ]
            # translate brief and outlook if user preference
            if ( self.translate is not None ):
                # we only need outlook and brief. the rest the skins or xbmc language file can handle
                # we separate each item with single pipe
                text = "|".join( wind )
                # separator for different info
                text += "|||||"
                # we separate each item with single pipe
                text += "|".join( brief )
                # translate text
                text = _translate_text( text, self.translate )
                # split text into it's original list
                wind = text.split( "|||||" )[ 0 ].split( "|" )
                brief = text.split( "|||||" )[ 1 ].split( "|" )
            # counter for date
            date_counter = 0
            # create our forecast list
            for count, item in enumerate( info ):
                # make icon path
                iconpath = "/".join( [ "special://temp", "weather", "128x128", item[ 2 ] + ".png" ] )
                # do we need to increment date_counter
                if ( item[ 0 ] == "12 am" and count > 0 ):
                    date_counter += 1
                # does sunrise/sunset fit in this period
                sunrise = ""
                sunset = ""
                # we want 24 hour as the math is easier
                period = _localize_unit( item[ 0 ], "time24" )
                # set to a high number, we use this for checking next time period
                period2 = "99:00"
                if ( count < len( info ) - 2 ):
                    period2 = _localize_unit( info[ count + 1 ][ 0 ], "time24" )
                    period2 = ( period2, "24:%s" % ( period2.split( ":" )[ 1 ], ), )[ period2.split( ":" )[ 0 ] == "0" ]
                # sunrise
                if ( sunrises ):
                    # get the 24 hour sunrise time
                    sunrise_check = _localize_unit( sunrises[ 0 ].strip().split( "Sunrise" )[ 1 ].strip(), "time24" )
                    # if in the correct time range, set our variable
                    if ( int( sunrise_check.split( ":" )[ 0 ] ) == int( period.split( ":" )[ 0 ] ) and int( sunrise_check.split( ":" )[ 1 ] ) >= int( period.split( ":" )[ 1 ] ) and 
                        ( int( sunrise_check.split( ":" )[ 1 ] ) < int( period2.split( ":" )[ 1 ] ) or int( sunrise_check.split( ":" )[ 0 ] ) < int( period2.split( ":" )[ 0 ] ) ) ):
                        sunrise = _localize_unit( sunrises[ 0 ].strip().split( "Sunrise" )[ 1 ].strip(), "time" )
                # sunset
                if ( sunsets ):
                    # get the 24 hour sunset time
                    sunset_check = _localize_unit( sunsets[ 0 ].strip().split( "Sunset" )[ 1 ].strip(), "time24" )
                    # if in the correct time range, set our variable
                    if ( int( sunset_check.split( ":" )[ 0 ] ) == int( period.split( ":" )[ 0 ] ) and int( sunset_check.split( ":" )[ 1 ] ) >= int( period.split( ":" )[ 1 ] ) and 
                        ( int( sunset_check.split( ":" )[ 1 ] ) < int( period2.split( ":" )[ 1 ] ) or int( sunset_check.split( ":" )[ 0 ] ) < int( period2.split( ":" )[ 0 ] ) ) ):
                        sunset = _localize_unit( sunsets[ 0 ].strip().split( "Sunset" )[ 1 ].strip(), "time" )
                # add result to our class variable
                self.forecast += [ ( _localize_unit( item[ 0 ], "time" ), dates[ date_counter ].split( ", " )[ -1 ], iconpath, _localize_unit( item[ 3 ] ), brief[ count ], _localize_unit( item[ 5 ] ), item[ 6 ].replace( "%", "" ), item[ 7 ].replace( "%", "" ), wind[ count ], _localize_unit( item[ 10 ], "speed" ), item[ 8 ].split( " " )[ -1 ], sunrise, sunset, ) ]


class ForecastWeekendParser:
    def __init__( self, htmlSource, translate ):
        self.forecast = []
        self.translate = translate
        # only need to parse source if there is source
        if ( htmlSource ):
            self._get_forecast( htmlSource )

    def _get_forecast( self, htmlSource ):
        # regex patterns
        pattern_heading = "from=[\"]*weekend[\"]+>([^<]+)</A>.*\s.*\s\
[^<]+<TD width=\"[^\"]+\" class=\"wkndButton[A-Z]+\" align=\"[^\"]+\" valign=\"[^\"]+\"><FONT class=\"[^\"]+\">([^\&]+)&nbsp;.*\s.*\s.*\s.*\s.*\s.*\s.*\s.*\s.*\s.*\s\
[^>]+>[^>]+>([^<]+)<"
        pattern_observed = ">(Observed:)+"
        pattern_brief = "<IMG src=\"http://(?:i.imwx.com)?(?:image.weather.com)?/web/common/wxicons/(?:pastwx/)?[0-9]+/([0-9]+).gif.*alt=\"([^\"]+)\""
        pattern_past = "<TD align=\"left\" class=\"grayFont10\">([^<]+)</TD>"
        pattern_past2 = "<TD align=\"[left|right]+\" class=\"blueFont10\">[<B>]*<FONT color=\"[^\"]+\">([^\s|^<]+)[^\n]+"
        pattern_avg = "<tr><td align=\"right\" valign=\"top\" CLASS=\"blueFont10\">([^<]+)<.*\s.*\s[^[A-Z0-9]+(.*&deg;[F|C]+)"
        pattern_high = "<FONT class=\"[^\"]+\">([^<]+)<BR><FONT class=\"[^\"]+\"><NOBR>([^<]+)</FONT></NOBR>"
        pattern_low = "<FONT class=\"[^\"]+\">([^<]+)</FONT><BR><FONT class=\"[^\"]+\"><B>([^<]+)</B></FONT>"
        pattern_precip = "<TD valign=\"top\" width=\"50%\" class=\"blueFont10\" align=\"[left|right]+\">(.*)"
        pattern_wind = "<td align=\"[^\"]+\" valign=\"[^\"]+\" CLASS=\"[^\"]+\">([^<]+)</td><td align=\"[^\"]+\">&nbsp;</td><td valign=\"[^\"]+\" CLASS=\"[^\"]+\"><B>.*\n[^A-Z]+([A-Z]+)<br>([^<]+)</B>"
        pattern_uv = "<td align=\"[^\"]+\" valign=\"[^\"]+\" CLASS=\"[^\"]+\">([^<]+)</td>\s[^>]+>[^>]+>[^>]+><B>([^<]+)"
        pattern_humidity = "<td align=\"[^\"]+\" valign=\"[^\"]+\" CLASS=\"[^\"]+\">([^<]+)[^>]+>[^>]+>[^>]+>[^>]+><B>([0-9]+%)"
        pattern_daylight = "<td align=\"[^\"]+\" valign=\"[^\"]+\" CLASS=\"[^\"]+\">([^<]+)[^>]+>[^>]+>[^>]+>[^>]+><B>([0-9]+:[0-9]+[^<]+)</B></td>"
        pattern_outlook = "<TD colspan=\"3\" class=\"blueFont10\" valign=\"middle\" align=\"left\">([^<]+)</TD>"
        pattern_departures = "<FONT COLOR=\"#7d8c9f\"><B>\s.*\s\s+(.+?F)"
        # fetch headings
        headings = re.findall( pattern_heading, htmlSource )
        # fetch observed status
        observeds = re.findall( pattern_observed, htmlSource )
        # insert necessary dummy entries
        for  i in range( 3 - len( observeds ) ):
            observeds.append( "" )
        # fetch briefs
        briefs = re.findall( pattern_brief, htmlSource )
        # insert necessary dummy entries
        for count, i in enumerate( range( 3 - len( briefs ) ) ):
            briefs.insert( count, ( "na", "", ) )
        # fetch departue from normal
        departures = re.findall( pattern_departures, htmlSource )
        for i in range( 6 - len( departures ) ):
            departures.append( "" )
        # fetch past info
        pasts = re.findall( pattern_past, htmlSource )
        if ( pasts == [] ):
            pasts2 = re.findall( pattern_past2, htmlSource )
            # create the pasts list
            for count, i in enumerate( range( 0, len( pasts2 ), 2 ) ):
                pasts += [ pasts2[ count * 2 ] + pasts2[ count * 2 + 1 ] ]
        # insert necessary dummy entries
        for i in range( 9 - len( pasts ) ):
            pasts.append( ":&nbsp;" )
        # fetch average info
        avgs = re.findall( pattern_avg, htmlSource )
        # insert necessary dummy entries
        for i in range( 0, 12 - len( avgs ) ):
            avgs.append( ( "", "", ) )
        # fetch highs
        highs = re.findall( pattern_high, htmlSource )
        # insert necessary dummy entries
        for count, i in enumerate( range( 3 - len( highs ) ) ):
            highs.insert( count, ( pasts[ count * 3 ].split( ":&nbsp;" )[ 0 ], pasts[ count * 3 ].split( ":&nbsp;" )[ 1 ], ) )
        # fetch lows
        lows = re.findall( pattern_low, htmlSource )
        # insert necessary dummy entries
        for count, i in enumerate( range( 3 - len( lows ) ) ):
            lows.insert( count, ( pasts[ count * 3 + 1 ].split( ":&nbsp;" )[ 0 ], pasts[ count * 3 + 1 ].split( ":&nbsp;" )[ 1 ], ) )
        # fetch precips
        precips = re.findall( pattern_precip, htmlSource )
        # insert necessary dummy entries
        for i in range( 6 - len( precips ) ):
            precips.insert( 0, "" )
        # fetch winds
        tmp_winds = re.findall( pattern_wind, htmlSource )
        # insert necessary dummy entries
        for i in range( 3 - len( tmp_winds ) ):
            tmp_winds.insert( 0, ( "", "", "", ) )
        winds = []
        for i in range( len( tmp_winds ) ):
            if ( tmp_winds[ i ][ 0 ] != "" ):
                winds += [ ( tmp_winds[ i ][ 0 ], "%s at %s" % ( tmp_winds[ i ][ 1 ], _localize_unit( tmp_winds[ i ][ 2 ].split()[ 1 ], "speed" ), ) ), ]
            else:
                winds += [ ( "", "", ) ]
        # fetch uvs
        uvs = re.findall( pattern_uv, htmlSource )
        # insert necessary dummy entries
        for i in range( 3 - len( uvs ) ):
            uvs.insert( 0, ( "", "", ) )
        # fetch humids
        humids = re.findall( pattern_humidity, htmlSource )
        # insert necessary dummy entries
        for i in range( 3 - len( humids ) ):
            humids.insert( 0, ( "", "", ) )
        # fetch daylights
        daylights = re.findall( pattern_daylight, htmlSource )
        # insert necessary dummy entries
        for i in range( 6 - len( daylights ) ):
            daylights.insert( 0, ( "", "" ) )
        # fetch outlooks
        outlooks = re.findall( pattern_outlook, htmlSource )
        # insert necessary dummy entries
        for i in range( 3 - len( outlooks ) ):
            outlooks.insert( 0, "" )
        # separate briefs
        brief = []
        icon = []
        for item in briefs:
            brief += [ item[ 1 ] ]
            icon += [ item[ 0 ] ]
        # convert outlook wind/temp values
        outlooks = _normalize_outlook( outlooks )
        # translate brief and outlook if user preference
        if ( self.translate is not None ):
            # we only need outlook and brief. the rest the skins or xbmc language file can handle
            # we separate each item with single pipe
            text = "|".join( outlooks )
            # separator for different info
            text += "|||||"
            # we separate each item with single pipe
            text += "|".join( brief )
            # translate text
            text = _translate_text( text, self.translate )
            # split text into it's original list
            outlooks = text.split( "|||||" )[ 0 ].split( "|" )
            brief = text.split( "|||||" )[ 1 ].split( "|" )
        # no need to run if none found
        if ( len( headings ) ):
            # set our previous variables to the first items
            prevday = int( headings[ 0 ][ 1 ].split( " " )[ -1 ] )
            prevmonth = headings[ 0 ][ 1 ].split( " " )[ 0 ]
            # use a dictionary for next month
            nextmonth = { "Jan": "Feb", "Feb": "Mar", "Mar": "Apr", "Apr": "May", "May": "Jun", "Jun": "Jul", "Jul": "Aug", "Aug": "Sep", "Sep": "Oct", "Oct": "Nov", "Nov": "Dec", "Dec": "Jan" }
            # enumerate thru and create our forecast list
            for count, ( day, date, alert, ) in enumerate( headings ):
                # add a month to the date
                month = date.split( " " )[ 0 ]
                mday = int( date.split( " " )[ -1 ] )
                # month change
                if ( mday < prevday ):
                    prevmonth = nextmonth[ prevmonth ]
                # set the new date
                date = "%s %d" % ( prevmonth, mday, )
                prevday = mday
                # if no icon, set it to na
                if ( not briefs[ count ][ 0 ] ):
                    pass
                # make icon path
                iconpath = "/".join( [ "special://temp", "weather", "128x128", icon[ count ] + ".png" ] )
                # add result to our class variable
                self.forecast += [ ( day, date, iconpath, brief[ count ], highs[count][ 0 ], _localize_unit( highs[ count ][ 1 ] ),
                lows[ count ][ 0 ], _localize_unit( lows[ count ][ 1 ] ), precips[ count * 2 ], precips[ count * 2 + 1 ].replace( "%", "" ).replace( "<B>", "" ).replace( "</B>", "" ),
                winds[ count ][ 0 ], winds[ count ][ 1 ], uvs[ count ][ 0 ], uvs[ count ][ 1 ],
                humids[ count ][ 0 ], humids[ count ][ 1 ].replace( "%", "" ), daylights[ count * 2 ][ 0 ], _localize_unit( daylights[ count * 2 ][ 1 ], "time" ), daylights[ count * 2 + 1 ][ 0 ],
                _localize_unit( daylights[ count * 2 + 1 ][ 1 ], "time" ), outlooks[ count ], observeds[ count ], pasts[ count * 3 + 2 ].split( "&nbsp;" )[ 0 ], _localize_unit( pasts[ count * 3 + 2 ].split( "&nbsp;" )[ 1 ], "depth" ),
                avgs[ count * 4 ][ 0 ], _localize_unit( avgs[ count * 4 ][ 1 ] ), avgs[ count * 4 + 1 ][ 0 ], _localize_unit( avgs[ count * 4 + 1 ][ 1 ] ),
                avgs[ count * 4 + 2 ][ 0 ], _localize_unit( avgs[ count * 4 + 2 ][ 1 ] ), avgs[ count * 4 + 3 ][ 0 ], _localize_unit( avgs[ count * 4 + 3 ][ 1 ] ),
                alert.strip(), _localize_unit( departures[ count * 2 ], "tempdiff" ), _localize_unit( departures[ count * 2 + 1 ], "tempdiff" ), ) ]


class Forecast10DayParser:
    def __init__( self, htmlSource, translate ):
        self.forecast = []
        self.translate = translate
        # only need to parse source if there is source
        if ( htmlSource ):
            self._get_forecast( htmlSource )

    def _get_forecast( self, htmlSource ):
        # regex patterns
        pattern_headings = "<p id=\"tdHead[A-Za-z]+\">(.*)</p>"
        pattern_headings2 = "<OPTION value=\"windsdp\" selected>([^<]+)</OPTION>"
        pattern_info = "<p><[^>]+>([^<]+)</a><br>([^<]+)</p>\s.*\s.*\s.*\s.*\s\
[^<]+<p><img src=\"http://i.imwx.com/web/common/wxicons/[0-9]+/([0-9]+).gif[^>]+><br>([^<]+)</p>\s.*\s.*\s.*\s.*\s[^<]+<p><strong>([^<]+)</strong><br>([^<]+)</p>\s.*\s.*\s.*\s.*\s.*\s[^<]+<p>([^<]+)</p>\s.*\s.*\s.*\s.*\s.*\s.*\s.*\s[^<]+<td><p>([^<]+)</p></td>\s.*\s.*\s\
[^<]+<[^<]+<[^<]+<[^<]+<strong>([^<]+</strong>[^<]+)</p>"
        # fetch info
        info = re.findall( pattern_info, htmlSource )
        # enumerate thru and create heading and forecast
        if ( len( info ) ):
            # we convert wind direction to abbreviated text for ShortWindDirection property
            windir = {    
                            "From the North": "N",
                            "From the North Northeast": "NNE",
                            "From the Northeast": "NE",
                            "From the East Northeast": "ENE",
                            "From the East": "E",
                            "From the East Southeast": "ESE",
                            "From the Southeast": "SE",
                            "From the South Southeast": "SSE",
                            "From the South": "S",
                            "From the South Southwest": "SSW",
                            "From the Southwest": "SW",
                            "From the West Southwest": "WSW",
                            "From the West": "W",
                            "From the West Northwest": "WNW",
                            "From the Northwest": "NW",
                            "From the North Northwest": "NNW"
                        }
            brief = []
            wind = []
            for item in info:
                wind += [ item[ 7 ] ]
                brief += [ item[ 3 ] ]
            # translate brief and outlook if user preference
            if ( self.translate is not None ):
                # we only need outlook and brief. the rest the skins or xbmc language file can handle
                # we separate each item with single pipe
                text = "|".join( wind )
                # separator for different info
                text += "|||||"
                # we separate each item with single pipe
                text += "|".join( brief )
                # translate text
                text = _translate_text( text, self.translate )
                # split text into it's original list
                wind = text.split( "|||||" )[ 0 ].split( "|" )
                brief = text.split( "|||||" )[ 1 ].split( "|" )
            # create our forecast list
            for count, item in enumerate( info ):
                # make icon path
                iconpath = "/".join( [ "special://temp", "weather", "128x128", item[ 2 ] + ".png" ] )
                # add result to our class variable
                self.forecast += [ ( item[ 0 ], item[ 1 ], iconpath, brief[ count ], _localize_unit( item[ 4 ] ), _localize_unit( item[ 5 ] ), item[ 6 ].replace( "&#37;", "" ).replace( "%", "" ), wind[ count ], _localize_unit( item[ 8 ].replace( "</strong>", "" ), "speed" ), windir.get( item[ 7 ], "N/A" ), ) ]


class MaplistParser:
    def __init__( self, htmlSource ):
        self.map_list = []
        self._get_map_list( htmlSource )

    def _get_map_list( self, htmlSource ):
        try:
            # regex patterns
            pattern_map_list = "<option.+?value=\"([^\"]+)\".*?>([^<]+)</option>"
            # fetch avaliable maps
            map_list = re.findall( pattern_map_list, htmlSource, re.IGNORECASE )
            # enumerate thru list and eliminate bogus items
            for map in map_list:
                # eliminate bogus items
                if ( len( map[ 0 ] ) > 7 ):
                    self.map_list += [ map + ( "", ) ]
        except:
            pass


class MapParser:
    def __init__( self, htmlSource ):
        self.maps = ()
        self._get_maps( htmlSource )

    def _get_maps( self, htmlSource ):
        try:
            # initialize our animated maps list
            animated_maps = []
            # regex patterns
            pattern_maps = "<IMG NAME=\"mapImg\" SRC=\"([^\"]+)\""
            # fetch static map
            static_map = re.findall( pattern_maps, htmlSource )
            # does this map support animation?
            motion = re.findall( ">Weather In Motion<", htmlSource, re.IGNORECASE )
            if ( len( motion ) ):
                # get our map
                region = os.path.splitext( os.path.basename( static_map[ 0 ] ) )[ 0 ]
                # enumerate thru and create our animated map urls
                for i in range( 1, 6 ):
                    animated_maps += [ "http://image.weather.com/looper/archive/%s/%dL.jpg" % ( region, i, ) ]
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
        # set our maps object
        self.maps += ( static_map, animated_maps, "", )


class WeatherClient:
    # base urls
    BASE_URL = "http://www.weather.com"
    BASE_FORECAST_URL = "http://www.weather.com/outlook/travel/businesstraveler/%s/%s?bypassredirect=true%s"
    BASE_FORECAST_URL = "http://www.weather.com/weather/%s/%s%s"
    BASE_VIDEO_URL = "http://v.imwx.com/multimedia/video/wxflash/%s.flv"
    BASE_MAPS = (
                                # Main local maps (includes some regional maps) #0
                                ( "", "", ),
                                # Main local maps (includes some regional maps) #1
                                ( "Local", "/outlook/travel/businesstraveler/%s/%s?bypassredirect=true%s", ),
                                # weather details #2
                                ( "Weather Details (Alaska)", "/maps/geography/alaskaus/index_large.html", ),
                                ( "Weather Details (Current Weather)", "/maps/maptype/currentweatherusnational/index_large.html", ),
                                ( "Weather Details (Doppler Radar)", "/maps/maptype/dopplerradarusnational/index_large.html", ),
                                ( "Weather Details (Extended Forecasts)", "/maps/maptype/tendayforecastusnational/index_large.html", ),
                                ( "Weather Details (Hawaii)", "/maps/geography/hawaiius/index_large.html", ),
                                ( "Weather Details (Satellite - US)", "/maps/maptype/satelliteusnational/index_large.html", ),
                                ( "Weather Details (Satellite - World)", "/maps/maptype/satelliteworld/index_large.html", ),
                                ( "Weather Details (Severe Alerts - US)", "/maps/maptype/severeusnational/index_large.html", ),
                                ( "Weather Details (Severe Alerts - Regional)", "/maps/maptype/severeusregional/index_large.html", ),
                                ( "Weather Details (Short Term Forecast)", "/maps/maptype/forecastsusnational/index_large.html", ),
                                ( "Weather Details (Weekly Planner)", "/maps/maptype/weeklyplannerusnational/index_large.html", ),
                                ( "Weather Details (US Regions - Current)", "/maps/maptype/currentweatherusregional/index_large.html", ),
                                ( "Weather Details (US Regions - Forecasts)", "/maps/maptype/forecastsusregional/index_large.html", ),
                                ( "Weather Details (US Regions - Central)", "/maps/geography/centralus/index_large.html", ),
                                ( "Weather Details (US Regions - East Central)", "/maps/geography/eastcentralus/index_large.html", ),
                                ( "Weather Details (US Regions - Midwest)", "/maps/geography/midwestus/index_large.html", ),
                                ( "Weather Details (US Regions - North Central)", "/maps/geography/northcentralus/index_large.html", ),
                                ( "Weather Details (US Regions - Northeast)", "/maps/geography/northeastus/index_large.html", ),
                                ( "Weather Details (US Regions - Northwest)", "/maps/geography/northwestus/index_large.html", ),
                                ( "Weather Details (US Regions - South Central)", "/maps/geography/southcentralus/index_large.html", ),
                                ( "Weather Details (US Regions - Southeast)", "/maps/geography/southeastus/index_large.html", ),
                                ( "Weather Details (US Regions - Southwest)", "/maps/geography/southwestus/index_large.html", ),
                                ( "Weather Details (US Regions - West )", "/maps/geography/westus/index_large.html", ),
                                ( "Weather Details (US Regions - West Central)", "/maps/geography/westcentralus/index_large.html", ),
                                ( "Weather Details (World - Africa & Mid East)", "/maps/geography/africaandmiddleeast/index_large.html", ),
                                ( "Weather Details (World - Asia)", "/maps/geography/asia/index_large.html", ),
                                ( "Weather Details (World - Australia)", "/maps/geography/australia/index_large.html", ),
                                ( "Weather Details (World - Central America)", "/maps/geography/centralamerica/index_large.html", ),
                                ( "Weather Details (World - Europe)", "/maps/geography/europe/index_large.html", ),
                                ( "Weather Details (World - North America)", "/maps/geography/northamerica/index_large.html", ),
                                ( "Weather Details (World - Pacific)", "/maps/geography/pacific/index_large.html", ),
                                ( "Weather Details (World - Polar)", "/maps/geography/polar/index_large.html", ),
                                ( "Weather Details (World - South America)", "/maps/geography/southamerica/index_large.html", ),
                                # activity #35
                                ( "Outdoor Activity (Lawn and Garden)", "/maps/activity/garden/index_large.html", ),
                                ( "Outdoor Activity (Aviation)", "/maps/activity/aviation/index_large.html", ),
                                ( "Outdoor Activity (Boat & Beach)", "/maps/activity/boatbeach/index_large.html", ),
                                ( "Outdoor Activity (Business Travel)", "/maps/activity/travel/index_large.html", ),
                                ( "Outdoor Activity (Driving)", "/maps/activity/driving/index_large.html", ),
                                ( "Outdoor Activity (Fall Foliage)", "/maps/activity/fallfoliage/index_large.html", ),
                                ( "Outdoor Activity (Golf)", "/maps/activity/golf/index_large.html", ),
                                ( "Outdoor Activity (Outdoors)", "/maps/activity/nationalparks/index_large.html", ),
                                ( "Outdoor Activity (Oceans)", "/maps/geography/oceans/index_large.html", ),
                                ( "Outdoor Activity (Pets)", "/maps/activity/pets/index_large.html", ),
                                ( "Outdoor Activity (Ski)", "/maps/activity/ski/index_large.html", ),
                                ( "Outdoor Activity (Special Events)", "/maps/activity/specialevents/index_large.html", ),
                                ( "Outdoor Activity (Sporting Events)", "/maps/activity/sportingevents/index_large.html", ),
                                ( "Outdoor Activity (Vacation Planner)", "/maps/activity/vacationplanner/index_large.html", ),
                                ( "Outdoor Activity (Weddings - Spring)", "/maps/activity/weddings/spring/index_large.html", ),
                                ( "Outdoor Activity (Weddings - Summer)", "/maps/activity/weddings/summer/index_large.html", ),
                                ( "Outdoor Activity (Weddings - Fall)", "/maps/activity/weddings/fall/index_large.html", ),
                                ( "Outdoor Activity (Weddings - Winter)", "/maps/activity/weddings/winter/index_large.html", ),
                                ( "Outdoor Activity (Holidays)", "/maps/activity/holidays/index_large.html", ),
                                # health and safety #54
                                ( "Health & Safety (Aches & Pains)", "/maps/activity/achesandpains/index_large.html", ),
                                ( "Health & Safety (Air Quality)", "/maps/activity/airquality/index_large.html", ),
                                ( "Health & Safety (Allergies)", "/maps/activity/allergies/index_large.html", ),
                                ( "Health & Safety (Cold & Flu)", "/maps/activity/coldandflu/index_large.html", ),
                                ( "Health & Safety (Earthquake Reports)", "/maps/maptype/earthquakereports/index_large.html", ),
                                ( "Health & Safety (Home Planner)", "/maps/activity/home/index_large.html", ),
                                ( "Health & Safety (Schoolday)", "/maps/activity/schoolday/index_large.html", ),
                                ( "Health & Safety (Severe Weather Alerts)", "/maps/maptype/severeusnational/index_large.html", ),
                                ( "Health & Safety (Skin Protection)", "/maps/activity/skinprotection/index_large.html", ),
                                ( "Health & Safety (Fitness)", "/maps/activity/fitness/index_large.html", ),
                                # user defined #64
                                ( "User Defined - (Maps & Radars)", "*", ),
                            )

    # base paths
    if ( DEBUG ):
        BASE_MAPS_PATH = os.path.join( os.getcwd(), "maps" )
        BASE_SOURCE_PATH = os.path.join( os.getcwd(), "source" )
    else:
        BASE_MAPS_PATH = xbmc.translatePath( "/".join( [ "special://temp", os.path.basename( os.getcwd() ), "maps" ] ) )
        BASE_SOURCE_PATH = xbmc.translatePath( "/".join( [ "special://profile", "script_data", os.path.basename( os.getcwd() ), "source" ] ) )

    def __init__( self, code=None, translate=None ):
        # only check for compatibility if not debugging
        if ( not DEBUG ):
            # we raise an error if not compatible
            if ( not self._compatible() ):
                raise
        # set users locale
        self.code = code
        # set users translate preference
        self.translate = translate

    def _compatible( self ):
        # check for compatibility
        return ( not "%s" % ( str( [ chr( c ) for c in ( 98, 111, 120, 101, 101, ) ] ).replace( "'", "" ).replace( ", ", "" )[ 1 : -1 ], ) in xbmc.translatePath( "%s" % ( str( [ chr( c ) for c in ( 115, 112, 101, 99, 105, 97, 108, 58, 47, 47, 120, 98, 109, 99, 47, ) ] ).replace( "'", "" ).replace( ", ", "" )[ 1 : -1 ], ) ).lower() )

    def fetch_36_forecast( self, video ):
        # fetch source
        #"http://www.weather.com/weather/today/USME0013?bypassredirect=true"
        htmlSource = self._fetch_data( self.BASE_FORECAST_URL % ( "today", self.code, "?from=tenDay_topnav_business", ), 15 )
        # parse source for forecast
        parser = Forecast36HourParser( htmlSource, self.translate )
        # fetch any alerts
        alerts, alertsrss, alertsnotify, alertscolor = self._fetch_alerts( parser.alerts )
        # create video url
        video = self._create_video( parser.video_location, video )
        # return forecast
        return alerts, alertsrss, alertsnotify, alertscolor, len( parser.alerts), parser.forecast, parser.extras, video

    def _fetch_alerts( self, urls ):
        alerts = ""
        alertscolor = ""
        alertsrss = ""
        alertsnotify = ""
        if ( urls ):
            alertscolor = urls[ 0 ][ 0 ]
            titles = []
            # enumerate thru the alert urls and add the alerts to one big string
            for url in urls:
                # fetch source refresh every 15 minutes
                htmlSource = self._fetch_data( self.BASE_URL + url[ 2 ], 15 )
                # parse source for alerts
                parser = WeatherAlert( htmlSource )
                # needed in case a new alert format was used and we errored
                if ( parser.alert is not None ):
                    # add result to our alert string
                    alerts += parser.alert
                    titles += [ parser.title ]
                    alertsrss += "%s  |  " % ( parser.alert_rss, )
                    alertsnotify += "%s  |  " % ( parser.title.replace( "[B]", "" ).replace( "[/B]", "" ), )
            # TODO: maybe handle this above passing count to the parser
            # make our title string if more than one alert
            if ( len( titles ) > 1 ):
                title_string = ""
                for count, title in enumerate( titles ):
                    title_string += "%d. %s\n" % ( count + 1, title, )
                # add titles to alerts
                alerts = "%s\n%s\n%s\n\n%s" % (  "-" * 100, title_string.strip(), "-" * 100, alerts )
        # return alert string stripping the last newline chars
        return alerts.strip(), alertsrss.strip().rstrip( "|" ).strip(), alertsnotify.rstrip( " |" ), alertscolor

    def _create_video( self, location, video ):
        # TODO: verify only US has videos?
        if ( len( location ) and self.code.startswith( "US" ) and video == "" ):
            # no local videos, try a regional
            if ( location[ 0 ] == "northeast" or location[ 0 ] == "midwest" or location[ 0 ] == "southeast" or location[ 0 ] == "western" or location[ 0 ] == "southern" or location[ 0 ] == "southwest" or location[ 0 ] == "northwest" ):
                video = location[ 0 ]
                if ( location[ 0 ] == "western" ):
                    video = "west"
                elif ( location[ 0 ] == "southern" ):
                    video = "south"
                # create the url
                url = self.BASE_VIDEO_URL % ( video, )
                # return valid video url
                return url
            else:
                # try different extension and check if video url is valid
                exts = ( "", location[ 1 ], "city", )
                for ext in exts:
                    try:
                        # create the url
                        url = self.BASE_VIDEO_URL % ( location[ 0 ] + ext, )
                        # request url
                        request = urllib2.Request( url )
                        # add a faked header
                        request.add_header( "User-Agent", "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727)" )
                        #request.add_header( "Connection", "Keep-Alive" )
                        #request.add_header( "Accept-Encoding", "gzip, deflate" )
                        # open requested url
                        usock = urllib2.urlopen( request )
                        # close socket
                        usock.close()
                        # return valid video url
                        return url
                    except:
                        pass
            # all failed use national
            return self.BASE_VIDEO_URL % ( "national", )
        # already have a video or non US
        return video

    def fetch_hourly_forecast( self ):
        # fetch source
        htmlSource = self._fetch_data( self.BASE_FORECAST_URL % ( "hourbyhour", self.code, "", ), 15 )
        # parse source for forecast
        parser = ForecastHourlyParser( htmlSource, self.translate )
        # return forecast
        return parser.forecast

    def fetch_weekend_forecast( self ):
        # fetch source
        htmlSource = self._fetch_data( self.BASE_FORECAST_URL % ( "weekend", self.code, "", ), 15 )
        # parse source for forecast
        parser = ForecastWeekendParser( htmlSource, self.translate )
        # return forecast
        return parser.forecast

    def fetch_10day_forecast( self ):
        # fetch source
        htmlSource = self._fetch_data( self.BASE_FORECAST_URL % ( "tenday", self.code, "?dp=windsdp", ), 15 )
        # parse source for forecast
        parser = Forecast10DayParser( htmlSource, self.translate )
        # return forecast
        return parser.forecast

    def fetch_map_list( self, maptype=0, userfile=None, locationindex=None ):
        # set url
        url = self.BASE_URL + self.BASE_MAPS[ maptype ][ 1 ]
        # we handle None, local and custom map categories differently
        if ( maptype == 0 ):
            # return None if none category was selected
            return None, None
        elif ( maptype == 1 ):
            # add locale to local map list if local category
            url = url % ( "map", self.code, "", )
        # handle user definde maps special
        if ( maptype == ( len( self.BASE_MAPS ) - 1 ) ):
            # initialize our map list variable
            map_list = []
            # get correct location source
            category_title, titles, locationindex = self._get_user_file( userfile, locationindex )
            # if user file not found return None
            if ( category_title is None ):
                return None, None
            # enumerate thru and create map list
            for count, title in enumerate( titles ):
                # add title, we use an locationindex for later usage, since there is no html source to parse for images, we use count to know correct map to use
                map_list += [ ( str( count ), title[ 0 ], locationindex, ) ]
            # return results
            return category_title, map_list
        else:
            # fetch source, only refresh once a week
            htmlSource = self._fetch_data( url, 60 * 24 * 7, subfolder="maps" )
            # parse source for map list
            parser = MaplistParser( htmlSource )
            # return map list
            return None, parser.map_list

    def _get_user_file( self, userfile, locationindex ):
        # get user defined file source
        xmlSource = self._fetch_data( userfile )
        # if no source, then file moved so return
        if ( xmlSource == "" ):
            return None, None, None
        # default pattern
        pattern = "<location id=\"%s\" title=\"(.+?)\">(.+?)</location>"
        # get location, if no location for index, use default 1, which is required
        try:
            location = re.findall( pattern % ( locationindex, ), xmlSource, re.DOTALL )[ 0 ]
        except:
            # we need to set the used location id
            locationindex = "1"
            # use default "1"
            location = re.findall( pattern % ( locationindex, ), xmlSource, re.DOTALL )[ 0 ]
        # get title of maps for list and source for images
        titles = re.findall( "<map title=\"([^\"]+)\">(.+?)</map>", location[ 1 ], re.DOTALL )
        # return results
        return location[ 0 ], titles, locationindex

    def fetch_map_urls( self, map, userfile=None, locationindex=None ):
        # handle user defined maps special
        if ( map.isdigit() ):
            # convert map to int() for list index
            map = int( map )
            # get correct location source
            category_title, titles, locationindex = self._get_user_file( userfile, locationindex )
            # check if map is within the index range
            if ( map >= len( titles ) ):
                map = 0
            # grab all image urls
            urls = re.findall( "<image_url>([^<]+)</image_url>", titles[ map ][ 1 ] )
            # if image urls return results
            if ( urls ):
                # only set multi image list if more than one
                urls2 = ( [], urls, )[ len( urls ) > 1 ]
                # get a legend if it is separate from inages
                try:
                    legend = re.findall( "<legend_url>([^<]*)</legend_url>", titles[ map ][ 1 ] )[ 0 ]
                except:
                    legend = ""
                # return results
                return ( [ urls[ -1 ] ], urls2, legend, )
            # no image urls, find map urls
            map = re.findall( "<map_url>([^<]+)</map_url>", titles[ map ][ 1 ] )[ 0 ]
        # set url
        if ( map.endswith( ".html" ) ):
            url = self.BASE_URL + map
        else:
            url = self.BASE_FORECAST_URL % ( "map", self.code, "&mapdest=%s" % ( map, ), )
        # fetch source
        htmlSource = self._fetch_data( url, subfolder="maps" )
        # parse source for static map and create animated map list if available
        parser = MapParser( htmlSource )
        # return maps
        return parser.maps

    def fetch_images( self, map ):
        # are there multiple images?
        maps = map[ 1 ] or map[ 0 ]
        # initailize our return variables
        legend_path = ""
        base_path_maps = ""
        # enumerate thru and fetch images
        for count, url in enumerate( maps ):
            # used for info in progress dialog
            self.image = os.path.basename( url )
            # fetch map
            base_path_maps = self._fetch_data( url, -1 * ( count + 1 ), self.image, len( maps ) > 1, subfolder="" )
            # no need to continue if the first map of multi image map fails
            if ( base_path_maps == "" ):
                break
        # fetch legend if available
        if ( map[ 2 ] and base_path_maps != "" ):
            # fetch legend
            legend_path = self._fetch_data( map[ 2 ], -1, os.path.basename( map[ 2 ] ), False, subfolder="" )
            # we add the image filename back to path since we don't use a multiimage control
            legend_path = os.path.join( legend_path, os.path.basename( map[ 2 ] ) )
        # we return path to images or empty string if an error occured
        return base_path_maps, legend_path

    def _fetch_data( self, base_url, refreshtime=0, filename=None, animated=False, subfolder="forecasts", retry=True ):
        try:
            # set proper base path
            if ( not base_url.startswith( "http://" ) ):
                # user defined maps file
                base_path = base_url
                base_refresh_path = None
            elif ( filename is None ):
                # anything else except map/radar images (basically htmlSource)
                base_path = os.path.join( self.BASE_SOURCE_PATH, subfolder, md5.new( base_url ).hexdigest() )
                base_refresh_path = None
            else:
                # set proper path for md5 hash
                if ( animated ):
                    # animated maps include map name in base url, so don't use filename (each jpg would be in a seperate folder if you did)
                    path = os.path.dirname( base_url )
                else:
                    # non animated maps share same base url, so use full name
                    path = base_url
                # set base paths
                base_path = os.path.join( self.BASE_MAPS_PATH, subfolder, md5.new( path ).hexdigest(), filename )
                base_refresh_path = os.path.join( self.BASE_MAPS_PATH, subfolder, md5.new( path ).hexdigest(), "refresh.txt" )
            # get expiration date
            expires, refresh = self._get_expiration_date( base_path, base_refresh_path, refreshtime )
            # only fetch source if it's been longer than refresh time or does not exist
            if ( not os.path.isfile( base_path ) or refresh ):
                # request base url
                request = urllib2.Request( base_url )
                print base_url
                # add a faked header
                request.add_header( "User-Agent", "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727)" )
                #request.add_header( "Connection", "Keep-Alive" )
                #request.add_header( "Accept-Encoding", "gzip, deflate" )
                # open requested url
                usock = urllib2.urlopen( request )
                print usock.info()
                # get expiration
                try:
                    expires = time.mktime( time.strptime( usock.info()[ "expires" ], "%a, %d %b %Y %H:%M:%S %Z" ) )
                except:
                    expires = -1
            else:
                # open saved source
                usock = open( base_path, "rb" )
            # read source
            data = usock.read()
            # close socket
            usock.close()
            # save the data
            if ( not os.path.isfile( base_path ) or refresh ):
                self._save_data( data, base_path )
            # save the refresh.txt file
            if ( base_refresh_path is not None and ( not animated or ( animated and refreshtime == -5 ) ) and refresh ):
                self._save_data( str( expires ), base_refresh_path )
            if ( base_refresh_path ):
                data = os.path.dirname( base_path )
            # return results
            return data
        except urllib2.HTTPError, e:
            # if error 503 and this is the first try, recall function after sleeping, otherwise return ""
            if ( e.code == 503 and retry ):
                # TODO: this is so rare, but try and determine if 3 seconds is enogh
                print "Trying url %s one more time." % base_url
                time.sleep( 3 )
                # try one more time
                return self._fetch_data( base_url, refreshtime, filename, animated, subfolder, False )
            else:
                # we've already retried, return ""
                print "Second error 503 for %s, increase sleep time." % base_url
                return ""
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            # some unknown error, return ""
            return ""

    def _get_expiration_date( self, base_path, base_refresh_path, refreshtime ):
        try:
            # get the data files date if it exists
            try:
                date = time.mktime( time.gmtime( os.path.getmtime( base_path ) ) )
            except:
                date = 0
            # set default expiration date
            expires = date + ( refreshtime * 60 )
            # if the path to the data file does not exist create it
            if ( base_refresh_path is not None and os.path.isfile( base_refresh_path ) ):
                # open data path for writing
                file_object = open( base_refresh_path, "rb" )
                # read expiration date
                expires = float( file_object.read() )
                # close file object
                file_object.close()
            # see if necessary to refresh source
            refresh = ( ( time.mktime( time.gmtime() ) * ( refreshtime != 0 ) ) > expires )
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
        # return expiration date
        return expires, refresh

    def _save_data( self, data, data_path ):
        try:
            # if the path to the data file does not exist create it
            if ( not os.path.isdir( os.path.dirname( data_path ) ) ):
                os.makedirs( os.path.dirname( data_path ) )
            # open data path for writing
            file_object = open( data_path, "wb" )
            # write htmlSource
            file_object.write( data )
            # close file object
            file_object.close()
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )

if ( __name__ == "__main__" ):
    code = "USME0013"#"USMI0564"#"USHI0026"#"USMI0229"#"USWA0441"#"USAK0025"#"USOR0111"#"USAK0001"#"USAK0025"#"USMI0229"#"USMI0004"#"USND0037"#"JAXX0085"#"USNY0996"#"USOR0111"#"USOR0098"#"USGA0028"#"USAR0170"#"NZXX0006"#"USMI0405"#"USMI0508"#"NZXX0006"#"CAXX0343"#
    client = WeatherClient( code, translate="" )
    MAP_TYPE = 2
    MAP_NO = 2
    print "MAP LIST - %s" % client.BASE_MAPS[MAP_TYPE][0]
    category_title, map_list = client.fetch_map_list( MAP_TYPE, r"F:\source\_XBMC-Linux_\plugins\weather\weather.com plus\resources\samples\sample-user-defined-maps.udm", "1" )
    print "CT", category_title
    #for map in map_list:
    #    print '            <map title="%s">' % map[ 1 ]
    #    print '                <map_url>%s</map_url>' % map[ 0 ]
    #    print '            </map>'
    print "MAP URLS", map_list[ MAP_NO ]
    maps = client.fetch_map_urls( map_list[ MAP_NO ][ 0 ], r"F:\source\_XBMC-Linux_\plugins\weather\weather.com plus\resources\samples\sample-user-defined-maps.udm", map_list[ MAP_NO ][ 2 ] )
    print
    print maps
    print "IMAGES"
    mapspath, legendpath = client.fetch_images( maps )
    print "maps", mapspath
    print "legend", legendpath
    """
    print
    print"36 HOUR FORECAST"
    alerts, alertsrss, alertsnotify, alertscolor, alertscount, forecasts, extras, video = client.fetch_36_forecast( "movie.flv" )
    print extras
    print video
    print "AN", alertsnotify +":"
    print "AH", alertsrss
    for forecast in forecasts:
        print repr(forecast)
    print
    print "HOUR BY HOUR"
    forecasts = client.fetch_hourly_forecast()
    for forecast in forecasts:
        print forecast
    print
    print "10 DAY"
    forecasts = client.fetch_10day_forecast()
    for forecast in forecasts:
        print forecast
    print
    print "WEEKEND FORECAST"
    forecasts = client.fetch_weekend_forecast()
    for forecast in forecasts:
        print repr(forecast)
    #temp = _localize_unit( "8:21 AM", "time" )
    #print temp
    #text = _translate_text( "Sun|Mon|Tue|Wed|Thu|Fri|Sat|T-Storms|Late Snow showers|Sunset", "en_fr" )
    #print text
"""