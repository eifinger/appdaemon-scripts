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
        self.acceptable_range = self.get_arg("acceptable_range")

        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.sensor, attribute = "all"))

    def state_change(self, entity, attributes, old, new, kwargs):
        self.log("entity: {}".format(entity))
        self.log("old: {}".format(old))
        self.log("new: {}".format(new))

    
    def calculate_travel_times(self, *kwargs):
        if "entities" in self.args:
            for entity in self.args["entities"]:
                _from = self.args["entities"][entity]["from"]
                if _from.startswith("secret_"):
                    _from = self.get_secret(_from)
                _to = self.args["entities"][entity]["to"]
                if _to.startswith("secret_"):
                    _to = self.get_secret(_to)
                travelTime = self.get_distance_matrix(_from, _to)
                roundedTravelTime = int(round(travelTime["duration_in_traffic"]["value"] / 60))
                self.log("Updating {} to {} minutes".format(entity, str(roundedTravelTime)))
                self.set_state(entity, state = roundedTravelTime)
                #Notify component
                if roundedTravelTime <= travelTime["duration"]["value"] * 1.2 and self.get_state(self.args["entities"][entity]["notify_input_boolean"]) == "on":
                    message = messages.journey_start().format(_to)
                    self.log("Notify user")
                    self.call_service("notify/group_notifications",message=message)
                    self.turn_off(self.args["entities"][entity]["notify_input_boolean"])
        else:
            self.log("No entities defined", level = "ERROR")
        self.run_in(self.calculate_travel_times, self.delay) 

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