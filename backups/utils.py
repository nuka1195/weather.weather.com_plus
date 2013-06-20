""" helper functions """
try:
    import xbmc
    import xbmcgui
    import xbmcaddon
    DEBUG = False
except:
    DEBUG = True

import os
import sys

if ( not DEBUG ):
    # get the addon info method from Addons class
    Addon = xbmcaddon.Addon( id=os.path.basename( os.getcwd() ) )

    def LOG( text, level=xbmc.LOGNOTICE, heading=False ):
        # log a heading
        if ( heading ):
            xbmc.log( "-" * 70, level )
        # log message
        xbmc.log( text, level )
        # log a footer
        if ( heading ):
            xbmc.log( "-" * 70, level )

    def check_compatible():
        # check compatible
        try:
            # get xbmc revision
            xbmc_rev = int( xbmc.getInfoLabel( "System.BuildVersion" ).split( " r" )[ -1 ][ : 5 ] )
            # compatible?
            ok = 2#xbmc_rev >= Addon.getAddonInfo( "XBMC_MinRevision" )
        except:
            # error, so unknown, allow to run
            xbmc_rev = 0
            ok = 2
        # spam scripts statistics to log
        LOG( "=" * 80, xbmc.LOGNOTICE )
        LOG( "[ADD-ON] - %s initialized!" % ( Addon.getAddonInfo( "Name" ), ), xbmc.LOGNOTICE )
        LOG( "           Id: %s - Type: %s - Version: %s" % ( Addon.getAddonInfo( "Id" ), Addon.getAddonInfo( "Type" ), Addon.getAddonInfo( "Version" ).replace( "$", "" ).replace( "Revision", "" ).strip() ), xbmc.LOGNOTICE )
        #LOG( "           Required XBMC Revision: r%d" % ( Addon.getAddonInfo( "XBMC_MinRevision" ), ), xbmc.LOGNOTICE )
        #LOG( "           Found XBMC Revision: r%d [%s]" % ( xbmc_rev, [ "Not Compatible", "Compatible", "Unknown" ][ ok ], ), xbmc.LOGNOTICE )
        LOG( "=" * 80, xbmc.LOGNOTICE )
        # TODO: if the error dialog is fixed or we can end directory with false and not have an error message, use this
        """
        # if not compatible, inform user
        if ( not ok ):
            # display error message
            xbmcgui.Dialog().ok( "%s - %s: %s" % ( Addon.getAddonInfo( "Name" ), Addon.getLocalizedString( 30700 ), Addon.getAddonInfo( "Version" ), ), Addon.getLocalizedString( 30701 ) % ( Addon.getAddonInfo( "Name" ), ), Addon.getLocalizedString( 30702 ) % ( Addon.getAddonInfo( "XBMC_MinRevision" ), ), Addon.getLocalizedString( 30703 ) )
        """
        #return result
        return ok

    def get_keyboard( default="", heading="", hidden=False ):
        """ shows a keyboard and returns a value """
        # show keyboard for input
        keyboard = xbmc.Keyboard( default, heading, hidden )
        keyboard.doModal()
        # return user input unless canceled
        if ( keyboard.isConfirmed() ):
            return keyboard.getText()
        # user canceled, return None
        return None

    def refresh_source( base_source_path ):
        # set base resources path
        base_source_path = xbmc.validatePath( os.path.join( Addon.getSetting( "source_cache_path" ), Addon.getSetting( "trailer_scraper" ).replace( " - ", "_" ).replace( " ", "_" ).lower(), "source" ) )
        #TODO: fix this for any source (REMOVE SOURCE FOLDER ENTIRELY)
        # iterate thru and delete all source xml files
        for source in [ "current.xml", "current_480p.xml", "current_720p.xml" ]:
            # set path and url
            base_path = os.path.join( base_source_path, source )
            # remove xml file
            try:
                os.remove( base_path )
            except:
                # log error message
                LOG( "An error occurred removing '%s'" % ( base_path, ), level=xbmc.LOGERROR )
                # return failure
                return False
        # return success
        return True

    def get_legal_filepath( title, url, mode, download_path, use_title, use_trailer ):
        # TODO: find a better way
        import re
        # TODO: figure out how to determine download_path's filesystem, statvfs() not available on windows
        # get the filesystem the trailer will be saved to
        filesystem = [ os.environ.get( "OS", "xbox" ), "win32" ][ download_path.startswith( "smb://" ) ]
        # different os's have different illegal characters
        illegal_characters = { "xbox": '\\/:*?"<>|,=;+', "win32": '\\/:*?"<>|', "Linux": "/", "OS X": "/:" }[ filesystem ]
        # get a valid filepath
        if ( use_title ):
            # append "-trailer" if user preference
            title = u"%s%s%s" % ( title, [ u"", u"-trailer" ][ use_trailer ], os.path.splitext( url )[ 1 ], )
        else:
            # append "-trailer" if user preference
            title = u"%s%s%s" % ( os.path.splitext( os.path.basename( url ) )[ 0 ], [ u"", u"-trailer" ][ use_trailer ], os.path.splitext( os.path.basename( url ) )[ 1 ], )
        # clean the filename
        filename = re.sub( '[%s]' % ( illegal_characters, ), u"", title )
        # we need to handle xbox special
        if ( filesystem == "xbox" ):
            # set the length to 37 if filepath isn't a smb share for the .conf file
            if( len( filename ) > 37 and not download_path.startswith( "smb://" ) ):
                name, ext = os.path.splitext( filename )
                filename = name[ : 37 - len( ext ) ].strip() + ext
            # replace any characters whose ord > 127
            for char in filename:
                if ( ord( char ) > 127 ):
                    filename = filename.replace( char, "_" )
        # make our filepath
        filepath = savedpath = os.path.join( xbmc.translatePath( download_path ), filename )
        # if play_mode is temp download to cache folder
        if ( mode == 1 ):
            filepath = xbmc.translatePath( "special://temp/%s" % ( os.path.basename( url ), ) )
        # return results
        return filepath, savedpath

    def get_thumb_cachename():
        #cachename is based on listitems url
        cachename = xbmc.getCacheThumbName( sys.argv[ 0 ] + sys.argv[ 2 ] )
        # return full path to thumbnail
        return os.path.join( xbmc.translatePath( "special://profile/" ), "Thumbnails", "Video", cachename[ 0 ], cachename )

    def translatePath( filepath ):
        # translate any special:// paths
        filepath = xbmc.translatePath( xbmc.validatePath( filepath ) )
        # if windows and samba convert to a proper format for shutil and os modules
        if ( os.environ.get( "OS", "win32" ) == "win32" and filepath.startswith( "smb://" ) ):
            filepath = filepath.replace( "/", "\\" ).replace( "smb:", "" )
        # return result
        return filepath

    def makedirs( path ):
        if ( os.path.isdir( path ) ): return
        w_path = path
        while ( not os.path.isdir( w_path ) ):
            try:
                os.mkdir( translatePath( w_path ) )
            except:
                w_path = os.path.dirname( w_path )
        makedirs( path )

    def _search():
        # spam log file
        LOG( ">>> _search()", heading=True )
        # get default search terms
        default = xbmcgui.Window( xbmcgui.getCurrentWindowId() ).getProperty( "Plugin.Search.Text" )
        # get search keywords
        text = get_keyboard( default=default, heading=Addon.getLocalizedString( 30731 ) )
        # skip if user cancels keyboard
        if ( text != None ):
            # set property for next search
            xbmcgui.Window( xbmcgui.getCurrentWindowId() ).setProperty( "Plugin.Search.Text", text )
            # spam search term
            LOG( "search for: %s" % ( text, ), heading=True )
            # we need to quote and unquote
            from urllib import quote_plus, unquote_plus
            # execute our action
            xbmc.executebuiltin( "Container.Update(%s?category=%s,replace)" % ( unquote_plus( sys.argv[ 1 ] ), quote_plus( repr( u"search: " + text ) ), ) )
        # spam log file
        LOG( "<<< _search()", heading=True )

class Viewer:
    import re

    def __init__( self, *args, **kwargs ):
        try:
            # set initial message
            if ( not DEBUG ):
                # we need to grab the dialog window before the progress dialog
                self.window = xbmcgui.Window( xbmcgui.getCurrentWindowDialogId() )
                # inform user our status
                self.dialog = xbmcgui.DialogProgress()
                self.dialog.create( Addon.getAddonInfo( "Name" ), { "changelog": Addon.getLocalizedString( 30760 ), "readme": Addon.getLocalizedString( 30761 ), "updates": Addon.getLocalizedString( 30762 ) }[ kwargs[ "kind" ] ] )
            # fetch correct info
            if ( kwargs[ "kind" ] == "readme" ):
                text = self._fetch_readme()
            else:
                text = self._fetch_changelog( kwargs[ "kind" ] )
        except Exception, e:
            # no localization for DEBUG
            if ( DEBUG ):
                text = "An error occurred fetching %s!\n\n%s" % ( kwargs[ "kind" ], str( e ), )
            elif ( not self.dialog.iscanceled() ):
                text = Addon.getLocalizedString( 30766 ) % ( { "changelog": Addon.getLocalizedString( 30763 ), "readme": Addon.getLocalizedString( 30764 ), "updates": Addon.getLocalizedString( 30765 ) }[ kwargs[ "kind" ] ], str( e ), )
            # set kind to None so xbmc will run again
            kwargs[ "kind" ] = None
        # set initial message
        if ( not DEBUG ):
            self.dialog.close()
        # only set text if user did not cancel
        if ( DEBUG or not self.dialog.iscanceled() ):
            self._set_text( text, kwargs[ "kind" ] )
        else:
            self.window.setProperty( "AddonSettingsSubtitle", xbmc.getLocalizedString( 5 ) );

    def _pysvn_cancel_callback( self ):
        # check if user cancelled operation
        if ( not DEBUG ):
            return self.dialog.iscanceled()
        return False

    def _fetch_changelog( self, kind ):
        # import required modules
        import datetime
        import pysvn
        # get our regions format and correct path
        if ( DEBUG ):
            date_format = "%x %X"
            path = os.path.dirname( os.path.dirname( os.getcwd() ) )
        else:
            date_format = xbmc.getRegion( "datelong" ).replace( "DDDD,", "%a," ).replace( "MMMM", "%B" ).replace( "D", "%d" ).replace( "YYYY", "%Y" ).strip()
            date_format = "%s %s" % ( date_format, xbmc.getRegion( "time" ).replace( "xx", "%p" ).replace( "H", "%H" ).replace( "h", "%I" ).replace( "mm", "%M" ).replace( "ss", "%S" ), )
            path = os.getcwd()
        # get client
        client = pysvn.Client()
        client.callback_cancel = self._pysvn_cancel_callback
        # grab current revision and repo url
        info = client.info( path=path )
        # fetch log for current revision
        if ( kind == "changelog" ):
            # changelog
            log = client.log( url_or_path=info[ "url" ], limit=25, revision_start=pysvn.Revision( pysvn.opt_revision_kind.number, info[ "commit_revision" ].number ) )
        else:
            # updates
            log = client.log( url_or_path=info[ "url" ], limit=25, revision_end=pysvn.Revision( pysvn.opt_revision_kind.number, info[ "commit_revision" ].number + 1 ) )
        # if no entries set user message
        if ( len( log ) ):
            # initialize our log variable
            changelog = "%s\n" % ( "-" * 150, )
        else:
            if ( DEBUG ):
                changelog = "Your version is up to date."
            else:
                changelog = Addon.getLocalizedString( 30704 )
        # we need to compile so we can add DOTALL
        clean_entry = self.re.compile( "\[.+?\][\s]+(?P<name>[^\[]+)(?:\[.+)?", self.re.DOTALL )
        # iterate thru and format each message
        for entry in log:
            # add heading
            changelog += "r%d - %s - %s\n\n" % ( entry[ "revision" ].number, datetime.datetime.fromtimestamp( entry[ "date" ] ).strftime( date_format ), entry[ "author" ], )
            # add formatted message  "\[.+?\][\s]+(?P<name>[^\[]+)", "\\1"
            changelog += "\n".join( [ self.re.sub( "(?P<name>^[a-zA-Z])", "- \\1", line.lstrip( " -" ) ) for line in clean_entry.sub( "\\1", entry[ "message" ] ).strip().splitlines() ] )
            # add separator
            changelog += "\n%s\n" % ( "-" * 150, )
        # return colorized result
        return self._colorize_text( changelog )

    def _fetch_readme( self ):
        # fetch readme
        if ( DEBUG ):
            path = os.path.join( os.getcwd(), "..\\readme.txt" )
        else:
            path = os.path.join( os.getcwd(), "resources", "readme.txt" )
        # open file
        f = open( path, "r" )
        # read text
        readme = f.read()
        # close file
        f.close()
        # needed for indentation, only if not debugging
        if ( not DEBUG ):
            readme = self.re.sub( "  ", "[COLOR 00FFFFFF]__[/COLOR]", readme )
        # return colorized result
        return self._colorize_text( readme )

    def _colorize_text( self, text ):
        # only colorize if not debugging
        if ( not DEBUG ):
            text = self.re.sub( "(?P<name>r[0-9]+ - .+?)(?P<name2>[\r\n]+)", "[COLOR FF0084FF]\\1[/COLOR]\\2", text )
            text = self.re.sub( "(?P<name>http://[\S]+)", "[COLOR FFEB9E17]\\1[/COLOR]", text )
            text = self.re.sub( "(?P<name>[^\]]r[0-9]+)", "[COLOR FFEB9E17]\\1[/COLOR]", text )
            text = self.re.sub( "(?P<name>\".+?\")", "[COLOR FFEB9E17]\\1[/COLOR]", text )
            text = self.re.sub( "(?P<name>[A-Z ]+:)[\r\n]+", "[COLOR FF0084FF][B]\\1[/B][/COLOR]\r\n", text )
            text = self.re.sub( "(?P<name> - )", "[COLOR FFFFFFFF]\\1[/COLOR]", text )
            text = self.re.sub( "(?P<name>-[-]+)", "[COLOR FFFFFFFF]\\1[/COLOR]", text )
        # return colorized text
        return text

    def _set_text( self, text, kind=None ):
        # set text
        if ( DEBUG ):
            print text
        else:
            # set PluginChangelog or PluginReadme
            if ( kind is not None ):
                self.window.setProperty( "AddonSettings%s" % ( kind, ), text )
            # now we need to set PluginInfoText, since that is what we use to display
            self.window.setProperty( "AddonSettingsInfoText", text )

if ( __name__ == "__main__" ):
    item = [ "readme", "changelog", "updates" ]
    Viewer( kind=item[ 0 ] )
