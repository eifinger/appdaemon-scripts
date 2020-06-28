import appdaemon.plugins.hass.hassapi as hass
import globals

#
# App which listens on the log for WARNING and ERROR and notifies via telegram
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
        self.notify_name = globals.get_arg(self.args, "notify_name")
        self.notify_message = globals.get_arg(self.args, "notify_message")
        self.include_log_message_in_notification = globals.get_arg(
            self.args, "include_log_message_in_notification"
        )
        try:
            self.exclude_apps = globals.get_arg_list(self.args, "exclude_apps")
        except KeyError:
            self.exclude_apps = None

        # App dependencies
        self.notifier = self.get_app("Notifier")

        self.handle = self.listen_log(self.log_message_callback)

    def log_message_callback(self, app_name, ts, level, log_type, message, kwargs):
        self.log("name: {}, ts: {}, level: {}, messsage: {}".format(app_name, ts, level, message))
        if level == "WARNING" or level == "ERROR" or level == "CRITICAL":
            self.log("Correct level: {}".format(level))
            self.log("name: {}".format(app_name))
            if app_name == "AppDaemon":
                self.log("Is AppDaemon message")
                # check if this is a warning for an app
                try:
                    app_message_start_index = message.index(":", 11) + 2
                except ValueError:
                    app_message_start_index = None
                self.log(
                    "app_message_start_index is: {}".format(app_message_start_index)
                )
                first_space_index = message.index(" ", 11)
                self.log("first_space_index is: {}".format(first_space_index))
                if app_message_start_index is not None:
                    if app_message_start_index > first_space_index:
                        stripped_app_name = message[11, message.index(":", 11)]

                        app_message = message[app_message_start_index:]

                        self.notifier.notify(
                            self.notify_name,
                            self.notify_message.format(stripped_app_name),
                            useAlexa=False,
                        )
                        if self.include_log_message_in_notification:
                            self.notifier.notify(
                                self.notify_name, app_message, useAlexa=False
                            )

    def terminate(self):
        self.cancel_listen_log(self.handle)
