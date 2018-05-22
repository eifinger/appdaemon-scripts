import appdaemon.plugins.hass.hassapi as hass
import messages
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
        oneplus3 = self.get_state("device_tracker.android342cb6b2879c4a9b")
        oneplus3T = self.get_state("device_tracker.android841a92d172870395")
        self.isHomeHandler(oneplus3T, oneplus3)
        
        self.listen_state(self.state_change, "device_tracker.android342cb6b2879c4a9b")
        self.listen_state(self.state_change, "device_tracker.android841a92d172870395")
    
    def state_change(self, entity, attribute, old, new, kwargs):
        if new != "":
            if entity == "device_tracker.android841a92d172870395":
                oneplus3 = self.get_state("device_tracker.android342cb6b2879c4a9b")
                oneplus3T = new
            if entity == "device_tracker.android342cb6b2879c4a9b":
                oneplus3T = self.get_state("device_tracker.android841a92d172870395")
                oneplus3 = new
            self.isHomeHandler(oneplus3T, oneplus3)

    def isHomeHandler(self, oneplus3T, oneplus3):
        if oneplus3 == "home" or oneplus3T == "home":
            self.set_state(self.args["isHome"], state = "on")
        if oneplus3 == "not_home" and oneplus3T == "not_home":
            self.set_state(self.args["isHome"], state = "off")
            self.call_service("notify/slack",message=messages.isHome_off())
      
