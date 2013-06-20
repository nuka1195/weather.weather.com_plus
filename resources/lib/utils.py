## Utilities module

import sys
import os

try:
    import xbmc
    import xbmcgui
    import xbmcaddon
except:
    # get dummy xbmc modules (Debugging)
    from debug import *
    xbmc = XBMC()
    xbmcgui = XBMCGUI()
    xbmcaddon = XBMCADDON()

# Addon class
Addon = xbmcaddon.Addon( id="script.weather.com.plus" )


class Viewer:
    # we need regex for parsing info
    import re
    # constants
    WINDOW = 10147
    CONTROL_LABEL = 1
    CONTROL_TEXTBOX = 5

    def __init__( self, *args, **kwargs ):
        # activate the text viewer window
        xbmc.executebuiltin( "ActivateWindow(%d)" % ( self.WINDOW, ) )
        # get window
        window = xbmcgui.Window( self.WINDOW )
        # give window time to initialize
        xbmc.sleep( 100 )
        # set message
        msg = { "updates": 30760, "changelog": 30761, "readme": 30762, "license": 30763, "properties": 30764 }[ kwargs[ "kind" ] ]
        # set heading
        window.getControl( self.CONTROL_LABEL ).setLabel( "%s - %s" % ( Addon.getLocalizedString( msg + 5 ), Addon.getAddonInfo( "Name" ), ) )
        # set fetching message
        window.getControl( self.CONTROL_TEXTBOX ).setText( Addon.getLocalizedString( msg ) )
        # fetch correct info
        try:
            if ( kwargs[ "kind" ] in [ "updates", "changelog" ] ):
                text = self._fetch_changelog( kwargs[ "kind" ] )
            elif ( kwargs[ "kind" ] in [ "readme", "license" ] ):
                text = self._fetch_text_file( kwargs[ "kind" ] )
            elif ( kwargs[ "kind" ] == "properties" ):
                text = self._fetch_properties()
        except Exception, e:
            # set error message
            text = "%s[CR][CR]%s" % ( Addon.getLocalizedString( 30771 ) % ( Addon.getLocalizedString( msg + 5 ), ), e, )
        # set text
        window.getControl( self.CONTROL_TEXTBOX ).setText( text )

    def _fetch_changelog( self, kind ):
        # import required modules
        import datetime
        import pysvn
        # get our regions format
        date_format = "%s %s" % ( xbmc.getRegion( "datelong" ), xbmc.getRegion( "time" ), )
        # get client
        client = pysvn.Client()
        client.callback_cancel = self._pysvn_cancel_callback
        try:
            # grab current revision and repo url
            info = client.info( path=Addon.getAddonInfo( "Path" ) )
            # fetch changelog for current revision
            if ( kind == "changelog" ):
                log = client.log( url_or_path=info[ "url" ], limit=25, revision_start=pysvn.Revision( pysvn.opt_revision_kind.number, info[ "commit_revision" ].number ) )
            # updates
            else:
                log = client.log( url_or_path=info[ "url" ], limit=25, revision_end=pysvn.Revision( pysvn.opt_revision_kind.number, info[ "commit_revision" ].number + 1 ) )
        except:
            # changelog
            log = client.log( url_or_path="http://xbmc-addons.googlecode.com/svn/addons/%s" % ( Addon.getAddonInfo( "Id" ), ), limit=25 )
        # if no entries set user message
        if ( len( log ) ):
            # initialize our log variable
            changelog = "%s\n" % ( "-" * 150, )
        else:
            # should only happen for "updates" and there are none
            changelog = Addon.getLocalizedString( 30704 )
        # we need to compile so we can add DOTALL
        clean_entry = self.re.compile( "\[.+?\][\s]+(?P<name>[^\[]+)(?:\[.+)?", self.re.DOTALL )
        # iterate thru and format each message
        for entry in log:
            # add heading
            changelog += "r%d - %s - %s\n\n" % ( entry[ "revision" ].number, datetime.datetime.fromtimestamp( entry[ "date" ] ).strftime( date_format ), entry[ "author" ], )
            # add formatted message
            changelog += "\n".join( [ self.re.sub( "(?P<name>^[a-zA-Z])", "- \\1", line.lstrip( " -" ) ) for line in clean_entry.sub( "\\1", entry[ "message" ] ).strip().splitlines() ] )
            # add separator
            changelog += "\n%s\n" % ( "-" * 150, )
        # return colorized result
        return self._colorize_text( changelog )

    def _pysvn_cancel_callback( self ):
        # check if user cancelled operation
        return False

    def _fetch_text_file( self, kind ):
        # set path, first try translated version
        _path = os.path.join( Addon.getAddonInfo( "Path" ), "%s-%s.txt" % ( kind, xbmc.getRegion( "locale" ), ) )
        # if doesn't exist, use default
        if ( not os.path.isfile( _path ) ):
            _path = os.path.join( Addon.getAddonInfo( "Path" ), "%s.txt" % ( kind, ) )
        # read  file
        text = open( _path, "r" ).read()
        # return colorized result
        return text##self._colorize_text( text )

    def _fetch_properties( self ):
        # get python source, we set properties in main py file
        pySource = open( os.path.join( os.path.dirname( __file__ ), "weather.py" ), "r" ).read()
        # get properties set by addon, we use a dict to eliminate duplicates
        properties = dict( self.re.findall( "self.WINDOW.setProperty\(.*?\"([^\"]+)\"()", pySource ) ).keys()
        properties.sort()
        # get skin strings used by addon, we use a dict to eliminate duplicates
        skinstrings = dict( self.re.findall( "(Skin.String\([^\)]+\))()", pySource ) ).keys()
        skinstrings.sort()
        # add user message header
        text = "[I]%s[/I]\n\n" % ( Addon.getLocalizedString( 30840 ), )
        # add skin strings header
        text += "[B]%s[/B]\n%s\n" % ( Addon.getLocalizedString( 30841 ), "-" * 150, )
        # loop thru and add skin strings
        for skinstring in skinstrings:
            text += skinstring + "\n"
        # add ending divider
        text += "%s\n\n" % ( "-" * 150, )
        # add window properties header
        text += "[B]%s[/B]\n%s" % ( Addon.getLocalizedString( 30842 ), "-" * 150, )
        # variable used to separate weather forecasts
        category = ""
        # loop thru and add properties
        for property in properties:
            # if new category we want a newline inserted
            newcategory = [ "", "\n" ][ category != property[ : 4 ] ]
            # set current category
            category = property[ : 4 ]
            # 36 hour and weekend have 3 sets
            if ( property.startswith( "36Hour.%d" ) or property.startswith( "Weekend.%d" ) ):
                property = property.replace( "%d", "[1-3]" )
            # map list has 30 sets
            elif ( property.startswith( "MapList.%d" ) ):
                property = property.replace( "%d", "[1-30]" )
            # hourly has 12 sets
            elif ( property.startswith( "Hourly.%d" ) ):
                property = property.replace( "%d", "[1-12]" )
            # 10Day has 10 sets
            elif ( property.startswith( "10Day.%d" ) ):
                property = property.replace( "%d", "[1-10]" )
            # append formatted property
            text += "%sWindow(Weather).Property(%s)\n" % ( newcategory, property, )
        # add ending divider
        text += "%s\n" % ( "-" * 150, )
        # log properties for easy copying
        xbmc.log( text, level=xbmc.LOGNOTICE )
        # return text
        return text

    def _colorize_text( self, text ):
        # format text using colors
        text = self.re.sub( "(?P<name>r[0-9]+ - .+?)(?P<name2>[\r\n]+)", "[COLOR FF0084FF]\\1[/COLOR]\\2", text )
        text = self.re.sub( "(?P<name>http://[\S]+)", "[COLOR FFEB9E17]\\1[/COLOR]", text )
        text = self.re.sub( "(?P<name>[^\]]r[0-9]+)", "[COLOR FFEB9E17]\\1[/COLOR]", text )
        text = self.re.sub( "(?P<name>\".+?\")", "[COLOR FFEB9E17]\\1[/COLOR]", text )
        text = self.re.sub( "(?P<name>[A-Z ]+:)[\r\n]+", "[COLOR FF0084FF][B]\\1[/B][/COLOR]\n", text )
        text = self.re.sub( "(?P<name> - )", "[COLOR FFFFFFFF]\\1[/COLOR]", text )
        text = self.re.sub( "(?P<name>-[-]+)", "[COLOR FFFFFFFF]\\1[/COLOR]", text )
        # return colorized text
        return text


def _fetch_local_video_list():
    # inform user
    dialog = xbmcgui.DialogProgress()
    dialog.create( Addon.getAddonInfo( "Name" ), Addon.getLocalizedString( 30800 ) )
    dialog.update( 0 )
    # import weather client
    from WeatherClient import WeatherClient
    # fetch video list
    ok = WeatherClient( Addon=Addon ).fetch_local_video_list( refresh=True )
    # set video list fetched message
    msg = [ 30802, 30801 ][ ok ]
    # close progress dialog
    dialog.close()
    # notify user of status
    ok = xbmcgui.Dialog().ok( Addon.getAddonInfo( "Name" ), Addon.getLocalizedString( msg ) )


if ( __name__ == "__main__" ):
    # need this while debugging
    if ( len( sys.argv ) == 1 ):
        sys.argv.append( "properties" )
    # upate local video list
    if ( sys.argv[ 1 ] == "fetchlocalvideolist" ):
        _fetch_local_video_list()
    # show info
    elif ( sys.argv[ 1 ] in [ "updates", "changelog", "readme", "license", "properties" ] ):
        Viewer( kind=sys.argv[ 1 ] )
