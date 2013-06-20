""" Package manager for addons """

import sys
import os
import xbmc
import xbmcgui

try:
    import xbmcaddon
except:
    # get xbox compatibility module
    from xbox import *
    xbmcaddon = XBMCADDON()

import urllib
import time


class PackageMgr:
    # Addon class
    Addon = xbmcaddon.Addon( id=os.path.basename( os.path.dirname( os.path.dirname( os.getcwd() ) ) ) )

    def __init__( self, package=None ):
        # class wide progress dialog, maybe smoother
        self.pDialog = xbmcgui.DialogProgress()
        # set initial message to successful
        self.message = 30720
        # select correct url for package
        if ( package == "mappack" ):
            package_url = self._get_package_version()
            # this is used to add extra info to settings
            include_package_name = True
        # check for previous package download
        self._check_previous_download_info( package=package )
        # now get the path to download to
        installation_path = self._get_installation_path()
        # only proceed if download path was set
        if ( installation_path == "" ):
            self.message = 30723
        else:
            # download package
            self._download_package( url=package_url, path=installation_path )
            # write message to settings to inform user unless cancelled by user
            if ( self.message != 30723 ):
                self._save_setting( setting=package, path=installation_path, filename=os.path.basename( package_url ), include=include_package_name )
        # inform user of success or failure
        self._inform_user( url=package_url, path=self.Addon.getLocalizedString( 30712 ) % ( installation_path, ) )

    def _save_setting( self, setting, path, filename, include ):
        # set proper setting value
        value = ( self.Addon.getLocalizedString( 30728 ), self.Addon.getLocalizedString( 30729 ), )[ self.message == 30720 ]
        # set proper path
        path = ( "", path, )[ self.message == 30720 ]
        # we add packages filename to value if include`and successful
        if ( include and self.message == 30720 ):
            value += " - %s" % ( filename, )
        # mark package as installed or failed
        self.Addon.setSetting( "install_%s" % ( setting, ), value )
        self.Addon.setSetting( "install_%s_path" % ( setting, ), path )
        # set TWC.MapsIconPath skin setting, so icons work immediately
        if ( path ):
            xbmc.executebuiltin( "Skin.SetString(TWC.MapsIconPath,%s)" % ( path, ) ) 

    def _inform_user( self, url, path ):
        # set filename
        filename = os.path.basename( url )
        # do not display if message is user cancelled
        path = ( "", path )[ self.message != 30723 ]
        # inform user of result
        ok = xbmcgui.Dialog().ok( self.Addon.getLocalizedString( 30001 ) % ( self.Addon.getAddonInfo( "Name" ), ), self.Addon.getLocalizedString( self.message ) % ( filename, ), path )

    def _get_package_version( self ):
        # ask user which pack
        package = xbmcgui.Dialog().yesno( self.Addon.getLocalizedString( 30001 ) % ( self.Addon.getAddonInfo( "Name" ), ), self.Addon.getLocalizedString( 30850 ), self.Addon.getLocalizedString( 30851 ), self.Addon.getLocalizedString( 30852 ), self.Addon.getLocalizedString( 30854 ), self.Addon.getLocalizedString( 30853 ), )
        # set proper url
        url = "http://xbmc-addons.googlecode.com/svn/packages/plugins/weather/weather.com%%20plus/%s" % ( ( "MapIconPack-small.zip", "MapIconPack-large.zip", )[ package == True ], )
        # return result
        return url

    # TODO: determine what to do with this
    def _check_previous_download_info( self, package ):
        # get path and date of download
        path = self.Addon.getSetting( "install_%s_path" % ( package, ) )
        date = self.Addon.getSetting( "install_%s_date" % ( package, ) )

    def _get_installation_path( self ):
        # get user input
        value = xbmcgui.Dialog().browse( 3, self.Addon.getLocalizedString( 30735 ), "files", "", False, False, "" )
        # return value
        return value

    def _download_package( self, url, path ):
        # set filename
        self.filename = os.path.basename( url )
        # temporary download path
        self.tmp_path = os.path.join( "special://temp", self.filename )
        try:
            # create dialog
            self.pDialog.create( self.Addon.getLocalizedString( 30001 ) % ( self.Addon.getAddonInfo( "Name" ), ) )
            # get current time
            self.start_time = self.elapsed_time = time.time()
            # fetch package
            urllib.urlretrieve( url , xbmc.translatePath( self.tmp_path ), self._report_hook )
            # extract package
            self._extract_package( path=path )
        except:
            # set error message
            self.message = ( self.message, 30722, )[ self.message == 30720 ]
            # close dialog
            self.pDialog.close()

    def _report_hook( self, count, blocksize, totalsize ):
        def _format_bytes( bytes ):
            # calculate megabytes
            MB = float( bytes ) / 1024 /1024
            # calculate kilobytes
            kB = float( bytes ) / 1024
            # return correct format
            return [ "%i%s" % ( bytes, self.Addon.getLocalizedString( 30714 ), ), "%i%s" % ( kB, self.Addon.getLocalizedString( 30715 ), ), "%3.1f%s" % ( MB, self.Addon.getLocalizedString( 30716 ), ) ][ ( kB >= 1 ) + ( MB >= 1 ) ]

        def _calc_speed( bytes, now ):
            # calculate time elapsed
            elapsed = now - self.start_time
            # format string and return speed
            return "%s/s" % ( _format_bytes( float( bytes ) / elapsed ), )

        def _calc_eta( bytes, now, totalsize ):
            # calculate time elapsed
            elapsed = now - self.start_time
            # calculate eta
            eta = long( ( float( totalsize ) - float( bytes ) ) / ( float( bytes ) / elapsed ) )
            # separate minutes/seconds and format string
            return "%02d:%02d" % divmod( eta, 60 )
        # raise an error if user cancelled dialog
        if ( self.pDialog.iscanceled() ):
            # set error message
            self.message = 30723
            # raise the error
            raise
        # get current time
        now = time.time()
        # only update every ?????????????????????? TODO: remove or adjust this if the message isn't stable
        if ( ( now - self.elapsed_time ) < .2 or count == 0 ): return
        # reset elapsed time
        self.elapsed_time = now
        # calculate percent done
        percent = int( float( count * blocksize * 100 ) / totalsize )
        # set messages
        msg1 = self.Addon.getLocalizedString( 30710 ) % ( self.filename, )
        msg2 = self.Addon.getLocalizedString( 30712 ) % ( os.path.dirname( self.tmp_path ), )
        msg3 = "%s %s %s %s %s %s %s" % ( _format_bytes( count * blocksize ), self.Addon.getLocalizedString( 30717 ), _format_bytes( totalsize ), self.Addon.getLocalizedString( 30718 ), _calc_speed( count * blocksize, now ), self.Addon.getLocalizedString( 30719 ), _calc_eta( count * blocksize, now, totalsize ), )
        # update dialog
        self.pDialog.update( percent, msg1, msg2, msg3 )

    def _extract_package( self, path ):
        try:
            # extract if zip or rar file
            if ( self.filename.endswith( ".zip" ) or self.filename.endswith( ".rar" ) ):
                # create dialog
                self.pDialog.update( 0, self.Addon.getLocalizedString( 30713 ) % ( self.filename, ), self.Addon.getLocalizedString( 30712 ) % ( os.path.dirname( path ), ), "" )
                # this is needed?
                xbmc.sleep( 30 )
                # extract package
                xbmc.executebuiltin( "XBMC.Extract(%s,%s)" % ( self.tmp_path, path, ) )
        except: 
            # set error message
            self.message = 30721
        try:
            # close dialog
            self.pDialog.close()
        except:
            pass


if ( __name__ == "__main__" ):
    PackageMgr( sys.argv[ 1 ].split( "=" )[ 1 ] )
