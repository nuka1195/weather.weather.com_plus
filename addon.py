## Weather.com+

import sys
import xbmcaddon

# Addon class
Addon = xbmcaddon.Addon( id="script.weather.com.plus" )


if ( __name__ == "__main__" ):
    # is this a request from user to log properties
    if ( sys.argv[ 1 ] == "properties" ):
        # get property printer module
        from xbmcweather import pprinter
        # print properties
        pprinter.PPrinter( addon=Addon ).print_properties()
    # is this a request from user to select new town
    elif sys.argv[ 1 ].startswith( "search" ):
        # get search module
        from xbmcweather import search
        # search for town
        search.TownSearch( addon=Addon, index=sys.argv[ 1 ].replace( "search", "" ) ).get_town()
    # standard weather fetcher
    else:
        # get weather module
        from resources.lib import weather
        # is this a map selection?
        if ( sys.argv[ 1 ].startswith( "map=" ) ):
            # fetch map
            weather.Weather( addon=Addon ).fetch_map( sys.argv[ 1 ] )
        else:
            # fetch weather
            weather.Weather( addon=Addon, index=sys.argv[ 1 ], refresh=sys.argv[ 2 ] == "1" ).fetch_weather()
