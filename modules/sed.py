#--depends-on commands
#--depends-on config

import re, traceback
from src import ModuleManager, utils

REGEX_SPLIT = re.compile("(?<!\\\\)/")
REGEX_SED = re.compile("^s/")

@utils.export("channelset", {"setting": "sed",
    "help": "Disable/Enable sed in a channel",
    "validate": utils.bool_or_none, "example": "on"})
@utils.export("channelset", {"setting": "sed-sender-only",
    "help": "Disable/Enable sed only looking at the messages sent by the user",
    "validate": utils.bool_or_none, "example": "on"})
class Module(ModuleManager.BaseModule):
    def _closest_setting(self, event, setting, default):
        return event["target"].get_setting(setting,
            event["server"].get_setting(setting, default))

    @utils.hook("command.regex")
    def channel_message(self, event):
        """
        :command: sed
        :pattern: ^s/
        """
        sed_split = re.split(REGEX_SPLIT, event["message"], 3)
        if event["message"].startswith("s/") and len(sed_split) > 2:
            if not self._closest_setting(event, "sed", False):
                return

            regex_flags = 0
            flags = (sed_split[3:] or [""])[0]
            count = None

            last_flag = ""
            for flag in flags:
                if flag.isdigit():
                    if last_flag.isdigit():
                        count = int(str(count) + flag)
                    elif not count:
                        count = int(flag)
                elif flag == "i":
                    regex_flags |= re.I
                elif flag == "g":
                    count = 0
                last_flag = flag
            if count == None:
                count = 1

            try:
                pattern = re.compile(sed_split[1], regex_flags)
            except:
                traceback.print_exc()
                event["stderr"].write("Invalid regex in pattern")
                return
            replace = utils.irc.bold(sed_split[2].replace("\\/", "/"))

            for_user = event["user"].nickname if self._closest_setting(event,
                "sed-sender-only", False) else None
            line = event["target"].buffer.find(pattern, from_self=False,
                for_user=for_user, not_pattern=REGEX_SED)
            if line:
                new_message = re.sub(pattern, replace, line.message, count)
                if line.action:
                    prefix = "* %s" % line.sender
                else:
                    prefix = "<%s>" % line.sender
                event["stdout"].write("%s %s" % (prefix, new_message))
