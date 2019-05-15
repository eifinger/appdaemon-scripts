import appdaemon.plugins.hass.hassapi as hass
import datetime
import globals

#
# App which notifies the user if the travel time is within a normal amount
#
#
# Args:
# sensor_realtime: waze realtime travel sensor to watch. example: sensor.travel_time_home_from_work_waze_realtime
# sensor: waze travel sensor to watch. example: sensor.travel_time_home_from_work_waze
# destination_name: Name of the destination to use in notifications
# notify_input_boolean: input_boolean determining whether to notify. example: input_boolean.travel_time_home_from_work
# notify_name: Who to notify. example: group_notifications
# acceptable_range (optional): Multiplier of the normal travel time that is still acceptable. example: 1.2
# message: message to use in notification
# notify_use_Alexa: use Alexa as TTS. Defaults to True. example: False
#
# Release Notes
# Version 1.1:
#   implement unknown check
#
# Version 1.0:
#   Ported from googel_travel_time


class WazeTravelTime(hass.Hass):
    def initialize(self):

        self.listen_state_handle_list = []
        self.timer_handle_list = []

        self.sensor = globals.get_arg(self.args, "sensor")
        self.sensor_realtime = globals.get_arg(self.args, "sensor_realtime")
        self.destination_name = globals.get_arg(self.args, "destination_name")
        self.notify_input_boolean = globals.get_arg(self.args, "notify_input_boolean")
        self.notify_name = globals.get_arg(self.args, "notify_name")
        self.message = globals.get_arg(self.args, "message")
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
            self.listen_state(self.state_change, self.sensor_realtime, attribute="all")
        )

    def state_change(self, entity, attributes, old, new, kwargs):
        if self.get_state(self.notify_input_boolean) == "on":
            self.log("entity: {}".format(entity), level="DEBUG")
            self.log("old: {}".format(old), level="DEBUG")
            self.log("new: {}".format(new), level="DEBUG")

            duration_in_traffic = new["attributes"]["duration"]
            if duration_in_traffic == "unknown":
                self.log("duration_in_traffic is unknown".format(), level="ERROR")
            else:
                duration_in_traffic_minutes = float(duration_in_traffic)
                self.log(
                    "duration_in_traffic_minutes: {}".format(
                        duration_in_traffic_minutes
                    ),
                    level="DEBUG",
                )

                duration = self.get_state(self.sensor, attribute="all")["attributes"][
                    "duration"
                ]
                if duration == "unknown":
                    self.log("duration is unknown".format(), level="ERROR")
                else:
                    duration_minutes = float(duration)
                    self.log(
                        "duration_minutes: {}".format(duration_minutes), level="DEBUG"
                    )

                    if (
                        duration_in_traffic_minutes
                        <= duration_minutes * self.acceptable_range
                    ):
                        message = self.message.format(self.destination_name)
                        self.log("Notify user")
                        self.notifier.notify(
                            self.notify_name, message, useAlexa=self.notify_use_Alexa
                        )
                        self.turn_off(self.notify_input_boolean)

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
