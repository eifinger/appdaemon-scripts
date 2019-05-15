import appdaemon.plugins.hass.hassapi as hass
import datetime
import globals

#
# App which notifies the user if the travel time is within a normal amount
#
#
# Args:
# sensor: google travel sensor to watch. example: sensor.travel_time_home_from_work
# notify_input_boolean: input_boolean determining whether to notify. example: input_boolean.travel_time_home_from_work
# notify_name: Who to notify. example: group_notifications
# acceptable_range (optional): Multiplier of the normal travel time that is still acceptable. example: 1.2
# message_<LANG>: message to use in notification
# notify_use_Alexa: use Alexa as TTS. Defaults to True. example: False
#
# Release Notes
#
# Version 1.4:
#   use Notify App
#
# Version 1.3:
#   message now directly in own yaml instead of message module
#
# Version 1.2:
#   Moved to standard google travel sensors. Now only notification
#
# Version 1.1:
#   Add notification feature
#
# Version 1.0:
#   Initial Version


class GoogleTravelTime(hass.Hass):
    def initialize(self):

        self.listen_state_handle_list = []
        self.timer_handle_list = []

        self.sensor = globals.get_arg(self.args, "sensor")
        self.notify_input_boolean = globals.get_arg(self.args, "notify_input_boolean")
        self.notify_name = globals.get_arg(self.args, "notify_name")
        self.message = globals.get_arg(self.args, "message_DE")
        try:
            self.acceptable_range = globals.get_arg(self.args, "acceptable_range")
        except KeyError:
            self.acceptable_range = 1.2
        try:
            self.notify_use_Alexa = globals.get_arg(self.args, "notify_use_Alexa")
        except KeyError:
            self.notify_use_Alexa = True

        self.notifier = self.get_app("Notifier")

        self.listen_state_handle_list.append(
            self.listen_state(self.state_change, self.sensor, attribute="all")
        )

    def state_change(self, entity, attributes, old, new, kwargs):
        self.log("entity: {}".format(entity), level="DEBUG")
        self.log("old: {}".format(old), level="DEBUG")
        self.log("new: {}".format(new), level="DEBUG")

        duration_in_traffic = new["attributes"]["duration_in_traffic"]
        duration_in_traffic_minutes = int(
            duration_in_traffic[: duration_in_traffic.find(" ")]
        )
        self.log(
            "duration_in_traffic_minutes: {}".format(duration_in_traffic_minutes),
            level="DEBUG",
        )

        duration = new["attributes"]["duration"]
        duration_minutes = int(duration[: duration.find(" ")])
        self.log("duration_minutes: {}".format(duration_minutes), level="DEBUG")

        if (
            duration_in_traffic_minutes <= duration_minutes * self.acceptable_range
            and self.get_state(self.notify_input_boolean) == "on"
        ):
            message = self.message.format(new["attributes"]["destination_addresses"][0])
            self.log("Notify user")
            self.notifier.notify(
                self.notify_name, message, useAlexa=self.notify_use_Alexa
            )
            self.turn_off(self.notify_input_boolean)

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
