## Utilities module

import xbmc
import xbmcgui


class Utilities:
    """
        Utilities class:
            for running common tasks
    """

    def __init__(self, *args, **kwargs):
        # set our Addon class
        self.Addon = kwargs["addon"]
        # do work, #FIXME: this check is unnecessary?
        if (kwargs.has_key("function")):
            exec "self.{function}()".format(function=kwargs["function"])

    def check_for_updates(self):
        def _convert_version(version):
            # split parts into major, minor & micro
            parts = version.split(".")
            # return an integer value
            return int(parts[0]) * 100000 + int(parts[1]) * 1000 + int(parts[2])
        try:
            # import needed modules
            import re
            import urllib
            # create dialog
            pDialog = xbmcgui.DialogProgress()
            # give feedback
            pDialog.create(self.Addon.getAddonInfo("Name"), self.Addon.getLocalizedString(30760))
            pDialog.update(0)
            # url to addon.xml file
            url = "{repo}{branch}{id}/addon.xml".format(repo=self.Addon.getSetting("repo"), branch=self.Addon.getSetting("branch"), id=self.Addon.getAddonInfo("Id"))
            # get addon.xml source
            xml = urllib.urlopen(url).read()
            # parse version
            version = re.search("<addon.+?version\=\"(.+?)\".*?>", xml, re.DOTALL).group(1)
        except Exception as error:
            # set proper error messages
            msg1 = self.Addon.getLocalizedString(30770)
            msg2 = str(error)
        else:
            # set proper message
            msg1 = self.Addon.getLocalizedString(30700).format(version=self.Addon.getAddonInfo("Version"))
            msg2 = [self.Addon.getLocalizedString(30701), self.Addon.getLocalizedString(30702).format(version=version)][_convert_version(version) > _convert_version(self.Addon.getAddonInfo("Version"))]

        # done, close dialog
        pDialog.close()
        # notify user of result
        ok = xbmcgui.Dialog().ok(self.Addon.getAddonInfo("Name"), msg1, "", msg2)
