## Package manager for addons

import sys
import os
import xbmc
import xbmcgui
import xbmcaddon
import urllib
import time


class PackageMgr:
    # Addon class
    Addon = xbmcaddon.Addon(id=os.path.basename(os.path.dirname(os.path.dirname(os.getcwd()))))

    def __init__(self):
        # class wide progress dialog, maybe smoother
        self.pDialog = xbmcgui.DialogProgress()
        # set initial message to successful
        self.message = 30780
        # parse argv for any params
        params = self._parse_argv()
        # set correct url for package
        package_url = self._get_package_url(params[ "package" ])
        # check for previous package download
        self._check_previous_download_info(id=params[ "id" ])
        # now get the path to download to
        installation_path = self._get_installation_path()
        # only proceed if download path was set
        if (installation_path == ""):
            self.message = 30783
        else:
            # download package
            self._download_package(url=package_url, path=installation_path)
            # write message to settings to inform user unless cancelled by user
            if (self.message != 30783):
                self._save_setting(id=params[ "id" ], path=installation_path, filename=os.path.basename(package_url), skinsetting=params[ "id" ])
        # inform user of success or failure
        self._inform_user(url=package_url, path=self.Addon.getLocalizedString(30712) % (installation_path,))

    def _parse_argv(self):
        # parse sys.argv for params and return result
        params = dict(arg.split("=") for arg in sys.argv[ 1 ].split("&"))
        # return params
        return params

    def _get_package_url(self, package):
        # set proper url
        url = "http://xbmc-addons.googlecode.com/svn/packages/addons/%s/%s" % (self.Addon.getAddonInfo("Id"), package,)
        # return result
        return url

    # TODO: determine what to do with this
    def _check_previous_download_info(self, id):
        # get path and date of download
        path = self.Addon.getSetting("%s_path" % (id,))
        date = self.Addon.getSetting("%s_date" % (id,))

    def _get_installation_path(self):
        # get user input
        value = xbmcgui.Dialog().browse(3, self.Addon.getLocalizedString(30735), "files", "", False, False, "")
        # return value
        return value

    def _save_setting(self, id, path, filename, skinsetting):
        # set proper setting value
        value = (self.Addon.getLocalizedString(30788), self.Addon.getLocalizedString(30789),)[ self.message == 30780 ]
        # set proper path
        path = ("", path,)[ self.message == 30780 ]
        # mark package as installed or failed
        self.Addon.setSetting(id, value)
        self.Addon.setSetting("%s_path" % (id,), path)
        self.Addon.setSetting("%s_date" % (id,), xbmc.getInfoLabel("System.Date"))
        # set skin setting if required
        if (skinsetting and path):
            xbmc.executebuiltin("Skin.SetString(%s,%s)" % (skinsetting, path,))

    def _inform_user(self, url, path):
        # set filename
        filename = os.path.basename(url)
        # do not display if message is user cancelled
        path = ("", path)[ self.message != 30783 ]
        # inform user of result
        ok = xbmcgui.Dialog().ok(self.Addon.getLocalizedString(30001) % (self.Addon.getAddonInfo("Name"),), self.Addon.getLocalizedString(self.message) % (filename,), path)

    def _download_package(self, url, path):
        # set filename
        self.filename = os.path.basename(url)
        # temporary download path
        self.tmp_path = os.path.join("special://temp", self.filename)
        try:
            # create dialog
            self.pDialog.create(self.Addon.getLocalizedString(30001) % (self.Addon.getAddonInfo("Name"),))
            # get current time
            self.start_time = self.elapsed_time = time.time()
            # fetch package
            urllib.urlretrieve(url , xbmc.translatePath(self.tmp_path), self._report_hook)
            # extract package
            self._extract_package(path=path)
        except:
            # set error message
            self.message = (self.message, 30782,)[ self.message == 30780 ]
            # close dialog
            self.pDialog.close()

    def _report_hook(self, count, blocksize, totalsize):
        def _format_bytes(bytes):
            # calculate megabytes
            MB = float(bytes) / 1024 / 1024
            # calculate kilobytes
            kB = float(bytes) / 1024
            # return correct format
            return [ "%i%s" % (bytes, self.Addon.getLocalizedString(30714),), "%i%s" % (kB, self.Addon.getLocalizedString(30715),), "%3.1f%s" % (MB, self.Addon.getLocalizedString(30716),) ][ (kB >= 1) + (MB >= 1) ]

        def _calc_speed(bytes, now):
            # calculate time elapsed
            elapsed = now - self.start_time
            # format string and return speed
            return "%s/s" % (_format_bytes(float(bytes) / elapsed),)

        def _calc_eta(bytes, now, totalsize):
            # calculate time elapsed
            elapsed = now - self.start_time
            # calculate eta
            eta = long((float(totalsize) - float(bytes)) / (float(bytes) / elapsed))
            # separate minutes/seconds and format string
            return "%02d:%02d" % divmod(eta, 60)
        # raise an error if user cancelled dialog
        if (self.pDialog.iscanceled()):
            # set error message
            self.message = 30783
            # raise the error
            raise
        # get current time
        now = time.time()
        # only update every ?????????????????????? TODO: remove or adjust this if the message isn't stable
        if ((now - self.elapsed_time) < .2 or count == 0): return
        # reset elapsed time
        self.elapsed_time = now
        # calculate percent done
        percent = int(float(count * blocksize * 100) / totalsize)
        # set messages
        msg1 = self.Addon.getLocalizedString(30710) % (self.filename,)
        msg2 = self.Addon.getLocalizedString(30712) % (os.path.dirname(self.tmp_path),)
        msg3 = "%s %s %s %s %s %s %s" % (_format_bytes(count * blocksize), self.Addon.getLocalizedString(30717), _format_bytes(totalsize), self.Addon.getLocalizedString(30718), _calc_speed(count * blocksize, now), self.Addon.getLocalizedString(30719), _calc_eta(count * blocksize, now, totalsize),)
        # update dialog
        self.pDialog.update(percent, msg1, msg2, msg3)

    def _extract_package(self, path):
        try:
            # extract if zip or rar file
            if (self.filename.endswith(".zip") or self.filename.endswith(".rar")):
                # create dialog
                self.pDialog.update(0, self.Addon.getLocalizedString(30713) % (self.filename,), self.Addon.getLocalizedString(30712) % (os.path.dirname(path),), "")
                # this is needed?
                xbmc.sleep(30)
                # extract package
                xbmc.executebuiltin("XBMC.Extract(%s,%s)" % (self.tmp_path, path,))
        except:
            # set error message
            self.message = 30781
        try:
            # close dialog
            self.pDialog.close()
        except:
            pass


if (__name__ == "__main__"):
    PackageMgr()
