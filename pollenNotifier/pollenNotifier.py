import appdaemon.plugins.hass.hassapi as hass
import globals
import datetime

#
# App which notifies you when there is a pollen forecast for today
# Used with sensors getting data from https://opendata.dwd.de/climate_environment/health/alerts/s31fg.json
#
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
# pollen_sensor: sensor which shows pollen for today. example: sensor.pollen_101_roggen_today
# pollen_name: Name of the allergen. example: Roggen
# notify_name: Who to notify. example: group_notifications
# notify_time: When to notify. example: 08:00
# notify_threshold: Minimum level of pollen needed to notify. example: 1.0
# message: localized message to use in notification
#
# Release Notes
#
# Version 1.3.1:
#   Use consistent message variable
#
# Version 1.3:
#   use Notify App
#
# Version 1.2:
#   message now directly in own yaml instead of message module
#
# Version 1.1:
#   Added notify_threshold
#
# Version 1.0:
#   Initial Version


class PollenNotifier(hass.Hass):
    def initialize(self):

        self.timer_handle_list = []
        self.listen_event_handle_list = []
        self.listen_state_handle_list = []

        self.app_switch = globals.get_arg(self.args, "app_switch")
        self.pollen_sensor = globals.get_arg(self.args, "pollen_sensor")
        self.pollen_name = globals.get_arg(self.args, "pollen_name")
        self.notify_name = globals.get_arg(self.args, "notify_name")
        self.notify_time = globals.get_arg(self.args, "notify_time")
        self.notify_threshold = globals.get_arg(self.args, "notify_threshold")
        self.message = globals.get_arg(self.args, "message")
        self.message_no_data = globals.get_arg(self.args, "message_no_data")

        self.mappingsdict = {}
        self.mappingsdict["-1"] = "keine Daten"
        self.mappingsdict["0"] = "Keine"
        self.mappingsdict["0-1"] = "Keine bis Geringe"
        self.mappingsdict["1"] = "Geringe"
        self.mappingsdict["1-2"] = "Geringe bis Mittlere"
        self.mappingsdict["2"] = "Mittlere"
        self.mappingsdict["2-3"] = "Mittlere bis Hohe"
        self.mappingsdict["3"] = "Hohe"

        self.level_mapping_dict = {}
        self.level_mapping_dict["-1"] = -1.0
        self.level_mapping_dict["0"] = 0.0
        self.level_mapping_dict["0-1"] = 0.5
        self.level_mapping_dict["1"] = 1.0
        self.level_mapping_dict["1-2"] = 1.5
        self.level_mapping_dict["2"] = 2.0
        self.level_mapping_dict["2-3"] = 2.5
        self.level_mapping_dict["3"] = 3

        self.notifier = self.get_app("Notifier")

        hours = self.notify_time.split(":", 1)[0]
        minutes = self.notify_time.split(":", 1)[1]
        self.timer_handle_list.append(
            self.run_daily(
                self.run_daily_callback, datetime.time(int(hours), int(minutes), 0)
            )
        )

    def run_daily_callback(self, kwargs):
        """Check if there is an pollen forcast and notify the user about it"""
        if self.get_state(self.app_switch) == "on":
            pollen_sensor_state = self.get_state(self.pollen_sensor)
            self.log(
                "{} Belastung Heute: {}".format(self.pollen_name, pollen_sensor_state)
            )

            if pollen_sensor_state == "-1":
                message = self.message_no_data.format("Heute", self.pollen_name)
            elif pollen_sensor_state == "0":
                message = (
                    self.message.format(
                        "Heute",
                        self.mappingsdict[pollen_sensor_state],
                        self.pollen_name,
                    )
                    + " Genieß den Tag!"
                )
            else:
                message = self.message.format(
                    "Heute", self.mappingsdict[pollen_sensor_state], self.pollen_name
                )

            if self.level_mapping_dict[pollen_sensor_state] >= float(
                self.notify_threshold
            ):
                self.log("Notifying user")
                self.notifier.notify(self.notify_name, message)
            else:
                self.log("Threshold not met. Not notifying user")

    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
