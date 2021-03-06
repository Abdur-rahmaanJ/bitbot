#--depends-on commands

import time
from src import ModuleManager, utils

class Module(ModuleManager.BaseModule):
    def _uptime(self):
        return utils.to_pretty_time(int(time.time()-self.bot.start_time))

    @utils.hook("received.command.uptime")
    def uptime(self, event):
        """
        :help: Show my uptime
        """
        event["stdout"].write("Uptime: %s" % self._uptime())
    @utils.hook("api.get.uptime")
    def uptime_api(self, event):
        return self._uptime()

    def _stats(self):
        networks = len(self.bot.servers)
        channels = 0
        users = 0
        for server in self.bot.servers.values():
            channels += len(server.channels)
            users += len(server.users)
        return [networks, channels, users]

    @utils.hook("received.command.stats")
    def stats(self, event):
        """
        :help: Show my network/channel/user stats
        """
        networks, channels, users = self._stats()

        response = "I currently have %d network" % networks
        if networks > 1:
            response += "s"
        response += ", %d channel" % channels
        if channels > 1:
            response += "s"
        response += " and %d visible user" % users
        if users > 1:
            response += "s"

        event["stdout"].write(response)

    @utils.hook("api.get.stats")
    def stats_api(self, event):
        networks, channels, users = self._stats()
        return {"networks": networks, "channels": channels, "users": users}

    def _server_stats(self, server):
        connected_seconds = time.time()-server.socket.connect_time
        return {
            "hostname": server.connection_params.hostname,
            "port": server.connection_params.port,
            "tls": server.connection_params.tls,
            "alias": server.connection_params.alias,
            "hostmask": "%s!%s@%s" % (
                server.nickname, server.username, server.hostname),
            "users": len(server.users),
            "bytes-written": server.socket.bytes_written,
            "bytes-written-per-second":
                server.socket.bytes_written/connected_seconds,
            "bytes-read": server.socket.bytes_read,
            "bytes-read-per-second": server.socket.bytes_read/connected_seconds,
            "channels": {
                c.name: self._channel_stats(c) for c in server.channels
            },
            "capabilities": list(server.agreed_capabilities),
            "version": server.version
        }

    @utils.hook("api.get.servers")
    def servers_api(self, event):
        if event["path"]:
            server_id = event["path"][0]
            if not server_id.isdigit():
                return None
            server_id = int(server_id)

            server = self.bot.get_server_by_id(server_id)
            if not server:
                return None
            return self._server_stats(server)
        else:
            servers = {}
            for server in self.bot.servers.values():
                servers[server.id] = self._server_stats(server)
            return servers

    def _channel_stats(self, channel):
        return {
            "users": sorted([user.nickname for user in channel.users],
                key=lambda nickname: nickname.lower()),
            "topic": channel.topic,
            "topic-set-at": channel.topic_time,
            "topic-set-by": channel.topic_setter_nickname
        }
    @utils.hook("api.get.channels")
    def channels_api(self, event):
        if event["path"]:
            server_id = event["path"][0]
            if not server_id.isdigit():
                return None
            server_id = int(server_id)

            server = self.bot.get_server_by_id(server_id)
            if not server:
                return None
            channels = {}
            for channel in server.channels.values():
                channels[channel.name] = self._channel_stats(channel)
            return channels
        else:
            channels = {}
            for server in self.bot.servers.values():
                channels[server.id] = {}
                for channel in server.channels.values():
                    channels[server.id][str(channel)] = self._channel_stats(
                        channel)
            return channels

    @utils.hook("api.get.modules")
    def modules_api(self, event):
        return list(self.bot.modules.modules.keys())

    @utils.hook("received.command.caps")
    def capabilities(self, event):
        """
        :help: List negotiated IRCv3 capabilities
        """
        event["stdout"].write("IRCv3 capabilities: %s" %
            ", ".join(event["server"].agreed_capabilities))
