## Utilities for localizing weather forecasts
# -*- coding: UTF-8 -*-

import xbmc
import urllib
import re
import time


class Localize:
    """
        Class for localizing text and values.
    """

    def __init__( self, localize ):
        # set our localize functions
        self.localize_unit = localize.localize_unit

    # TODO: maybe use xbmc language strings for brief outlook translation
    def _translate_text( self, text, translate ):
        # base babelfish url
        url = "http://babelfish.yahoo.com/translate_txt"
        try:
            # hack for translating T-Storms, TODO: verify if this is necessary
            text = text.replace( "T-Storms", "Thunderstorms" )
            # data dictionary
            data = { "ei": "UTF-8", "doit": "done", "fr": "bf-home", "intl": "1", "tt": "urltext", "trtext": text, "lp": translate, "btnTrTxt": "Translate" }
            # request url
            request = urllib2.Request( url, urlencode( data ) )
            # add a faked header, we use ie 8.0. it gives correct results for regex
            request.add_header( "User-Agent", "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727)" )
            # read htmlSource
            htmlSource = urllib2.urlopen( request ).read()
            # find translated text
            text = re.search( "<div id=\"result\"><div style=\"[^\"]+\">([^<]+)", htmlSource ).group( 1 )
        except Exception, e:
            # TODO: add error checking?
            pass
        # return translated text
        return text

    def _normalize_outlook( self, outlook ):
        # set temperature and speed unit
        tempunit = xbmc.getRegion( id="tempunit" )
        speedunit = xbmc.getRegion( id="speedunit" )
        # enumerate thru and localize values
        for count, tmp_outlook in enumerate( outlook ):
            if ( tempunit != "°F" ):
                # find all temps
                temps = re.findall( "[0-9]+F", tmp_outlook )
                for temp in temps:
                    tmp_outlook = re.sub( temp, self.localize_unit( temp ) + tempunit, tmp_outlook, 1 )
                # calculate the localized temp ranges if C is required
                temps = re.findall( "[low|mid|high]+ [0-9]+s", tmp_outlook )
                add = { "l": 3, "m": 6, "h": 9 }
                for temp in temps:
                    new_temp = self.localize_unit( str( int( re.search( "[0-9]+", temp ).group( 1 ) ) + add.get( temp[ 0 ], 3 ) ) )
                    temp_int = int( float( new_temp ) / 10 ) * 10
                    temp_rem = int( float( new_temp ) % 10 )
                    temp_text = [ "low %ds", "mid %ds", "high %ds" ][ ( temp_rem >= 4 ) + ( temp_rem >= 6 ) ]
                    tmp_outlook = re.sub( temp, temp_text % ( temp_int, ), tmp_outlook, 1 )
            if ( speedunit != "mph" ):
                # calculate the localized wind if C is required
                winds = re.findall( "[0-9]+ to [0-9]+ mph", tmp_outlook )
                for wind in winds:
                    speeds = re.findall( "[0-9]+", wind )
                    for speed in speeds:
                        wind = re.sub( speed, self.localize_unit( speed, "speed" ).split( " " )[ 0 ], wind, 1 )
                    tmp_outlook = re.sub( "[0-9]+ to [0-9]+ mph", wind.replace( "mph", speedunit ), tmp_outlook, 1 )
            # add our text back to the main variable
            outlook[ count ] = tmp_outlook
        # return normalized text
        return outlook
