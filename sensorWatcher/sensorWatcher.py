import appdaemon.plugins.hass.hassapi as hass
import globals

#
# App which notifies if sensor goes offline
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.sensor_watcher
# watch_list: list of entities which should be watched
# message: message to use in notification
# notify_name: who to notify. example: group_notifications
# use_alexa (optional): use alexa for notification. example: False
#
# Release Notes
#
# Version 1.0:
#   Initial Version


class SensorWatcher(hass.Hass):
    def initialize(self):
        self.listen_state_handle_list = []

        self.app_switch = globals.get_arg(self.args, "app_switch")
        self.watch_list = globals.get_arg_list(self.args, "watch_list")
        self.message = globals.get_arg(self.args, "message")
        self.message_back_online = globals.get_arg(self.args, "message_back_online")
        self.notify_name = globals.get_arg(self.args, "notify_name")
        try:
            self.use_alexa = globals.get_arg(self.args, "use_alexa")
        except KeyError:
            self.use_alexa = False

        self.notifier = self.get_app("Notifier")

        if self.get_state(self.app_switch) == "on":
            for sensor in self.watch_list:
                if (
                    self.get_state(sensor) is None
                    or self.get_state(sensor).lower() == "unknown"
                ):
                    self.notifier.notify(
                        self.notify_name,
                        self.message.format(self.friendly_name(sensor)),
                        useAlexa=self.use_alexa,
                    )

        for sensor in self.watch_list:
            self.listen_state_handle_list.append(
                self.listen_state(self.state_change, sensor)
            )

    def state_change(self, entity, attribute, old, new, kwargs):
        if self.get_state(self.app_switch) == "on":
            if new != old and (new is None or new.lower() == "unknown"):
                self.notifier.notify(
                    self.notify_name,
                    self.message.format(self.friendly_name(entity)),
                    useAlexa=self.use_alexa,
                )
            if new != old and (
                (old is None or old.lower() == "unknown")
                and (new is not None and new.lower() != "unknown")
            ):
                self.notifier.notify(
                    self.notify_name,
                    self.message_back_online.format(self.friendly_name(entity)),
                    useAlexa=self.use_alexa,
                )

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
