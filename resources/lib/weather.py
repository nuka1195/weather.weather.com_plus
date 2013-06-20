## Enhanced weather addon for www.weather.com

import sys
import os
import xbmc
import xbmcgui
"""
from threading import Thread
"""
from urllib import quote, unquote
from WeatherClient import WeatherClient



class Weather:
    """
        Fetches weather info from weather.com and
        sets window properties for skinners to use.
    """
    # weather window for setting weather properties
    WINDOW = xbmcgui.Window( 12600 )

    def __init__( self, addon, index=None, refresh=True ):
        # set Addon
        self.Addon = addon
        # set area code, used to fetch proper weather info
        if ( index is None ):
            self.index = xbmc.getInfoLabel( "Window(Weather).Property(Location.Index)" )
        else:
            self.index = index
        # set weather.com code, used to fetch proper weather info
        self.location_id = self.Addon.getSetting( "id%s" % ( self.index, ) )
        # set force refresh
        self.refresh = refresh
        # get our WeatherClient
        self._get_client()

    def fetch_map( self, args ):
        # parse sys.argv for params
        params = dict( unquote( arg ).split( "=" ) for arg in args.split( "&" ) )
        # fetch map
        self._fetch_map( params[ "map" ], params[ "title" ], xbmc.getInfoLabel( "Window(Weather).Property(Location.Index)" ) )#params[ "location" ] )
        # we're finished, exit
        self._exit_script()

    def fetch_weather( self ):
        # log started action
        self._log_addon_action( "started" )
        # clear key properties if new location
        self._clear_properties()
        # initialize our thread list
        """
        thread_list = []
        # get our 36 hour forecast
        current = FetchInfo( self._fetch_current_conditions )
        thread_list += [ current ]
        current.start()
        # get our hour by hour forecast
        current = FetchInfo( self._fetch_hourly_forecast )
        thread_list += [ current ]
        current.start()
        # get our weekend forecast
        current = FetchInfo( self._fetch_weekend_forecast )
        thread_list += [ current ]
        current.start()
        # get our 10 day forecast
        current = FetchInfo( self._fetch_10day_forecast )
        thread_list += [ current ]
        current.start()
        # get our map list and default map
        current = FetchInfo( self._fetch_map_list )
        thread_list += [ current ]
        current.start()
        # join our threads with the main thread
        for thread in thread_list:
           thread.join()
        """
        # standard current weather info
        msg = self._fetch_current_conditions()
        self._fetch_map_list()
        self._fetch_36hour_forecast()
        self._fetch_videos()
        self._fetch_weekend_forecast()
        self._fetch_hourly_forecast()
        self._fetch_10day_forecast()
        self.WINDOW.setProperty( "Weather.IsFetched", msg )
        # we're finished, exit
        self._exit_script()

    def _log_addon_action( self, action ):
        # log addon info
        xbmc.log( "=" * 80, xbmc.LOGNOTICE )
        xbmc.log( "[ADD-ON] - %s %s!" % ( self.Addon.getAddonInfo( "Name" ), action, ), xbmc.LOGNOTICE )
        xbmc.log( "           Id: %s - Type: %s - Version: %s" % ( self.Addon.getAddonInfo( "Id" ), self.Addon.getAddonInfo( "Type" ), self.Addon.getAddonInfo( "Version" ) ), xbmc.LOGNOTICE )
        xbmc.log( "=" * 80, xbmc.LOGNOTICE )

    def _get_client( self ):
        # do we want to translate?
        self.settings = { "translate": [ "en", xbmc.getRegion( "locale" ) ][ self.Addon.getSetting( "translate" ) == "true" ] }
        # get area code
        if ( self.index is None ):
            self.areacode = xbmc.getInfoLabel( "Window(Weather).Property(Location.Index)" )
        else:
            self.areacode = self.index
        # set if new location
        self.new_location = ( xbmc.getInfoLabel( "Window(Weather).Property(Weather.AreaCode)" ) != self.areacode )
        # if new location, set it
        if ( self.new_location ):
            self.WINDOW.setProperty( "Weather.AreaCode", self.areacode )
        # setup our weather client
        self.WeatherClient = WeatherClient( self.location_id, self.Addon )

    def _set_maps_path( self, status="loading", maps_path="script.weather.com.plus/loading", legend_path="" ):
        # we have three possibilities. loading (default), error or the actual map path
        self.WINDOW.setProperty( "MapsStatus", status )
        self.WINDOW.setProperty( "MapsPath", maps_path )
        self.WINDOW.setProperty( "MapsLegendPath", legend_path )

    def _clear_properties( self ):
        # clear properties used for visibility
        self.WINDOW.setProperty( "36Hour.IsEnabled", self.Addon.getSetting( "forecast_36hour" ) )
        self.WINDOW.setProperty( "Weekend.IsEnabled", self.Addon.getSetting( "forecast_weekend" ) )
        self.WINDOW.setProperty( "Hourly.IsEnabled", self.Addon.getSetting( "forecast_hourly" ) )
        self.WINDOW.setProperty( "10Day.IsEnabled", self.Addon.getSetting( "forecast_10day" ) )
        self.WINDOW.setProperty( "Maps.IsEnabled", self.Addon.getSetting( "forecast_maps" ) )
        self.WINDOW.setProperty( "Videos.IsEnabled", self.Addon.getSetting( "forecast_videos" ) )
        self.WINDOW.clearProperty( "Alerts" )
        self.WINDOW.setProperty( "Alerts.Color", "default" )
        self.WINDOW.clearProperty( "Video.National.Url" )
        self.WINDOW.clearProperty( "Video.Regional.Url" )
        self.WINDOW.clearProperty( "Video.Local.Url" )
        self.WINDOW.clearProperty( "Video.Storm.Url" )
        self.WINDOW.setProperty( "36Hour.IsFetched", "false" )
        self.WINDOW.setProperty( "Weekend.IsFetched", "false" )
        self.WINDOW.setProperty( "Hourly.IsFetched", "false" )
        self.WINDOW.setProperty( "10Day.IsFetched", "false" )
        self.WINDOW.setProperty( "Maps.IsFetched", "false" )
        self.WINDOW.setProperty( "Videos.IsFetched", "false" )

    def _clear_map_list( self, list_id ):
        # enumerate thru and clear all map list labels, icons and onclicks
        for count in range( 1, 31 ):
            # these are what the user sees and the action the button performs
            self.WINDOW.clearProperty( "MapList.%d.MapLabel.%d" % ( list_id, count, ) )
            self.WINDOW.clearProperty( "MapList.%d.MapLabel2.%d" % ( list_id, count, ) )
            self.WINDOW.clearProperty( "MapList.%d.MapIcon.%d" % ( list_id, count, ) )
            self.WINDOW.clearProperty( "MapList.%d.MapOnclick.%d" % ( list_id, count, ) )
        # set the default titles
        self._set_map_list_titles( list_id )

    def _set_map_list_titles( self, list_id, short_title=None, long_title=None ):
        # set map list titles for skinners buttons
        if ( short_title is None ):
            # non user defined list
            short_title = self.Addon.getSetting( "maplist%d" % ( list_id, ) )
            if ( short_title.find( "(" ) >= 0 ):
                short_title = short_title[ short_title.find( "(" ) + 1 : -1 ]
            long_title = self.Addon.getSetting( "maplist%d" % ( list_id, ) )
        # now set the titles
        self.WINDOW.setProperty( "MapList.%d.ShortTitle" % ( list_id, ), short_title )
        self.WINDOW.setProperty( "MapList.%d.LongTitle" % ( list_id, ), long_title )

    def _fetch_map_list( self ):
        # exit script if user changed locations
        if ( self.Addon.getSetting( "forecast_maps" ) != "true" ): return
        # intialize our download variable, we use this so we don't re-download same info
        map_download = []
        # enumerate thru and clear our properties if map is different (if user changed setiings), local and user defined list should be downloaded if location changed
        for count in range( 1, 4 ):
            # do we need to download this list?
            map_download += [ 
                ( self.new_location and ( self.Addon.getSetting( "maplist%d" % ( count, ) ) == "Local" or self.Addon.getSetting( "maplist%d" % ( count, ) ) == "User Defined" ) ) or 
                ( self.WINDOW.getProperty( "MapList.%d.LongTitle" % ( count, ) ) != self.Addon.getSetting( "maplist%d" % ( count, ) ) )
            ]
            # do we need to clear the info?
            if ( map_download[ count - 1 ] ):
                self._clear_map_list( count )
        # we set this here in case we do not need to download new lists
        current_map = self.WINDOW.getProperty( "Weather.CurrentMapUrl" )
        current_map_title = self.WINDOW.getProperty( "Weather.CurrentMap" )
        # only run if any new map lists
        if ( True in map_download ):
            # we set our maps path property to loading images while downloading
            self._set_maps_path()
            # set default map, we allow skinners to have users set this with a skin string
            # FIXME: look at this, seems wrong, when changing locations maps can fail to load.
            default = (
                self.WINDOW.getProperty( "Weather.CurrentMap" ),
                xbmc.getInfoLabel( "Skin.String(TWC.DefaultMap)" ),
            )[ xbmc.getInfoLabel( "Skin.String(TWC.DefaultMap)" ) != "" and self.WINDOW.getProperty( "Weather.CurrentMap" ) == "" ]
            # get localized map categories
            categories = [ self.Addon.getLocalizedString( id ) for id in range( 30900, 30965 ) ]
            # enumurate thru map lists and fetch map list
            for maplist_count in range( 1, 4 ):
                # only fetch new list if required
                if ( not map_download[ maplist_count - 1 ] ): continue
                # get the correct category
                try:
                    map_category = categories.index( self.Addon.getSetting( "maplist%d" % ( maplist_count, ) ) ) + 30900
                except:
                    map_category = 30901
                # fetch map list
                category_title, maps = self.WeatherClient.fetch_map_list( map_category, self.Addon.getSetting( "maplist%d_user_file" % ( maplist_count, ) ), xbmc.getInfoLabel( "Window(Weather).Property(Location.Index)" ) )
                # only run if maps were found
                if ( maps is None ): continue
                # set a current_map in case one isn't set
                if ( current_map == "" ):
                    current_map = maps[ 0 ][ 0 ]
                    current_map_title = maps[ 0 ][ 1 ]
                # if user defined map list set the new titles
                if ( category_title is not None ):
                    self._set_map_list_titles( maplist_count, category_title, category_title )
                # enumerate thru our map list and add map and title and check for default
                for count, map in enumerate( maps ):
                    # create our label, icon and onclick event
                    self.WINDOW.setProperty( "MapList.%d.MapLabel.%d" % ( maplist_count, count + 1, ), map[ 1 ] )
                    self.WINDOW.setProperty( "MapList.%d.MapLabel2.%d" % ( maplist_count, count + 1, ), map[ 0 ] )
                    self.WINDOW.setProperty( "MapList.%d.MapIcon.%d" % ( maplist_count, count + 1, ), os.path.join( xbmc.getInfoLabel( "Skin.String(TWC.MapsIconPath)" ), map[ 1 ].replace( ":", "" ).replace( "/", " - " ) + ".jpg" ) )
                    self.WINDOW.setProperty( "MapList.%d.MapOnclick.%d" % ( maplist_count, count + 1, ), "XBMC.RunScript(%s,map=%s&title=%s&location=%s)" % ( sys.argv[ 0 ], map[ 0 ], quote( map[ 1 ] ), str( map[ 2 ] ) ) )
                    # if we have a match, set our class variable
                    if ( map[ 1 ] == default ):
                        current_map = map[ 0 ]
                        current_map_title = map[ 1 ]
        # fetch the current map
        self._fetch_map( current_map, current_map_title, xbmc.getInfoLabel( "Window(Weather).Property(Location.Index)" ) )

    def _fetch_map( self, map, title, locationindex=None ):
        # exit script if user changed locations
        ##if ( self.areacode != xbmc.getInfoLabel( "Window(Weather).Property(Location.Index)" ) ): return
        # we set our maps path property to loading images while downloading
        self._set_maps_path()
        # we set Weather.CurrentMap and Weather.CurrentMapUrl, the skin can handle it when the user selects a new map for immediate update
        self.WINDOW.setProperty( "Weather.CurrentMap", title )
        self.WINDOW.setProperty( "Weather.CurrentMapUrl", map )
        # fetch the available map urls
        maps = self.WeatherClient.fetch_map_urls( map, self.Addon.getSetting( "maplist%s_user_file" % ( locationindex, ) ), locationindex )
        # fetch the images
        maps_path, legend_path = self.WeatherClient.fetch_images( maps )
        # hack incase the weather in motion link was bogus
        if ( maps_path == "" and len( maps[ 1 ] ) ):
            maps_path, legend_path = self.WeatherClient.fetch_images( ( maps[ 0 ], [], maps[ 2 ], ) )
        # now set our window properties so multi image will display images
        self._set_maps_path( 
            status = [ "loaded", "error" ][ maps_path == "" ],
            maps_path = [ maps_path, "script.weather.com.plus/error" ][ maps_path == "" ],
            legend_path = [ legend_path, "" ][ maps_path == "" ]
        )

    def _set_alerts( self, alerts, alertsrss, alertsnotify, alertscolor, alertscount ):
        # send notification if user preference and there are alerts
        if ( alerts != "" and ( int( self.Addon.getSetting( "alert_notify_type" ) ) == 1 or
            ( alertscolor == "red" and int( self.Addon.getSetting( "alert_notify_type" ) ) > 1 ) or 
            ( alertscolor == "orange" and int( self.Addon.getSetting( "alert_notify_type" ) ) == 3 ) ) and
            ( self.Addon.getSetting( "alert_notify_once" ) == "false" or self.WINDOW.getProperty( "Alerts.RSS" ) != alertsrss )
        ):
            xbmc.executebuiltin( "XBMC.Notification(%s,\"%s\",%d,script.weather.com.plus/alert-%s.png)" % ( self.Addon.getLocalizedString( 30799 ), alertsnotify, int( float( self.Addon.getSetting( "alert_notify_time" ) ) ) * 1000, alertscolor, ) )
        # set any alerts
        self.WINDOW.setProperty( "Alerts", self.translate_text( alerts, self.settings[ "translate" ] ) )
        self.WINDOW.setProperty( "Alerts.RSS", self.translate_text( alertsrss, self.settings[ "translate" ] ) )
        self.WINDOW.setProperty( "Alerts.Color", ( "default", alertscolor, )[ alerts != "" ] )
        self.WINDOW.setProperty( "Alerts.Count", ( "", str( alertscount ), )[ alertscount > 1 ] )
        self.WINDOW.setProperty( "Alerts.Label", xbmc.getLocalizedString( 33049 + ( alertscount > 1 ) ) )

    def _fetch_videos( self ):
        # exit script if user changed locations
        if ( self.Addon.getSetting( "forecast_videos" ) != "true" ): return
        try:
            # set success message
            msg = "true"
            # set video
            nvideo = self.WINDOW.getProperty( "Video.National.Url" ) or self.Addon.getSetting( "video_national%s" % ( xbmc.getInfoLabel( "Window(Weather).Property(Location.Index)" ), ) )
            nthumb = self.WINDOW.getProperty( "Video.National.Thumbnail" )
            rvideo = self.WINDOW.getProperty( "Video.Regional.Url" ) or ( "northeast", "northwest", "southeast", "southwest", "south", "west", "hawaii", "alaska", )[ int( self.Addon.getSetting( "video_regional%s" % ( xbmc.getInfoLabel( "Window(Weather).Property(Location.Index)" ), ) ) ) ]
            rthumb = self.WINDOW.getProperty( "Video.Regional.Thumbnail" )
            lvideo = self.WINDOW.getProperty( "Video.Local.Url" ) or self.Addon.getSetting( "video_local%s" % ( xbmc.getInfoLabel( "Window(Weather).Property(Location.Index)" ), ) )
            lthumb = self.WINDOW.getProperty( "Video.Local.Thumbnail" )
            svideo = self.WINDOW.getProperty( "Video.Storm.Url" )
            sthumb = self.WINDOW.getProperty( "Video.Storm.Thumbnail" )
            # fetch videos
            videos = self.WeatherClient.fetch_videos( videos=[ [ nvideo, nthumb ], [ rvideo, rthumb ], [ lvideo, lthumb ], [ svideo, sthumb ] ] )
            # set our different video urls
            self.WINDOW.setProperty( "Video.National.Url", videos[ 0 ][ 0 ] )
            self.WINDOW.setProperty( "Video.National.Thumbnail", videos[ 0 ][ 1 ] )
            self.WINDOW.setProperty( "Video.Regional.Url", videos[ 1 ][ 0 ] )
            self.WINDOW.setProperty( "Video.Regional.Thumbnail", videos[ 1 ][ 1 ] )
            self.WINDOW.setProperty( "Video.Local.Url", videos[ 2 ][ 0 ] )
            self.WINDOW.setProperty( "Video.Local.Thumbnail", videos[ 2 ][ 1 ] )
            self.WINDOW.setProperty( "Video.Storm.Url", videos[ 3 ][ 0 ] )
            self.WINDOW.setProperty( "Video.Storm.Thumbnail", videos[ 3 ][ 1 ] )
        except:
            # set error message
            msg = "error"
        # used for visibility
        self.WINDOW.setProperty( "Videos.IsFetched", msg )

    def _fetch_current_conditions( self ):
        # get standard weather module
        from xbmcweather import weather, localize
        # get localize functions
        l = localize.Localize()
        # set localize functions
        self.localize_unit = l.localize_unit
        self.localize_text = l.localize_text
        self.localize_text_special = l.localize_text_special
        self.translate_text = l.translate_text
        # fetch weather
        return weather.Weather( addon=self.Addon, index=self.index, refresh=self.refresh, localize=l ).fetch_weather()

    def _fetch_36hour_forecast( self ):
        # exit script if user changed locations
        if ( self.Addon.getSetting( "forecast_36hour" ) != "true" ): return
        try:
            # set success message
            msg = "true"
            # fetch 36 hour forecast
            alerts, alertsrss, alertsnotify, alertscolor, alertscount, forecasts = self.WeatherClient.fetch_36hour_forecast()
            # set any alerts
            self._set_alerts( alerts, alertsrss, alertsnotify, alertscolor, alertscount )
            # translate text
            #[('Tonight', '29', 'Partly Cloudy', 'Low', '34', '10', ('ENE', '4'), '87', ['--'], 'A few clouds. Low 34F. Winds light and variable.', 'Sunset', '5:16 pm'), ('Tomorrow', '30', 'Partly Cloudy', 'High', '61', '20', ('E', '10'), '68', ['2', 'Low'], 'Partly cloudy. High 61F. Winds E at 5 to 10 mph.', 'Sunrise', '7:21 am'), ('Tomorrow Night', '11', 'Showers', 'Low', '39', '40', ('SSE', '10'), '81', ['--'], 'Showers early becoming less numerous late. Low 39F. Winds SSE at 5 to 10 mph. Chance of rain 40%.', 'Sunset', '5:15 pm')]

            ##if ( xbmc.getRegion( "locale" ) != "en" and self.Addon.getSetting( "translate_google" ) == "true" ):
            ##    translated_forecasts = [ self.translate_text( [ forecast[ 0 ], forecast[ 2 ], forecast[ 3 ], forecast[ 6 ][ 0 ], forecast[ 8 ][ -1 ], forecast[ 9 ], forecast[ 10 ] ], xbmc.getRegion( "locale" ) ) for forecast in forecasts ]
            ##    #translated_forecasts = self.translate_text( translated_forecasts, xbmc.getRegion( "locale" ) )
            ##    print translated_forecasts
            ##    #forecasts = eval( self.translate_text( repr( forecasts ), xbmc.getRegion( "locale" ) ) )
            # enumerate thru and set the info
            for day, forecast in enumerate( forecasts ):
                self.WINDOW.setProperty( "36Hour.%d.OutlookIcon" % ( day + 1, ), os.path.join( self.Addon.getSetting( "icon_path_weather" ), forecast[ 1 ] + ".png" ) )
                self.WINDOW.setProperty( "36Hour.%d.FanartCode" % ( day + 1, ), forecast[ 1 ] )
                self.WINDOW.setProperty( "36Hour.%d.Outlook" % ( day + 1, ), " ".join( [ self.localize_text.get( word, word ) for word in forecast[ 2 ].split( " " ) if ( word ) ] ) )
                self.WINDOW.setProperty( "36Hour.%d.TemperatureColor" % ( day + 1, ), forecast[ 3 ].lower() )
                self.WINDOW.setProperty( "36Hour.%d.TemperatureHeading" % ( day + 1, ), self.localize_text.get( forecast[ 3 ], forecast[ 3 ] ) )
                self.WINDOW.setProperty( "36Hour.%d.Temperature" % ( day + 1, ), self.localize_unit( forecast[ 4 ] ) )
                self.WINDOW.setProperty( "36Hour.%d.Precipitation" % ( day + 1, ), forecast[ 5 ] )
                self.WINDOW.setProperty( "36Hour.%d.Wind" % ( day + 1, ), self.localize_unit( forecast[ 6 ][ 1 ], "wind", direction=forecast[ 6 ][ 0 ] ) )
                self.WINDOW.setProperty( "36Hour.%d.WindLong" % ( day + 1, ), self.localize_unit( forecast[ 6 ][ 1 ], "wind", direction=forecast[ 6 ][ 0 ], long=True ) )
                self.WINDOW.setProperty( "36Hour.%d.WindDirection" % ( day + 1, ), self.localize_text_special.get( forecast[ 6 ][ 0 ], [ forecast[ 6 ][ 0 ] ] )[ 0 ] )
                self.WINDOW.setProperty( "36Hour.%d.WindDirectionLong" % ( day + 1, ), self.localize_text_special.get( forecast[ 6 ][ 0 ], [ forecast[ 6 ][ 0 ] ] )[ -1 ] )
                self.WINDOW.setProperty( "36Hour.%d.WindSpeed" % ( day + 1, ), self.localize_unit( forecast[ 6 ][ 1 ], "speed" ) )
                self.WINDOW.setProperty( "36Hour.%d.Humidity" % ( day + 1, ), forecast[ 7 ] )
                self.WINDOW.setProperty( "36Hour.%d.UVIndex" % ( day + 1, ), "%s %s" % ( forecast[ 8 ][ 0 ], self.localize_text.get( forecast[ 8 ][ -1 ], forecast[ 8 ][ -1 ] ), ) )
                self.WINDOW.setProperty( "36Hour.%d.Forecast" % ( day + 1, ), forecast[ 9 ] )##translated_forecasts[ day ][ 5 ].strip() )##
                self.WINDOW.setProperty( "36Hour.%d.DaylightTitle" % ( day + 1, ), self.localize_text.get( forecast[ 10 ], forecast[ 10 ] ) )
                self.WINDOW.setProperty( "36Hour.%d.DaylightTime" % ( day + 1, ), self.localize_unit( forecast[ 11 ], "time" ) )
                self.WINDOW.setProperty( "36Hour.%d.DaylightType" % ( day + 1, ), ( "sunrise", "sunset", )[ forecast[ 10 ] == "Sunset" ] )
                self.WINDOW.setProperty( "36Hour.%d.Title" % ( day + 1, ), self.localize_text.get( forecast[ 0 ], forecast[ 0 ] ) )
        except:
            import traceback
            traceback.print_exc()
            # set error message
            msg = "error"
        # use this to hide info until fully fetched
        self.WINDOW.setProperty( "36Hour.IsFetched", msg )

    def _fetch_hourly_forecast( self ):
        # exit script if user changed locations
        if ( self.Addon.getSetting( "forecast_hourly" ) != "true" ): return
        try:
            # set success message
            msg = "true"
            # fetch hourly forecast
            forecasts = self.WeatherClient.fetch_hourly_forecast()
            # enumerate thru and set the info
            for hour, forecast in enumerate( forecasts ):
                # set properties
                self.WINDOW.setProperty( "Hourly.%d.Time" % ( hour + 1, ), self.localize_unit( forecast[ 0 ], "time", hours=True ) )
                self.WINDOW.setProperty( "Hourly.%d.Date" % ( hour + 1, ), self.localize_unit( forecast[ 1 ], "monthdate", long=True ) )
                self.WINDOW.setProperty( "Hourly.%d.DateShort" % ( hour + 1, ), self.localize_unit( forecast[ 1 ], "monthdate" ) )
                self.WINDOW.setProperty( "Hourly.%d.OutlookIcon" % ( hour + 1, ), os.path.join( self.Addon.getSetting( "icon_path_weather" ), forecast[ 2 ] + ".png" ) )
                self.WINDOW.setProperty( "Hourly.%d.FanartCode" % ( hour + 1, ), forecast[ 2 ] )
                self.WINDOW.setProperty( "Hourly.%d.Outlook" % ( hour + 1, ), " ".join( [ self.localize_text.get( word, word ) for word in forecast[ 4 ].split( " " ) if ( word ) ] ) )
                self.WINDOW.setProperty( "Hourly.%d.Temperature" % ( hour + 1, ), self.localize_unit( forecast[ 3 ] ) )
                self.WINDOW.setProperty( "Hourly.%d.FeelsLike" % ( hour + 1, ), self.localize_unit( forecast[ 5 ] ) )
                self.WINDOW.setProperty( "Hourly.%d.Precipitation" % ( hour + 1, ), forecast[ 6 ] )
                self.WINDOW.setProperty( "Hourly.%d.Humidity" % ( hour + 1, ), forecast[ 7 ] )
                self.WINDOW.setProperty( "Hourly.%d.Wind" % ( hour + 1, ), self.localize_unit( forecast[ 9 ], "wind", direction=forecast[ 8 ], split=True ) )
                self.WINDOW.setProperty( "Hourly.%d.WindLong" % ( hour + 1, ), self.localize_unit( forecast[ 9 ], "wind", direction=forecast[ 8 ], long=True, split=True ) )
                self.WINDOW.setProperty( "Hourly.%d.WindDirection" % ( hour + 1, ), self.localize_text_special.get( forecast[ 8 ], [ forecast[ 8 ] ] )[ 0 ] )
                self.WINDOW.setProperty( "Hourly.%d.WindDirectionLong" % ( hour + 1, ), self.localize_text_special.get( forecast[ 8 ], [ forecast[ 8 ] ] )[ -1 ] )
                self.WINDOW.setProperty( "Hourly.%d.WindSpeed" % ( hour + 1, ), self.localize_unit( forecast[ 9 ], "speed" ) )
                self.WINDOW.setProperty( "Hourly.%d.Sunrise" % ( hour + 1, ), self.localize_unit( forecast[ 10 ], "time" ) )
                self.WINDOW.setProperty( "Hourly.%d.Sunset" % ( hour + 1, ), self.localize_unit( forecast[ 11 ], "time" ) )
        except:
            # set error message
            msg = "error"
            # set to empty to clear properties
            forecasts = []
        # enumerate thru and clear all hourly times
        for hour in range( len( forecasts ), 12 ):
            # clear any remaining hourly times as some locals do not have all of them
            self.WINDOW.clearProperty( "Hourly.%d.Time" % ( hour + 1, ) )
        # use this to hide info until fully fetched
        self.WINDOW.setProperty( "Hourly.IsFetched", msg )

    def _fetch_weekend_forecast( self ):
        # exit script if user changed locations
        if ( self.Addon.getSetting( "forecast_weekend" ) != "true" ): return
        try:
            # set success message
            msg = "true"
            # fetch weekend forecast
            forecasts = self.WeatherClient.fetch_weekend_forecast()
            # enumerate thru and set the info
            for day, forecast in enumerate( forecasts ):
                self.WINDOW.setProperty( "Weekend.%d.Day" % ( day + 1, ), self.localize_text_special.get( forecast[ 0 ], [ forecast[ 0 ] ] )[ -1 ] )
                self.WINDOW.setProperty( "Weekend.%d.DayShort" % ( day + 1, ), self.localize_text_special.get( forecast[ 0 ], [ forecast[ 0 ] ] )[ 0 ] )
                self.WINDOW.setProperty( "Weekend.%d.Date" % ( day + 1, ), self.localize_unit( forecast[ 1 ], "monthdate", long=True ) )
                self.WINDOW.setProperty( "Weekend.%d.DateShort" % ( day + 1, ), self.localize_unit( forecast[ 1 ], "monthdate" ) )
                self.WINDOW.setProperty( "Weekend.%d.OutlookIcon" % ( day + 1, ), os.path.join( self.Addon.getSetting( "icon_path_weather" ), forecast[ 2 ] + ".png" ) )
                self.WINDOW.setProperty( "Weekend.%d.FanartCode" % ( day + 1, ), forecast[ 2 ] )
                self.WINDOW.setProperty( "Weekend.%d.Outlook" % ( day + 1, ), " ".join( [ self.localize_text.get( word, word ) for word in forecast[ 3 ].split( " " ) if ( word ) ] ) )
                self.WINDOW.setProperty( "Weekend.%d.HighTemperature" % ( day + 1, ), self.localize_unit( forecast[ 4 ] ) )
                self.WINDOW.setProperty( "Weekend.%d.LowTemperature" % ( day + 1, ), self.localize_unit( forecast[ 5 ] ) )
                self.WINDOW.setProperty( "Weekend.%d.Precipitation" % ( day + 1, ), forecast[ 6 ] )
                self.WINDOW.setProperty( "Weekend.%d.Wind" % ( day + 1, ), forecast[ 11 ] )
                self.WINDOW.setProperty( "Weekend.%d.Wind" % ( day + 1, ), self.localize_unit( forecast[ 8 ], "wind", direction=forecast[ 7 ] ) )
                self.WINDOW.setProperty( "Weekend.%d.WindLong" % ( day + 1, ), self.localize_unit( forecast[ 8 ], "wind", direction=forecast[ 7 ], long=True ) )
                self.WINDOW.setProperty( "Weekend.%d.WindDirection" % ( day + 1, ), self.localize_text_special.get( forecast[ 7 ], [ forecast[ 7 ] ] )[ 0 ] )
                self.WINDOW.setProperty( "Weekend.%d.WindDirectionLong" % ( day + 1, ), self.localize_text_special.get( forecast[ 7 ], [ forecast[ 7 ] ] )[ -1 ] )
                self.WINDOW.setProperty( "Weekend.%d.WindSpeed" % ( day + 1, ), self.localize_unit( forecast[ 8 ], "speed" ) )
                self.WINDOW.setProperty( "Weekend.%d.UVIndex" % ( day + 1, ), forecast[ 9 ] )
                self.WINDOW.setProperty( "Weekend.%d.Humidity" % ( day + 1, ), forecast[ 10 ] )
                self.WINDOW.setProperty( "Weekend.%d.Sunrise" % ( day + 1, ), self.localize_unit( forecast[ 11 ], "time" ) )
                self.WINDOW.setProperty( "Weekend.%d.Sunset" % ( day + 1, ), self.localize_unit( forecast[ 12 ], "time" ) )
                self.WINDOW.setProperty( "Weekend.%d.Forecast" % ( day + 1, ), forecast[ 13 ] )
                self.WINDOW.setProperty( "Weekend.%d.Observed" % ( day + 1, ), str( forecast[ 14 ] != "" ) )
                self.WINDOW.setProperty( "Weekend.%d.ObservedTemperature" % ( day + 1, ), self.localize_unit( forecast[ 15 ] ) )
                self.WINDOW.setProperty( "Weekend.%d.ObservedTemperature" % ( day + 1, ), self.localize_unit( forecast[ 16 ] ) )
                self.WINDOW.setProperty( "Weekend.%d.ObservedPrecipitation" % ( day + 1, ), self.localize_unit( forecast[ 17 ], "depth" ) )
                self.WINDOW.setProperty( "Weekend.%d.ObservedAvgHighTemperature" % ( day + 1, ), self.localize_unit( forecast[ 18 ] ) )
                self.WINDOW.setProperty( "Weekend.%d.ObservedAvgLowTemperature" % ( day + 1, ), self.localize_unit( forecast[ 19 ] ) )
                self.WINDOW.setProperty( "Weekend.%d.ObservedRecordHighTemperature" % ( day + 1, ), self.localize_unit( forecast[ 20 ] ) )
                self.WINDOW.setProperty( "Weekend.%d.ObservedRecordLowTemperature" % ( day + 1, ), self.localize_unit( forecast[ 21 ] ) )
                self.WINDOW.setProperty( "Weekend.%d.DepartureHigh" % ( day + 1, ), self.localize_unit( forecast[ 22 ], "tempdiff" ) )
                self.WINDOW.setProperty( "Weekend.%d.DepartureHighColor" % ( day + 1, ), ( "low", "high", "default", )[ ( len( forecast[ 22 ] ) and forecast[ 22 ][ 0 ] == "+" ) + ( forecast[ 22 ] == "+0" ) ] )
                self.WINDOW.setProperty( "Weekend.%d.DepartureLow" % ( day + 1, ), self.localize_unit( forecast[ 23 ], "tempdiff" ) )
                self.WINDOW.setProperty( "Weekend.%d.DepartureLowColor" % ( day + 1, ), ( "low", "high", "default", )[ ( len( forecast[ 23 ] ) and forecast[ 23 ][ 0 ] == "+" ) + ( forecast[ 23 ] == "+0" ) ] )
        except:
            # set error message
            msg = "error"
        # use this to hide info until fully fetched
        self.WINDOW.setProperty( "Weekend.IsFetched", msg )

    def _fetch_10day_forecast( self ):
        # exit script if user changed locations
        if ( self.Addon.getSetting( "forecast_10day" ) != "true" ): return
        try:
            # set success message
            msg = "true"
            # fetch daily forecast
            forecasts = self.WeatherClient.fetch_10day_forecast()
            # enumerate thru and set the info
            for day, forecast in enumerate( forecasts ):
                self.WINDOW.setProperty( "10Day.%d.Day" % ( day + 1, ), self.localize_text_special.get( forecast[ 0 ], [ forecast[ 0 ] ] )[ -1 ] )
                self.WINDOW.setProperty( "10Day.%d.DayShort" % ( day + 1, ), self.localize_text_special.get( forecast[ 0 ], [ forecast[ 0 ] ] )[ 0 ] )
                self.WINDOW.setProperty( "10Day.%d.Date" % ( day + 1, ), self.localize_unit( forecast[ 1 ], "monthdate", long=True ) )
                self.WINDOW.setProperty( "10Day.%d.DateShort" % ( day + 1, ), self.localize_unit( forecast[ 1 ], "monthdate" ) )
                self.WINDOW.setProperty( "10Day.%d.OutlookIcon" % ( day + 1, ), os.path.join( self.Addon.getSetting( "icon_path_weather" ), forecast[ 2 ] + ".png" ) )
                self.WINDOW.setProperty( "10Day.%d.FanartCode" % ( day + 1, ), forecast[ 2 ] )
                self.WINDOW.setProperty( "10Day.%d.Outlook" % ( day + 1, ), " ".join( [ self.localize_text.get( word, word ) for word in forecast[ 3 ].split( " " ) if ( word ) ] ) )
                self.WINDOW.setProperty( "10Day.%d.HighTemperature" % ( day + 1, ), self.localize_unit( forecast[ 4 ] ) )
                self.WINDOW.setProperty( "10Day.%d.LowTemperature" % ( day + 1, ), self.localize_unit( forecast[ 5 ] ) )
                self.WINDOW.setProperty( "10Day.%d.Precipitation" % ( day + 1, ), forecast[ 6 ] )
                self.WINDOW.setProperty( "10Day.%d.Wind" % ( day + 1, ), self.localize_unit( forecast[ 8 ], "wind", direction=forecast[ 7 ], split=True ) )
                self.WINDOW.setProperty( "10Day.%d.WindLong" % ( day + 1, ), self.localize_unit( forecast[ 8 ], "wind", direction=forecast[ 7 ], long=True, split=True ) )
                self.WINDOW.setProperty( "10Day.%d.WindDirection" % ( day + 1, ), self.localize_text_special.get( forecast[ 7 ], [ forecast[ 7 ] ] )[ 0 ] )
                self.WINDOW.setProperty( "10Day.%d.WindDirectionLong" % ( day + 1, ), self.localize_text_special.get( forecast[ 7 ], [ forecast[ 7 ] ] )[ -1 ] )
                self.WINDOW.setProperty( "10Day.%d.WindSpeed" % ( day + 1, ), self.localize_unit( forecast[ 8 ], "speed" ) )
        except:
            # set error message
            msg = "error"
            # set to empty to clear properties
            forecasts = []
        # just in case day 10 is missing
        for day in range( len( forecasts ), 10 ):
            self.WINDOW.clearProperty( "10Day.%d.DayShort" % ( day + 1, ) )
            self.WINDOW.clearProperty( "10Day.%d.Day" % ( day + 1, ) )
        # use this to hide info until fully fetched
        self.WINDOW.setProperty( "10Day.IsFetched", msg )

    def _exit_script( self ):
        # end script
        pass

"""
class FetchInfo( Thread ):
    def __init__( self, method ):
        Thread.__init__( self )
        self.method = method

    def run( self ):
        self.method()
"""
