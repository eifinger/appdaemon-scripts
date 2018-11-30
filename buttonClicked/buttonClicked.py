import appdaemon.plugins.hass.hassapi as hass
#
# App which toggles entities for single/double presses of xiaomi buttons
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

        self.listen_event_handle_list.append(self.listen_event(self.event_detected, "xiaomi_aqara.click"))
        
    
    def event_detected(self, event_name, data, kwargs):
        if data["entity_id"] == self.args["sensor"]:
            if data["click_type"] == "single":
                self.log("ButtonClicked: {}".format(data["entity_id"]))
                if self.get_state(self.args["actor_single"]) == "on":
                    self.log("Turning {} off".format(self.args["actor_single"]))
                    #Workaround for Yeelight see https://community.home-assistant.io/t/transition-for-turn-off-service-doesnt-work-for-yeelight-lightstrip/25333/4
                    if self.args["actor_single"].startswith("light"):
                        self.call_service("light/turn_on", entity_id = self.args["actor_single"], transition = 1, brightness = 1)
                        self.run_in(self.turn_off_workaround,2)
                    else:
                        self.turn_off(self.args["actor_single"])
                if self.get_state(self.args["actor_single"]) == "off":
                    self.log("Turning {} on".format(self.args["actor_single"]))
                    if self.args["actor_single"].startswith("light"):
                        self.call_service("light/turn_on", entity_id = self.args["actor_single"], transition = 1, brightness = 100)
                    else:
                        self.turn_on(self.args["actor_single"])
            if data["click_type"] == "double":
                self.log("ButtonClicked: {}".format(data["entity_id"]))
                self.log("Toggling {}".format(self.args["actor_double"]))
                if self.get_state(self.args["actor_double"]) == "on":
                    #Workaround for Yeelight see https://community.home-assistant.io/t/transition-for-turn-off-service-doesnt-work-for-yeelight-lightstrip/25333/4
                    if self.args["actor_single"].startswith("light"):
                        self.call_service("light/turn_on", entity_id = self.args["actor_single"], transition = 1, brightness = 1)
                        self.run_in(self.turn_off_workaround,2)
                    else:
                        self.turn_off(self.args["actor_single"])
                if self.get_state(self.args["actor_double"]) == "off":
                    self.log("Turning {} on".format(self.args["actor_single"]))
                    if self.args["actor_single"].startswith("light"):
                        self.call_service("light/turn_on", entity_id = self.args["actor_single"], transition = 1, brightness = 100)
                    else:
                        self.turn_on(self.args["actor_single"])

    def turn_off_workaround(self, *kwargs):
        self.call_service("light/turn_off", entity_id = self.args["actor_single"])

    def terminate(self):
        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)
      