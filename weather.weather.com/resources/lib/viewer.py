## Viewer Module: View updates, changelog, readme, license and properties

import re
import os
import xbmc
import xbmcgui


class Viewer:
    """
        Viewer Class: View updates, changelog, readme, license and properties
    """
    # constants
    WINDOW_ID = 10147
    CONTROL_LABEL = 1
    CONTROL_TEXTBOX = 5

    def __init__(self, *args, **kwargs):
        # activate the text viewer window
        xbmc.executebuiltin("ActivateWindow({id})".format(id=self.WINDOW_ID))
        # get window
        window = xbmcgui.Window(self.WINDOW_ID)
        # set our Addon class
        self.Addon = kwargs["addon"]
        # set message
        msg = {"updates": 30760, "changelog": 30761, "readme": 30762, "license": 30763, "properties": 30764}[kwargs["kind"]]
        # give window time to initialize
        xbmc.sleep(100)
        # set heading
        window.getControl(self.CONTROL_LABEL).setLabel("{msg} - {name}".format(msg=self.Addon.getLocalizedString(msg + 5), name=self.Addon.getAddonInfo("Name")))
        # set fetching message
        window.getControl(self.CONTROL_TEXTBOX).setText(self.Addon.getLocalizedString(msg))
        # fetch correct info
        if (kwargs["kind"] in ["updates", "changelog"]):
            text = self._fetch_changelog(kwargs["kind"], msg=msg + 5)
        elif (kwargs["kind"] in ["readme", "license"]):
            text = self._fetch_text_file(kwargs["kind"], msg=msg + 5)
        elif (kwargs["kind"] == "properties"):
            text = self._fetch_properties(msg=msg + 5)
        # set text
        window.getControl(self.CONTROL_TEXTBOX).setText(text)

    def _fetch_changelog(self, kind, msg):
        def _pysvn_cancel_callback():
            # check if user cancelled operation
            return False
        # import required modules
        import datetime
        import pysvn
        # get our regions format
        date_format = "{date} {time}".format(date=xbmc.getRegion("datelong"), time=xbmc.getRegion("time"))
        # get client
        client = pysvn.Client()
        client.callback_cancel = _pysvn_cancel_callback
        try:
            # grab current revision and repo URL
            info = client.info(path=self.Addon.getAddonInfo("Path"))
            # fetch changelog for current revision
            if (kind == "changelog"):
                log = client.log(url_or_path=info["url"], limit=25, revision_start=pysvn.Revision(pysvn.opt_revision_kind.number, info["commit_revision"].number))
            # updates
            else:
                log = client.log(url_or_path=info["url"], limit=25, revision_end=pysvn.Revision(pysvn.opt_revision_kind.number, info["commit_revision"].number + 1))
        except:
            # changelog
            log = client.log(url_or_path="{repo}{branch}{id}".format(repo=self.Addon.getSetting("Repo"), branch=self.Addon.getSetting("Branch"), id=self.Addon.getAddonInfo("Id"),), limit=25)
        # if no entries set user message
        if (len(log)):
            # initialize our log text
            changelog = "{0:-<150}\n".format("")
        else:
            # should only happen for "updates" and there are none
            changelog = self.Addon.getLocalizedString(30701)
        # we need to compile so we can add flags
        clean_entry = re.compile("\[.+?\][\s]+(?P<name>[^\[]+)(?:\[.+)?", re.DOTALL)
        version = re.compile("(Version.+)", re.IGNORECASE)
        # iterate thru and format each message
        for entry in log:
            # add version
            changelog += "{version}\n".format(version=version.search(entry["message"]).group(1))
            # add heading
            changelog += "r{revision} - {date} - {author}\n".format(revision=entry["revision"].number, date=datetime.datetime.fromtimestamp(entry["date"]).strftime(date_format), author=entry["author"])
            # add formatted message
            changelog += "\n".join([re.sub("(?P<name>^[a-zA-Z])", "- \\1", line.lstrip(" -")) for line in entry["message"].strip().splitlines() if (not line.startswith("["))])
            # add separator
            changelog += "\n{0:-<150}\n".format("")

        return self._colorize_text(changelog)

    def _fetch_text_file(self, kind, msg):
        # set path, first try translated version
        path = os.path.join(self.Addon.getAddonInfo("Path"), u"{kind}-{language}.txt".format(kind=kind, language=xbmc.getRegion("locale")))
        # if doesn't exist, use default
        if (not os.path.isfile(path)):
            path = os.path.join(self.Addon.getAddonInfo("Path"), u"{kind}.txt".format(kind=kind))
        try:
            # read file
            text = unicode(open(path, "r").read(), "UTF-8")
        except IOError as error:
            # set error message
            return u"{msg}[CR][CR]{error}".format(msg=self.Addon.getLocalizedString(30771).format(kind=self.Addon.getLocalizedString(msg)), error=error.strerror)
        else:
            return text

    def _fetch_properties(self, msg):
        try:
            # get python source, we set properties in resources/lib/properties.py file
            pySource = unicode(open(os.path.join(os.path.dirname(__file__), u"properties.py"), "r").read(), "UTF-8")
        except IOError as error:
            # set error message
            return u"{msg}[CR][CR]{error}".format(msg=self.Addon.getLocalizedString(30771).format(kind=self.Addon.getLocalizedString(msg)), error=error.strerror)
        else:
            # initialize our text block
            messages = re.findall(u"(\$MSG|\$SUB_MSG)\[(.+?)\](\$END_MSG|\$END_SUB_MSG)", pySource)
            # initialize our text
            text = u"[COLOR changelog_headline][B]{header}[/B][/COLOR]\n{0:-<80}\n".format(u"", header=u"Notes")
            # iterate thru and add any messages
            for message in messages:
                head = [u"[COLOR 00000000]- [/COLOR]", u""][message[0] == u"$MSG"]
                tail = [u"\n\n", u"\n"][message[0] == u"$MSG"]
                text += u"{head}{message}{tail}".format(head=head, message=message[1], tail=tail)
            # get group, properties and description set by addon
            groups = re.findall(u"\$BEGIN_GROUP\[(.+?)\](.+?)\$END_GROUP", pySource, re.DOTALL)
            # iterate thru and get all properties and their descriptions
            for group in groups:
                # add group header
                text += u"\n[COLOR changelog_headline][B]{header}[/B][/COLOR]\n{0:-<80}\n".format(u"", header=group[0])
                # find all properties for this group
                properties = re.findall(u"\#[\s]*(.+?)\n\s+?self\.WINDOW\.setProperty\(.*?\"([^\"]+?)\".*?,.+?\)", group[1])
                # iterate thru and add the property
                for property in properties:
                    line = u"- [COLOR changelog_highlight]{id}[/COLOR]\n[COLOR 00000000]- [/COLOR][I]{desc}[/I]\n".format(id=property[1], desc=property[0])
                    # add line
                    text += line
            # replace tokens
            text = text.replace(u"$ICON", self.Addon.getAddonInfo("Icon")).replace(u"$ID", self.Addon.getAddonInfo("Id")).replace(u"$NAME", self.Addon.getAddonInfo("Name"))

            return text

    def _colorize_text(self, text):
        # format text using colors
        text = re.sub("(?P<name>Version:.+)[\r\n]+", "[COLOR FFEB9E17]\\1[/COLOR]\n\n", text)
        text = re.sub("(?P<name>r[0-9]+ - .+?)(?P<name2>[\r\n]+)", "[COLOR FF0084FF]\\1[/COLOR]\\2", text)
        text = re.sub("(?P<name>http://[\S]+)", "[COLOR FFEB9E17]\\1[/COLOR]", text)
        text = re.sub("(?P<name>[^\]]r[0-9]+)", "[COLOR FFEB9E17]\\1[/COLOR]", text)
        text = re.sub("(?P<name>\".+?\")", "[COLOR FFEB9E17]\\1[/COLOR]", text)
        text = re.sub("(?P<name>[A-Z]+:)[\r\n]+", "[COLOR FF0084FF][B]\\1[/B][/COLOR]\n", text)
        text = re.sub("(?P<name> - )", "[COLOR FFFFFFFF]\\1[/COLOR]", text)
        text = re.sub("(?P<name>-[-]+)", "[COLOR FFFFFFFF]\\1[/COLOR]", text)

        return text
