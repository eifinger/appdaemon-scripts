import appdaemon.plugins.hass.hassapi as hass
#
# App to Turn on Lobby Lamp when Door openes and OnePlus is not Home
#
# Args:
#
# isHome: input_boolean which shows if someone is home eg input_boolean.isHome
# Release Notes
#
# Version 1.0:
#   Initial Version

class IsHomeDeterminer(hass.Hass):

    def initialize(self):
        oneplus_state = self.get_state("device_tracker.android342cb6b2879c4a9b")
        if oneplus_state == "home":
            self.set_state(self.args["isHome"], state = "on")
        if oneplus_state == "not_home":
            self.set_state(self.args["isHome"], state = "off")
        
        self.listen_state(self.state_change, "device_tracker.android342cb6b2879c4a9b")
    
    def state_change(self, entity, attribute, old, new, kwargs):
        if new != "":
            if new == "home":
                self.set_state(self.args["isHome"], state = "on")
            if new == "not_home":
                self.set_state(self.args["isHome"], state = "off")
      
