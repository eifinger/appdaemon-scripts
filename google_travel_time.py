import appdaemon.plugins.hass.hassapi as hass
import datetime
import secrets
import messages

#
# App which notifies the user if the travel time is within a normal amount
#
#
# Args:
# sensor: google travel sensor to watch. example: sensor.travel_time_home_from_work
# notify_input_boolean: input_boolean determining whether to notify. example: input_boolean.travel_time_home_from_work
# notify_name: Who to notify. example: group_notifications
# acceptable_range (optional): Multiplier of the normal travel time that is still acceptable. example: 1.2
#
# Release Notes
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

        self.sensor = self.get_arg("sensor")
        self.notify_input_boolean = self.get_arg("notify_input_boolean")
        self.notify_name = self.get_arg("notify_name")
        try:
            self.acceptable_range = self.get_arg("acceptable_range")
        except KeyError:
            self.acceptable_range = 1.2

        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.sensor, attribute = "all"))

    def state_change(self, entity, attributes, old, new, kwargs):
        self.log("entity: {}".format(entity))
        self.log("old: {}".format(old))
        self.log("new: {}".format(new))

        duration_in_traffic = new["attributes"]["duration_in_traffic"]
        duration_in_traffic_minutes = duration_in_traffic.substring(0,duration_in_traffic.find(" "))
        self.log("duration_in_traffic_minutes: {}".format(duration_in_traffic_minutes))

        duration = new["attributes"]["duration"]
        duration_minutes = duration.substring(0,duration.find(" "))
        self.log("duration_minutes: {}".format(duration_minutes))

        if duration_in_traffic_minutes <= duration_minutes * self.acceptable_range and self.get_state(self.notify_input_boolean) == "on":
            message = messages.journey_start().format(_to)
            self.log("Notify user")
            self.call_service("notify/" + self.notify_name, message=message)
            self.turn_off(self.notify_input_boolean)

    def get_arg(self, key):
        key = self.args[key]
        if key.startswith("secret_"):
            if key in secrets.secret_dict:
                return secrets.secret_dict[key]
            else:
                self.log("Could not find {} in secret_dict".format(key))
        else:
            return key

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)