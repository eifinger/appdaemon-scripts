import appdaemon.plugins.hass.hassapi as hass
import globals
#
# App which listens on the log for WARNING and ERROR and notifies via telegram
#
# Args:
#
# Release Notes
#
# Version 1.0:
#   Initial Version


class AppWatcher(hass.Hass):

    def initialize(self):
        self.notify_name = globals.get_arg(self.args, "notify_name")
        self.notify_message = globals.get_arg(self.args, "notify_message")
        self.include_log_message_in_notification = globals.get_arg(self.args, "include_log_message_in_notification")
        try:
            self.exclude_apps = globals.get_arg_list(self.args, "exclude_apps")
        except KeyError:
            self.exclude_apps = None

        # App dependencies
        self.notifier = self.get_app('Notifier')

        self.listen_log(self.log_message_callback)

    def log_message_callback(self, name, ts, level, message):
        if level == "WARNING" or level == "ERROR" or level == "CRITICAL":
            if name == "Appdaemon":
                # check if this is a warning for an app
                try:
                    app_message_start_index = message.index(":", 11) + 2
                except ValueError:
                    app_message_start_index = None
                first_space_index = message.index(" ", 11)
                if app_message_start_index is not None:
                    if app_message_start_index > first_space_index:
                        app_name = message[11, message.index(":", 11)]

                        app_message = message[app_message_start_index:]

                        self.notifier.notify(self.notify_name, self.notify_message.format(app_name), useAlexa=False)
                        if self.include_log_message_in_notification:
                            self.notifier.notify(self.notify_name, app_message, useAlexa=False)

    def terminate(self):
        self.cancel_listen_log()
