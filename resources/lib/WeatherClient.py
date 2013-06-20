### weather.com api client module

import os

try:
    import xbmc
except:
    # get dummy xbmc modules (Debugging)
    from debug import *
    xbmc = XBMC()
    xbmcaddon = XBMCADDON()

import urllib2
import re
import time
import datetime

class WeatherAlert:
    # regex expressions
    regex_alert = re.compile( "<h2 class=\"wx-alert-subheader\">[^<]+<span class=\"la-alert-bullet alert-bullet-.+?\"></span>([^<]+)</h2>" )
    regex_expires = re.compile( "<h3 class=\"twc-module-sub-header twc-timestamp twc-alert-timestamp\">([^<]+)</h3>" )
    regex_posted = re.compile( "<h3 class=\"twc-module-sub-header twc-timestamp\">([^<]+)</h3>" )
    regex_issuedby = re.compile( "<h3>.+?(Issued by.+?)</h3>", re.DOTALL )
    regex_narrative = re.compile( "<div class=\"wx-alert-body\">(.*?)</div>", re.DOTALL )

    def __init__( self, htmlSource ):
        try:
            self._get_alert( htmlSource )
        except:
            self.alert = None
            self.title = ""
            self.alert_rss = ""

    def _get_alert( self, htmlSource ):
        # fetch alert parts
        alert = self.regex_alert.search( htmlSource ).group( 1 ).strip()
        expires = self.regex_expires.search( htmlSource ).group( 1 ).strip()
        posted = self.regex_posted.search( htmlSource ).group( 1 ).strip()
        issuedby = self.regex_issuedby.search( htmlSource ).group( 1 ).replace( "<br>", "[CR]" ).strip()
        narrative = self.regex_narrative.search( htmlSource ).group( 1 ).replace( "\n", "" ).replace( "\t", "" ).replace( "</p>", "\n\n" ).replace( "<p>", "" ).replace( "<h2>", "[B]" ).replace( "</h2>", "[/B]\n\n" ).strip()
        # create our alert string
        self.alert = "[B]%s[/B]\n\n%s\n\n[I]%s[/I]\n\n%s\n\n%s\n%s\n\n" % ( alert, expires, issuedby, posted, narrative, "-" * 100, )
        # we use this for adding titles at the beginning of the alerts text for multiple alerts
        self.title = alert
        # set the alert rss
        self.alert_rss = "[COLOR=rss_headline]%s:[/COLOR] %s %s - %s" % ( alert, alert, expires, issuedby.replace( "[CR]", " " ), )


class Forecast36HourParser:
    # regex expressions
    ##regex_video_location = re.compile( ">Watch the ([A-Za-z ]+) Forecast<" )
    regex_alerts = re.compile( "<div class=\"la-alert-bullet alert-bullet-([^\"]+)\"></div>\s[^<]+<div class=.+location.href=\'([^\']+)\'\" title=\"([^\"]+)\">([^<]+)</div>" )
    regex_days = re.compile( "<td class=\"twc-col-[2-4]+ twc-forecast-when.*?\">([^<]+)</td>" )
    regex_icon = re.compile( "<td class=\"twc-col-[2-4]+ twc-forecast-icon\">.+?<img src=\"http://s.imwx.com/v.20100719.135915/img/wxicon/72/(.+?).png\" width=\"72\" height=\"72\" alt=\"[^\"]+\" ></a></td>" )
    regex_brief = re.compile( "<td class=\"twc-col-[2-4]+\">([^<]+)</td>" )
    regex_temp = re.compile( "<td class=\"twc-col-[2-4]+ twc-forecast-temperature\"><strong>([0-9\-]+)[^<]+</strong></td>" )
    regex_temp_title = re.compile( "<td class=\"twc-col-[2-4]+ twc-forecast-temperature-info\">([^<]+)</td>" )
    ##regex_precip = re.compile( "<td class=\"twc-col-[2-4]+ twc-line-precip\">.+?<br><strong>([0-9]+)%</strong></td>" )
    regex_precip = re.compile( "<td class=\"twc-col-[2-4]+ twc-line-precip[^\"]*\">.+?<br><strong>([0-9]+)%</strong>", re.DOTALL )
    regex_wind = re.compile( "<td class=\"twc-col-[2-4]+ twc-line-wind\">Wind:<br><strong>.+?([A-Z]+) at.+?([0-9]+) mph", re.DOTALL )
    regex_humidity = re.compile( "<td class=\"twc-col-[2-4]+ twc-line-details twc-first\">([0-9]+)%</td>" )
    regex_uv_index = re.compile( "<td class=\"twc-col-[2-4]+ twc-line-details twc-last\">([^<]+)</td>", re.DOTALL )
    regex_daylight = re.compile( "<td class=\"twc-col-[2-4]+ twc-line-daylight\">([^<]+)<strong>(.+?)</strong>", re.DOTALL )

    def __init__( self, htmlSource ):
        self.forecast = []
        self.extras = []
        self.alerts = []
        ##self.video_location = []
        # only need to parse source if there is source
        if ( htmlSource ):
            self._get_forecast( htmlSource )

    def _get_forecast( self, htmlSource ):
        # fetch days
        days = self.regex_days.findall( htmlSource )
        # enumerate thru and combine the day with it's forecast
        if ( len( days ) ):
            # fetch info
            icon = self.regex_icon.findall( htmlSource )
            brief = self.regex_brief.findall( htmlSource )
            temp = self.regex_temp.findall( htmlSource )
            temp_title = self.regex_temp_title.findall( htmlSource )
            precip = self.regex_precip.findall( htmlSource )
            wind = self.regex_wind.findall( htmlSource )
            humidity = self.regex_humidity.findall( htmlSource )
            uvindex = self.regex_uv_index.findall( htmlSource )
            daylight = self.regex_daylight.findall( htmlSource )
            # parse outlooks
            outlook = brief[ 3 : ]
            # fetch alerts
            self.alerts = self.regex_alerts.findall( htmlSource )
            # loop thru and add our forecasts
            for count, day in enumerate( days ):
                # add result to our class variable
                self.forecast += [ ( day, icon[ count ], brief[ count ], temp_title[ count ], temp[ count ], precip[ count ], wind[ count ], humidity[ count ], uvindex[ count ].strip().replace( " - ", " " ).split(), outlook[ count ].strip(), daylight[ count ][ 0 ].strip( ": " ), daylight[ count ][ 1 ].strip(), ) ]


class ForecastHourlyParser:
    # regex expressions
    # use this to grab the 15 minutes details
    # regex_info = re.compile( "<div class=\"hbhTDTime[^>]+><div>([^<]+)</div></div>\
    # use this to grab only 1 hour details
    regex_info = re.compile( "<div class=\"hbhTDTime\"><div>([^<]+)</div></div>\
[^<]+<div class=\"hbhTDConditionIcon\"><div><img src=\"http://i.imwx.com/web/common/wxicons/[0-9]+/(?:gray/)?([0-9]+).gif\"[^>]+></div></div>\
[^<]+<div class=\"hbhTDCondition\"><div><b>([0-9\-]+)[^<]+</b><br>([^<]+)</div></div>\
[^<]+<div class=\"hbhTDFeels\"><div>([0-9\-]+)[^<]+</div></div>\
[^<]+<div class=\"hbhTDPrecip\"><div>([0-9]+)[^<]+</div></div>\
[^<]+<div class=\"hbhTDHumidity\"><div>([0-9]+)[^<]+</div></div>\
[^<]+<div class=\"hbhTDWind\"><div>(?:(.+?)<br> )?(.+?)(?: mph)?</div></div>" )
    regex_dates = re.compile( "<div class=\"hbhDateHeader\">([^<]+)</div>" )
    regex_sunrise = re.compile( "<img src=\"http://i.imwx.com/web/local/hourbyhour/icon_sunrise.gif\"[^>]+>.*?Sunrise ([0-9]+:[0-9]+ [a-z]+)" )
    regex_sunset = re.compile( "<img src=\"http://i.imwx.com/web/local/hourbyhour/icon_sunset.gif\"[^>]+>.*?Sunset ([0-9]+:[0-9]+ [a-z]+)" )

    def __init__( self, htmlSource ):
        self.forecast = []
        # only need to parse source if there is source
        if ( htmlSource ):
            self._get_forecast( htmlSource )

    def _get_forecast( self, htmlSource ):
        # fetch info
        info = self.regex_info.findall( htmlSource )
        # enumerate thru and create heading and forecast
        if ( len( info ) ):
            # fetch dates, add an extra blank date for times when weather.com, does not display date
            dates = [ self.regex_dates.search( htmlSource ).group( 1 ).split( ", " )[ -1 ] ]
            ndate = datetime.datetime( *time.strptime( dates[ 0 ], "%B %d" )[ : 3 ] ) + datetime.timedelta( days=1 )
            dates += [ ndate.strftime( "%B %d" ) ]
            # fetch sunrise and sunset
            sunrise = self.regex_sunrise.search( htmlSource )
            sunset = self.regex_sunset.search( htmlSource )
            # initialize date counter
            date_counter = 0
            # create our forecast list
            for count, item in enumerate( info ):
                # set sunrise and sunset
                _sunrise = _sunset = ""
                if ( sunrise is not None ):
                    _sunrise = [ "", sunrise.group( 1 ) ][ time.strptime( re.sub( ":[0-9]+", "", sunrise.group( 1 ) ), "%I %p" ) == time.strptime( item[ 0 ], "%I %p" ) ]
                if ( sunset is not None ):
                    _sunset = [ "", sunset.group( 1 ) ][ time.strptime( re.sub( ":[0-9]+", "", sunset.group( 1 ) ), "%I %p" ) == time.strptime( item[ 0 ], "%I %p" ) ]
                # do we need to increment date_counter
                if ( item[ 0 ] == "12 am" and count > 0 ):
                    date_counter += 1
                # add result to our class variable
                self.forecast += [ ( item[ 0 ], dates[ date_counter ], item[ 1 ], item[ 2 ], item[ 3 ].replace( "/", " / " ), item[ 4 ], item[ 5 ], item[ 6 ], item[ 7 ].replace( "From", "" ).strip(), item[ 8 ], _sunrise, _sunset, ) ]


class ForecastWeekendParser:
    # regex expressions
    regex_heading = re.compile( "from=[\"]*weekend[\"]+>([^<]+)</A>.*\s.*\s\
[^<]+<TD width=\"[^\"]+\" class=\"wkndButton[A-Z]+\" align=\"[^\"]+\" valign=\"[^\"]+\"><FONT class=\"[^\"]+\">([^\&]+)" )
    regex_observed = re.compile( ">(Observed:)+" )
    regex_brief = re.compile( "<IMG src=\"http://(?:i.imwx.com)?(?:image.weather.com)?/web/common/wxicons/(?:pastwx/)?[0-9]+/([0-9\-]+).gif.*alt=\"([^\"]+)\"" )
    regex_past = re.compile( "<TD align=\"left\" class=\"grayFont10\">[a-zA-z]+:&nbsp;([0-9\.\-]+)[^<]+</TD>" )
    regex_avg = re.compile( "<tr><td align=\"right\" valign=\"top\" CLASS=\"blueFont10\">[^<]+<.*\s.*\s[^[A-Z0-9\-]+([0-9\-]+)&deg;F" )
    regex_high = re.compile( "<FONT class=\"[^\"]+\">High<BR><FONT class=\"[^\"]+\"><NOBR>([0-9\-]+)[^<]+</FONT></NOBR>" )
    regex_low = re.compile( "<FONT class=\"[^\"]+\">Low</FONT><BR><FONT class=\"[^\"]+\"><B>([0-9\-]+)[^<]+</B></FONT>" )
    regex_precip = re.compile( "<TD valign=\"top\" width=\"50%\" class=\"blueFont10\" align=\"left\"><B>([0-9]+)%</B>" )
    regex_wind = re.compile( "<td align=\"[^\"]+\" valign=\"[^\"]+\" CLASS=\"[^\"]+\">[^<]+</td><td align=\"[^\"]+\">&nbsp;</td><td valign=\"[^\"]+\" CLASS=\"[^\"]+\"><B>.*\n[^A-Z]+([A-Z]+)<br>at ([0-9]+) mph</B>" )
    regex_uv = re.compile( "<td align=\"[^\"]+\" valign=\"[^\"]+\" CLASS=\"[^\"]+\">UV Index:</td>\s[^>]+>[^>]+>[^>]+><B>([^<]+)" )
    regex_humidity = re.compile( "<td align=\"[^\"]+\" valign=\"[^\"]+\" CLASS=\"[^\"]+\">Humidity:[^>]+>[^>]+>[^>]+>[^>]+><B>([0-9]+)%" )
    regex_daylight = re.compile( "<td align=\"[^\"]+\" valign=\"[^\"]+\" CLASS=\"[^\"]+\">[^<]+[^>]+>[^>]+>[^>]+>[^>]+><B>([0-9]+:[0-9]+[^<]+)</B></td>" )
    regex_outlook = re.compile( "<TD colspan=\"3\" class=\"blueFont10\" valign=\"middle\" align=\"left\">([^<]+)</TD>" )
    regex_departures = re.compile( "<FONT COLOR=\"#7d8c9f\"><B>\s.*\s\s+([\-\+]+[0-9]+)&deg;F" )

    def __init__( self, htmlSource ):
        self.forecast = []
        # only need to parse source if there is source
        if ( htmlSource ):
            self._get_forecast( htmlSource )

    def _get_forecast( self, htmlSource ):
        # fetch headings
        headings = self.regex_heading.findall( htmlSource )
        # no need to run if none found
        if ( len( headings ) ):
            # fetch observed status
            observeds = self.regex_observed.findall( htmlSource )
            observeds += [ "" for count in range( 3 - len( observeds ) ) ]
            # fetch briefs
            briefs = self.regex_brief.findall( htmlSource )
            ##briefs = [ ( "na", "", ) for count in range( 3 - len( briefs ) ) ] + briefs
            # fetch departure from normal
            departures = self.regex_departures.findall( htmlSource )
            departures += [ "" for count in range( 6 - len( departures ) ) ]
            # fetch past info
            pasts = self.regex_past.findall( htmlSource )
            pasts += [ "" for count in range( 9 - len( pasts ) ) ]
            # fetch average info
            avgs = self.regex_avg.findall( htmlSource )
            avgs += [ "" for count in range( 12 - len( avgs ) ) ]
            # fetch highs
            highs = self.regex_high.findall( htmlSource )
            highs = [ pasts[ count * 3 ] for count in range( 3 - len( highs ) ) ] + highs
            # fetch lows
            lows = self.regex_low.findall( htmlSource )
            lows = [ pasts[ count * 3 + 1 ] for count in range( 3 - len( lows ) ) ] + lows
            # fetch precips
            precips = self.regex_precip.findall( htmlSource )
            precips = [ "" for count in range( 3 - len( precips ) ) ] + precips
            # fetch winds
            winds = self.regex_wind.findall( htmlSource )
            winds = [ ( "", "", ) for count in range( 3 - len( winds ) ) ] + winds
            # fetch uvs
            uvs = self.regex_uv.findall( htmlSource )
            uvs = [ "" for count in range( 3 - len( uvs ) ) ] + uvs
            # fetch humids
            humids = self.regex_humidity.findall( htmlSource )
            humids = [ "" for count in range( 3 - len( humids ) ) ] + humids
            # fetch daylights
            daylights = self.regex_daylight.findall( htmlSource )
            daylights = [ "" for count in range( 6 - len( daylights ) ) ] + daylights
            # fetch outlooks
            outlooks = self.regex_outlook.findall( htmlSource )
            outlooks = [ "" for count in range( 3 - len( outlooks ) ) ] + outlooks
            # set our previous variables to the first items
            pdate = datetime.datetime( *time.strptime( headings[ 0 ][ 1 ], "%b %d" )[ : 3 ] )
            # enumerate thru and create our forecast list
            for count, ( day, date, ) in enumerate( headings ):
                # set proper date
                date = pdate + datetime.timedelta( days=count )
                # add result to our class variable
                self.forecast += [ ( day, date.strftime( "%b %d" ), briefs[ count ][ 0 ].replace( "-", "na" ), briefs[ count ][ 1 ], highs[count],
                    lows[ count ], precips[ count ], winds[ count ][ 0 ], winds[ count ][ 1 ], uvs[ count ], humids[ count ], daylights[ count * 2 ], daylights[ count * 2 + 1 ],
                    outlooks[ count ], observeds[ count ], pasts[ count * 3 ], pasts[ count * 3 + 1 ], pasts[ count * 3 + 2 ],
                    avgs[ count * 4 ], avgs[ count * 4 + 1 ], avgs[ count * 4 + 2 ], avgs[ count * 4 + 3 ], departures[ count * 2 ], departures[ count * 2 + 1 ], ) ]


class Forecast10DayParser:
    # regex expressions
    regex_info = re.compile( "<p><[^>]+>([^<]+)</a><br>([^<]+)</p>\s.*\s.*\s.*\s.*\s\
[^<]+<p><img src=\"http://i.imwx.com/web/common/wxicons/[0-9]+/([0-9]+).gif[^>]+><br>([^<]+)</p>\s.*\s.*\s.*\s.*\s[^<]+<p><strong>([^&<]+)[^<]*</strong><br>([0-9\-]+)[^<]+</p>\s.*\s.*\s.*\s.*\s.*\s[^<]+<p>([0-9]+)[^<]+</p>\s.*\s.*\s.*\s.*\s.*\s.*\s.*\s[^<]+<td><p>([^<]+)</p></td>\s.*\s.*\s\
[^<]+<[^<]+<[^<]+<[^<]+<strong>([^<]+)</strong>[^<]+</p>" )

    def __init__( self, htmlSource ):
        self.forecast = []
        # only need to parse source if there is source
        if ( htmlSource ):
            self._get_forecast( htmlSource )

    def _get_forecast( self, htmlSource ):
        # fetch info
        info = self.regex_info.findall( htmlSource )
        # enumerate thru and create heading and forecast
        if ( len( info ) ):
            # create our forecast list
            for count, item in enumerate( info ):
                # add result to our class variable
                self.forecast += [ ( item[ 0 ], item[ 1 ], item[ 2 ], item[ 3 ], item[ 4 ], item[ 5 ], item[ 6 ], item[ 7 ].replace( "From the ", "" ), item[ 8 ], ) ]


class MaplistParser:
    # regex expressions
    regex_map_list = re.compile( "<option.+?value=\"([^\"]+)\".*?>([^<]+)</option>", re.IGNORECASE )

    def __init__( self, htmlSource ):
        self.map_list = []
        self._get_map_list( htmlSource )

    def _get_map_list( self, htmlSource ):
        try:
            # fetch avaliable maps
            map_list = self.regex_map_list.findall( htmlSource )
            # enumerate thru list and eliminate bogus items
            for map in map_list:
                # eliminate bogus items
                if ( len( map[ 0 ] ) > 7 ):
                    self.map_list += [ map + ( "", ) ]
        except:
            pass


class MapParser:
    # regex expressions
    regex_maps = re.compile( "<IMG NAME=\"mapImg\" SRC=\"([^\"]+)\"", re.IGNORECASE )
    regex_motion_map = re.compile( ">Weather In Motion<", re.IGNORECASE )

    def __init__( self, htmlSource ):
        self.maps = ()
        # get maps
        self._get_maps( htmlSource )

    def _get_maps( self, htmlSource ):
        try:
            # initialize our animated maps list
            animated_maps = []
            # fetch static map
            static_map = self.regex_maps.search( htmlSource ).group( 1 )
            # regex necessary for case
            motion = self.regex_motion_map.search( htmlSource )
            # i believe find is faster than regex
            ##motion = htmlSource.find( ">Weather In Motion<" )
            # does this map support animation?
            if ( motion is not None ):
                # get our map
                region = os.path.splitext( os.path.basename( static_map ) )[ 0 ]
                # enumerate thru and create our animated map urls
                for i in range( 1, 6 ):
                    animated_maps += [ "http://image.weather.com/looper/archive/%s/%dL.jpg" % ( region, i, ) ]
        except Exception, e:
            # oops log error message
            xbmc.log( "MapParser::_get_maps (%s)" % ( e, ), xbmc.LOGERROR )
        # set our maps object
        self.maps += ( [ static_map ], animated_maps, "", )


class VideoListParser:
    # regex expressions
    regex_video_list = re.compile( "<item>[^<]+<title>(.+?) Forecast</title>[^<]+<link>http://link.brightcove.com/services/link/[^/]+/bclid87703296[0-9]+/[^<]+</link>[^<]+<description>&lt;img src=\"(http://i.imwx.com/web/multimedia/images/miscellaneous/([a-z]+)_[0-9]+.jpg)\"/&gt;[^<]+</description>", re.MULTILINE )
    regex_title_list = re.compile( "<item>[^<]+<title>(.+?) Forecast</title>[^<]+<link>http://link.brightcove.com/services/link/[^/]+/bclid87703296[0-9]+/[^<]+</link>", re.MULTILINE )

    def __init__( self, xmlSource ):
        # initialize our info lists
        self.video_list = []
        self.title_list = []
        # only need to parse source if there is source
        if ( xmlSource ):
            self._get_video_list( xmlSource )

    def _get_video_list( self, xmlSource ):
        # parse info, titlelist is needed for matching existing with new
        self.video_list = self.regex_video_list.findall( xmlSource )
        self.title_list = self.regex_title_list.findall( xmlSource )


class WeatherClient:
    # base urls
    BASE_URL = "http://www.weather.com"
    BASE_FORECAST_URL = "http://www.weather.com/%s/%s%s"
    ##BASE_MAP_URL = "http://www.weather.com/outlook/travel/businesstraveler/%s/%s?bypassredirect=true%s"
    BASE_VIDEO_URL = "http://v.imwx.com/multimedia/video/wxflash/%s.flv"
    BASE_VIDEO_THUMB_URL = "http://i.imwx.com/web/multimedia/images/miscellaneous/%s_122.jpg"#177 TODO: verify this changed
    # TODO: verify this does not change
    BASE_VIDEO_LIST_URL = "http://link.brightcove.com/services/link/bcpid824514779?action=rss"
    BASE_MAPS = {
        # Place holder for no selection
        30900: { "url": "" },
        # Main local maps (includes some regional maps)
        30901: { "url": "/outlook/travel/businesstraveler/%s/%s?bypassredirect=true%s" },
        # user defined
        30902: { "url": "*" },
        # weather details
        30903: { "url": "/maps/geography/alaskaus/index_large.html" },
        30904: { "url": "/maps/maptype/currentweatherusnational/index_large.html" },
        30905: { "url": "/maps/maptype/dopplerradarusnational/index_large.html" },
        30906: { "url": "/maps/maptype/tendayforecastusnational/index_large.html" },
        30907: { "url": "/maps/geography/hawaiius/index_large.html" },
        30908: { "url": "/maps/maptype/satelliteusnational/index_large.html" },
        30909: { "url": "/maps/maptype/satelliteworld/index_large.html" },
        30910: { "url": "/maps/maptype/severeusnational/index_large.html" },
        30911: { "url": "/maps/maptype/severeusregional/index_large.html" },
        30912: { "url": "/maps/maptype/forecastsusnational/index_large.html" },
        30913: { "url": "/maps/maptype/weeklyplannerusnational/index_large.html" },
        30914: { "url": "/maps/maptype/currentweatherusregional/index_large.html" },
        30915: { "url": "/maps/maptype/forecastsusregional/index_large.html" },
        30916: { "url": "/maps/geography/centralus/index_large.html" },
        30917: { "url": "/maps/geography/eastcentralus/index_large.html" },
        30918: { "url": "/maps/geography/midwestus/index_large.html" },
        30919: { "url": "/maps/geography/northcentralus/index_large.html" },
        30920: { "url": "/maps/geography/northeastus/index_large.html" },
        30921: { "url": "/maps/geography/northwestus/index_large.html" },
        30922: { "url": "/maps/geography/southcentralus/index_large.html" },
        30923: { "url": "/maps/geography/southeastus/index_large.html" },
        30924: { "url": "/maps/geography/southwestus/index_large.html" },
        30925: { "url": "/maps/geography/westus/index_large.html" },
        30926: { "url": "/maps/geography/westcentralus/index_large.html" },
        30927: { "url": "/maps/geography/africaandmiddleeast/index_large.html" },
        30928: { "url": "/maps/geography/asia/index_large.html" },
        30929: { "url": "/maps/geography/australia/index_large.html" },
        30930: { "url": "/maps/geography/centralamerica/index_large.html" },
        30931: { "url": "/maps/geography/europe/index_large.html" },
        30932: { "url": "/maps/geography/northamerica/index_large.html" },
        30933: { "url": "/maps/geography/pacific/index_large.html" },
        30934: { "url": "/maps/geography/polar/index_large.html" },
        30935: { "url": "/maps/geography/southamerica/index_large.html" },
        # activity
        30936: { "url": "/maps/activity/garden/index_large.html" },
        30937: { "url": "/maps/activity/aviation/index_large.html" },
        30938: { "url": "/maps/activity/boatbeach/index_large.html" },
        30939: { "url": "/maps/activity/travel/index_large.html" },
        30940: { "url": "/maps/activity/driving/index_large.html" },
        30941: { "url": "/maps/activity/fallfoliage/index_large.html" },
        30942: { "url": "/maps/activity/golf/index_large.html" },
        30943: { "url": "/maps/activity/nationalparks/index_large.html" },
        30944: { "url": "/maps/geography/oceans/index_large.html" },
        30945: { "url": "/maps/activity/pets/index_large.html" },
        30946: { "url": "/maps/activity/ski/index_large.html" },
        30947: { "url": "/maps/activity/specialevents/index_large.html" },
        30948: { "url": "/maps/activity/sportingevents/index_large.html" },
        30949: { "url": "/maps/activity/vacationplanner/index_large.html" },
        30950: { "url": "/maps/activity/weddings/spring/index_large.html" },
        30951: { "url": "/maps/activity/weddings/summer/index_large.html" },
        30952: { "url": "/maps/activity/weddings/fall/index_large.html" },
        30953: { "url": "/maps/activity/weddings/winter/index_large.html" },
        30954: { "url": "/maps/activity/holidays/index_large.html" },
        # health and safety
        30955: { "url": "/maps/activity/achesandpains/index_large.html" },
        30956: { "url": "/maps/activity/airquality/index_large.html" },
        30957: { "url": "/maps/activity/allergies/index_large.html" },
        30958: { "url": "/maps/activity/coldandflu/index_large.html" },
        30959: { "url": "/maps/maptype/earthquakereports/index_large.html" },
        30960: { "url": "/maps/activity/home/index_large.html" },
        30961: { "url": "/maps/activity/schoolday/index_large.html" },
        30962: { "url": "/maps/maptype/severeusnational/index_large.html" },
        30963: { "url": "/maps/activity/skinprotection/index_large.html" },
        30964: { "url": "/maps/activity/fitness/index_large.html" },
    }

    def __init__( self, code=None, Addon=None ):
        # Addon class
        self.Addon = Addon
        # set base paths
        self.BASE_MAPS_PATH = os.path.join( xbmc.translatePath( "special://temp" ), os.path.basename( self.Addon.getAddonInfo( "Path" ) ), "maps" )
        self.BASE_PROFILE_PATH = xbmc.translatePath( self.Addon.getAddonInfo( "Profile" ) )
        # set users weather.com code
        self.code = code

    def fetch_videos( self, videos ):
        # create video url
        videos = self._get_videos( videos )
        # return forecast
        return videos

    def fetch_36hour_forecast( self ):
        # fetch source
        htmlSource = self._fetch_data( self.BASE_FORECAST_URL % ( "weather/today", self.code, "", ), 15, headers={ "Accept-Encoding": "text\html" } )
        # parse source for forecast
        parser = Forecast36HourParser( htmlSource )
        # fetch any alerts
        alerts, alertsrss, alertsnotify, alertscolor = self._fetch_alerts( parser.alerts )
        # return forecast
        return alerts, alertsrss, alertsnotify, alertscolor, len( parser.alerts), parser.forecast

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
                if ( url[ 0 ] == "blank" ):
                    continue
                # fetch source refresh every 15 minutes
                htmlSource = self._fetch_data( self.BASE_URL + url[ 1 ], 15 )
                # parse source for alerts
                parser = WeatherAlert( htmlSource )
                # needed in case a new alert format was used and we errored
                if ( parser.alert is not None ):
                    # add result to our alert string
                    alerts += parser.alert
                    titles += [ parser.title ]
                    alertsrss += "%s  |  " % ( parser.alert_rss, )
                    alertsnotify += "%s  |  " % ( parser.title, )
            # TODO: maybe handle this above passing count to the parser
            # make our title string if more than one alert
            if ( len( titles ) > 1 ):
                title_string = ""
                for count, title in enumerate( titles ):
                    title_string += "%d. %s\n" % ( count + 1, title, )
                # add titles to alerts
                alerts = "%s\n[B]%s[/B]\n%s\n\n%s" % (  "-" * 100, title_string.strip(), "-" * 100, alerts )
        # return alert string stripping the last newline chars
        return alerts.strip(), alertsrss.rstrip( "| " ), alertsnotify.rstrip( "| " ), alertscolor

    def _get_videos( self, videos ):
        # return if already have videos set, videos[ 0 ] is national (global)
        if ( videos[ 0 ][ 0 ].startswith( "http://" ) and videos[ 1 ][ 0 ].startswith( "http://" ) and videos[ 2 ][ 0 ].startswith( "http://" ) and videos[ 3 ][ 0 ].startswith( "http://" ) ): return videos
        # fetch list
        self.fetch_local_video_list()
        # create national video url
        if ( ( self.code.startswith( "MX" ) and videos[ 0 ][ 0 ] == "0" ) or videos[ 0 ][ 0 ] == "3" ):
            url = self.BASE_VIDEO_URL % ( "mexico", )
            thumburl = self.BASE_VIDEO_THUMB_URL % ( "mexico", )
        elif ( ( self.code.startswith( "CAXX" ) and videos[ 0 ][ 0 ] == "0" ) or videos[ 0 ][ 0 ] == "2" ):
            url = self.BASE_VIDEO_URL % ( "canada", )
            thumburl = self.BASE_VIDEO_THUMB_URL % ( "canada", )
        else:
            url = self.BASE_VIDEO_URL % ( "national", )
            thumburl = self.BASE_VIDEO_THUMB_URL % ( "national", )
        # get thumbnail
        cachepath = self._fetch_data( thumburl, filename=os.path.basename( thumburl ) )
        videos[ 0 ] = [ url, os.path.join( cachepath, os.path.basename( thumburl ) ) ]
        # create regional
        if ( not videos[ 1 ][ 0 ].startswith( "http://" ) ):
            cachepath = self._fetch_data( self.BASE_VIDEO_THUMB_URL % ( videos[ 1 ][ 0 ], ), filename=os.path.basename( self.BASE_VIDEO_THUMB_URL % ( videos[ 1 ][ 0 ], ) ) )
            videos[ 1 ] = [ self.BASE_VIDEO_URL % ( videos[ 1 ][ 0 ], ), os.path.join( cachepath, os.path.basename( self.BASE_VIDEO_THUMB_URL % ( videos[ 1 ][ 0 ], ) ) ) ]
        # create local
        if ( not videos[ 2 ][ 0 ].startswith( "http://" ) ):
            source = self._fetch_data( os.path.join( self.BASE_PROFILE_PATH, "local_video_list", videos[ 2 ][ 0 ] ) )
            # get thumbnail
            cachepath = self._fetch_data( source.splitlines()[ 1 ], filename=os.path.basename( source.splitlines()[ 1 ] ) )
            videos[ 2 ] = [ source.splitlines()[ 0 ], os.path.join( cachepath, os.path.basename( source.splitlines()[ 1 ] ) ) ]
        # create storm
        if ( not videos[ 3 ][ 0 ].startswith( "http://" ) ):
            cachepath = self._fetch_data( self.BASE_VIDEO_THUMB_URL % ( "storm", ), filename=os.path.basename( self.BASE_VIDEO_THUMB_URL % ( "storm", ) ) )
            videos[ 3 ] = [ self.BASE_VIDEO_URL % ( "storm", ), os.path.join( cachepath, os.path.basename( self.BASE_VIDEO_THUMB_URL % ( "storm", ) ) ) ]
        # return reults
        return videos

    def fetch_local_video_list( self, refresh=False ):
        # fetch source
        xmlSource = self._fetch_data( self.BASE_VIDEO_LIST_URL, [ 10080, -1 ][ refresh ] )
        # parse source for forecast
        parser = VideoListParser( xmlSource )
        # base path
        base_path = os.path.join( self.BASE_PROFILE_PATH, "local_video_list" )
        # get current list
        try:
            current_list = os.listdir( base_path )
        except Exception, e:
            current_list = []
        # set our add/remove lists TODO: do we want to refresh this always in case urls change?
        add_video_list = [ set( parser.title_list ).difference( current_list ), parser.title_list ][ refresh ]
        remove_video_list = set( current_list ).difference( parser.title_list )
        # enumerate thru and delete our city
        for city in remove_video_list:
            # set proper path
            _path = os.path.join( base_path, city )
            # remove file
            os.remove( _path )
        # enumerate thru and add our city
        for city in add_video_list:
            # set proper path
            _path = os.path.join( base_path, xbmc.makeLegalFilename( city ) )
            # set data = video url and thumb url
            data = "%s\n%s" % ( self.BASE_VIDEO_URL % ( parser.video_list[ parser.title_list.index( city ) ][ 2 ], ), parser.video_list[ parser.title_list.index( city ) ][ 1 ], )
            # save file
            self._save_data( data, _path )
        # set video list fetched date
        if ( parser.title_list != [] ):
            self.Addon.setSetting( "video_list_fetched", "%s: %s" % ( self.Addon.getLocalizedString( 30759 ).encode( "UTF-8" ), xbmc.getInfoLabel( "System.Date" ), ) )
        # return status
        return parser.title_list != []

    def fetch_hourly_forecast( self ):
        # fetch source
        htmlSource = self._fetch_data( self.BASE_FORECAST_URL % ( "weather/hourbyhour", self.code, "", ), 15 )
        # parse source for forecast
        parser = ForecastHourlyParser( htmlSource )
        # return forecast
        return parser.forecast

    def fetch_weekend_forecast( self ):
        # fetch source
        htmlSource = self._fetch_data( self.BASE_FORECAST_URL % ( "outlook/travel/businesstraveler/weekend", self.code, "?lwsa=Weather36HourBusinessTravelerCommand", ), 15 )
        # parse source for forecast
        parser = ForecastWeekendParser( htmlSource )
        # return forecast
        return parser.forecast

    def fetch_10day_forecast( self ):
        # fetch source
        htmlSource = self._fetch_data( self.BASE_FORECAST_URL % ( "weather/tenday", self.code, "?dp=windsdp", ), 15 )
        # parse source for forecast
        parser = Forecast10DayParser( htmlSource )
        # return forecast
        return parser.forecast

    def fetch_map_list( self, maptype=30900, userfile=None, locationindex=None ):
        # set url
        url = self.BASE_URL + self.BASE_MAPS[ maptype ][ "url" ]
        # we handle None, local and custom map categories differently
        if ( maptype == 30900 ):
            # return None if none category was selected
            return None, None
        elif ( maptype == 30901 ):
            # add weather.com code to local map list if local category
            url = url % ( "map", self.code, "", )
            #print url
        # handle user definde maps special
        if ( maptype == 30902 ):
            # initialize our map list variable
            map_list = []
            # get correct location source
            category_title, titles, locationindex = self._get_user_file( userfile, locationindex )
            # if user file not found return None
            if ( category_title is None ):
                return None, None
            # enumerate thru and create map list
            for count, title in enumerate( titles ):
                # add title, we use a locationindex for later usage, since there is no html source to parse for images, we use count to know correct map to use
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
            location = re.search( pattern % ( locationindex, ), xmlSource, re.DOTALL ).group( 1 )
        except:
            # we need to set the used location id
            locationindex = "1"
            # use default "1"
            location = re.search( pattern % ( locationindex, ), xmlSource, re.DOTALL ).group( 1 )
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
                urls2 = [ [], urls ][ len( urls ) > 1 ]
                # get a legend if it is separate from inages
                try:
                    legend = re.search( "<legend_url>([^<]*)</legend_url>", titles[ map ][ 1 ] ).group( 1 )
                except:
                    legend = ""
                # return results
                return ( [ urls[ -1 ] ], urls2, legend, )
            # no image urls, find map urls
            map = re.search( "<map_url>([^<]+)</map_url>", titles[ map ][ 1 ] ).group( 1 )
        # set url
        if ( map.endswith( ".html" ) ):
            url = self.BASE_URL + map
        else:
            url = self.BASE_FORECAST_URL % ( "outlook/travel/businesstraveler/map", self.code, "?mapdest=%s" % ( map, ), )
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
            image = os.path.basename( url )
            # fetch map
            base_path_maps = self._fetch_data( url, -1 * ( count + 1 ), image, len( maps ) > 1, subfolder="" )
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

    def _fetch_data( self, base_url, refreshtime=0, filename=None, animated=False, subfolder="forecasts", retry=True, headers={} ):
        try:
            # set proper base path
            if ( not base_url.startswith( "http://" ) ):
                # user defined maps file
                base_path = base_url
                base_refresh_path = None
            elif ( filename is None ):
                # anything else except map/radar images (basically htmlSource)
                base_path = os.path.join( self.BASE_PROFILE_PATH, "source", subfolder, xbmc.getCacheThumbName( base_url )[ : -4 ] )
                base_refresh_path = None
            else:
                # set proper path for hash
                if ( animated ):
                    # animated maps include map name in base url, so don't use filename (each jpg would be in a seperate folder if you did)
                    _path = os.path.dirname( base_url )
                else:
                    # non animated maps share same base url, so use full name
                    _path = base_url
                # set base paths
                base_path = os.path.join( self.BASE_MAPS_PATH, subfolder, xbmc.getCacheThumbName( _path )[ : -4 ], filename )
                base_refresh_path = os.path.join( self.BASE_MAPS_PATH, subfolder, xbmc.getCacheThumbName( _path )[ : -4 ], "refresh.txt" )
            # get expiration date
            expires, refresh = self._get_expiration_date( base_path, base_refresh_path, refreshtime )
            # only fetch source if it's been longer than refresh time or does not exist
            if ( base_path and not os.path.isfile( base_path ) or refresh ):
                # add headers only if this is the first try
                if ( retry ):
                    headers.update( {
                        "User-Agent": "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
                        "Accept": "image/gif, image/jpeg, image/pjpeg, application/x-shockwave-flash, application/x-ms-application, application/x-ms-xbap, application/vnd.ms-xpsdocument, application/xaml+xml, */*",
                        "Accept-Language": "en-us",
                        "Connection": "Keep-Alive"
                        #"Accept-Encoding": "text",
                        #"Host": "www.weather.com",
                    } )
                # request base url
                request = urllib2.Request( base_url, headers=headers )
                # open requested url
                usock = urllib2.urlopen( request )
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
                # TODO: this is so rare, but try and determine if 3 seconds is enough
                xbmc.log( "Trying url %s one more time." % ( base_url, ), xbmc.LOGDEBUG )
                time.sleep( 3 )
                # try one more time
                return self._fetch_data( base_url, refreshtime, filename, animated, subfolder, False, headers )
            else:
                # we've already retried, return ""
                xbmc.log( "Second error 503 for %s, increase sleep time." % ( base_url, ), xbmc.LOGDEBUG )
                return ""
        except Exception, e:
            # oops log error message
            xbmc.log( "WeatherClient::_fetch_data (%s)" % ( e, ), xbmc.LOGERROR )
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
                # read expiration date
                expires = float( open( base_refresh_path, "rb" ).read() )
            # see if necessary to refresh source
            refresh = ( ( time.mktime( time.gmtime() ) * ( refreshtime != 0 ) ) > expires )
        except Exception, e:
            # oops log error message
            xbmc.log( "WeatherClient::_get_expiration_date (%s)" % ( e, ), xbmc.LOGERROR )
        # return expiration date
        return expires, refresh

    def _save_data( self, data, _path ):
        try:
            # if the base path does not exist create it
            if ( not os.path.isdir( os.path.dirname( _path ) ) ):
                os.makedirs( os.path.dirname( _path ) )
            # save data
            open( _path, "wb" ).write( data )
        except Exception, e:
            # oops log error message
            xbmc.log( "WeatherClient::_save_data (%s)" % ( e, ), xbmc.LOGERROR )


if ( __name__ == "__main__" ):
    #import urllib
    #print urllib.quote( "&" )
    #raise
    code = "USMI0564"#"USOH0251"#"USCA0806"#"USAK0025"#"USNY0996"#"USMD0018"#"USME0146"#USME0013"#"USMI0564"#"USWA0441"#"USOR0111"#"USOR0098"#"USGA0028"#"USAR0170"#"NZXX0006"#"USMI0405"#"USMI0508"#"NZXX0006"#"CAXX0343"#
    client = WeatherClient( code, Addon=xbmcaddon.Addon( "script.weather.com.plus" ) )
    MAP_TYPE = 30901#30904
    MAP_NO = 0#8
    print "MAP LIST - %s" % MAP_TYPE
    category_title, map_list = client.fetch_map_list( MAP_TYPE, r"", "1" )
    print "CT", category_title, map_list
    #for map in map_list:
    #    print '            <map title="%s">' % map[ 1 ]
    #    print '                <map_url>%s</map_url>' % map[ 0 ]
    #    print '            </map>'
    print "MAP URLS", map_list[ MAP_NO ]
    maps = client.fetch_map_urls( map_list[ MAP_NO ][ 0 ], r"F:\source\_XBMC_\plugins\weather\weather.com plus\resources\samples\sample-user-defined-maps.udm", map_list[ MAP_NO ][ 2 ] )
    print
    print maps
    print "IMAGES"
    mapspath, legendpath = client.fetch_images( maps )
    print "maps", mapspath
    print "legend", legendpath
    """
    print
    print "ALERTS & CURRENT CONDITIONS"
    # fetch 36 hour forecast
    alerts, alertsrss, alertsnotify, alertscolor, alertscount, forecasts = client.fetch_36hour_forecast()
    #print "Video:", videos
    print "Alerts Color:", alertscolor
    print "Alerts RSS", alertsrss
    print "Alerts notify", alertsnotify
    print "Alerts count", alertscount
    print alerts
    print "-------------------"
    for forecast in forecasts:
        print repr(forecast)
    print
    print "TEN DAY FORECAST"
    forecasts = client.fetch_10day_forecast()
    for forecast in forecasts:
        print repr( forecast )
    print
    print "WEEKEND FORECAST"
    forecasts = client.fetch_weekend_forecast()
    for forecast in forecasts:
        print repr( forecast )
    print
    print "HOURLY FORECAST"
    forecasts = client.fetch_hourly_forecast()
    for forecast in forecasts:
        print repr( forecast )
    print
    """
