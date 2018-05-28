import appdaemon.plugins.hass.hassapi as hass
#
# App to send notification when a sensor changes state
#
# Args:
#
# sensor: sensor to monitor e.g. sensor.upstairs_smoke
# actor_single: actor to toggle on single click
# actor_double: actor to toggle on double click
# Release Notes
#
# Version 1.0:
#   Initial Version

class ButtonClicked(hass.Hass):

    def initialize(self):
        self.listen_event_handle_list = []

        self.listen_event_handle_list.append(self.listen_event(self.event_detected, "click"))
        
    
    def event_detected(self, event_name, data, kwargs):
        if data["entity_id"] == self.args["sensor"]:
            if data["click_type"] == "single":
                self.log("ButtonClicked: {}".format(data["entity_id"]))
                self.log("Toggling {}".format(self.args["actor_single"]))
                if self.get_state(self.args["actor_single"]) == "on":
                    self.turn_off(self.args["actor_single"])
                if self.get_state(self.args["actor_single"]) == "off":
                    self.turn_on(self.args["actor_single"])
            if data["click_type"] == "double":
                self.log("ButtonClicked: {}".format(data["entity_id"]))
                self.log("Toggling {}".format(self.args["actor_double"]))
                if self.get_state(self.args["actor_double"]) == "on":
                    self.turn_off(self.args["actor_double"])
                if self.get_state(self.args["actor_double"]) == "off":
                    self.turn_on(self.args["actor_double"])

    def terminate(self):
        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)
      