if ( __name__ == "__main__" ):
    code = "USMI0229"#"USMI0004"#"USND0037"#"JAXX0085"#"USMI0564"#"USWA0441"#"USNY0996"#"USOR0111"#"USOR0098"#"USGA0028"#"USAR0170"#"NZXX0006"#"USMI0405"#"USMI0508"#"NZXX0006"#"CAXX0343"#
    client = WeatherClient( code, translate="" )
    """
    print"36 HOUR FORECAST"
    alerts, alertsrss, alertsnotify, alertscolor, alertscount, forecasts, video = client.fetch_36_forecast( "movie.flv" )
    print video
    print "AN", alertsnotify +":"
    print "AH", alertsrss
    for forecast in forecasts:
        print repr(forecast)
    MAP_TYPE = 64
    MAP_NO = 0
    print "MAP LIST - %s" % client.BASE_MAPS[MAP_TYPE][0]
    category_title, map_list = client.fetch_map_list( MAP_TYPE, r"F:\source\XBMC-Linux\plugins\weather\weather.com plus\resources\samples\sample user defined maps.udm", "3" )
    print "CT", category_title
    for map in map_list:
        print map
    print "MAP URLS", map_list[ MAP_NO ]
    maps = client.fetch_map_urls( map_list[ MAP_NO ][ 0 ], r"F:\source\XBMC-Linux\plugins\weather\weather.com plus\resources\samples\sample user defined maps.udm", map_list[ MAP_NO ][ 2 ] )
    print
    print maps
    print "IMAGES"
    mapspath, legendpath = client.fetch_images( maps )
    print "maps", mapspath
    print "legend", legendpath
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
    """
    print "WEEKEND FORECAST"
    forecasts = client.fetch_weekend_forecast()
    for forecast in forecasts:
        print repr(forecast)
    #temp = _localize_unit( "8:21 AM", "time" )
    #print temp
    #text = _translate_text( "Sun|Mon|Tue|Wed|Thu|Fri|Sat|T-Storms|Late Snow showers|Sunset", "en_fr" )
    #print text
