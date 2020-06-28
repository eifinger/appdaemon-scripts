import appdaemon.plugins.hass.hassapi as hass

#
# App which listens on the log for App crashes and notifies via telegram
#
# Args:
#
# Release Notes
#
# Version 2.0:
#   Updates for Appdaemon Version 4.0.3
#
# Version 1.0:
#   Initial Version


class AppWatcher(hass.Hass):
    def initialize(self):
        self.notify_name = self.args["notify_name"]
        self.notify_message = self.args["notify_message"]
        try:
            self.exclude_apps = self.args["exclude_apps"].split(",")
        except KeyError:
            self.exclude_apps = None

        # App dependencies
        self.notifier = self.get_app("Notifier")

        self.handle = self.listen_log(self.log_message_callback)

    def log_message_callback(self, app_name, ts, level, log_type, message, kwargs):
        if level == "WARNING" or level == "ERROR" or level == "CRITICAL":
            if app_name == "AppDaemon":
                if "Unexpected error" in message:
                    self.notifier.notify(
                        self.notify_name,
                        self.notify_message.format(message),
                        useAlexa=False,
                    )

    def terminate(self):
        self.cancel_listen_log(self.handle)
