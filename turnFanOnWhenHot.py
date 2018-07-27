import appdaemon.plugins.hass.hassapi as hass
import globals
#
# App to Turn on fan when temp is above a threshold and someone is Home
#
# Args:
#
# temp_sensor: temp sensor to monitor. example: sensor.large_lamp_temperature
# threshold: temp treshhold which must be reached. example: 28
# isHome: input_boolean which shows if someone is home. example: input_boolean.isHome
# actor: actor to turn on
# Release Notes
#
# Version 1.0:
#   Initial Version

class TurnFanOnWhenHot(hass.Hass):

  def initialize(self):
    self.listen_state_handle_list = []

    self.temp_sensor = globals.get_arg(self.args,"temp_sensor")
    self.threshold = globals.get_arg(self.args,"threshold")
    self.isHome = globals.get_arg(self.args,"isHome")
    self.actor = globals.get_arg(self.args,"actor")

    self.listen_state_handle_list.append(self.listen_state(self.state_change, self.temp_sensor))
    
  def state_change(self, entity, attribute, old, new, kwargs):
    if new != None and new != "" and float(new) > self.threshold and self.get_state(self.isHome) == "on":
      self.log("{} changed to {}".format(self.friendly_name(entity), new))
      self.log("Turning on {}".format(self.friendly_name(self.actor)))
      self.turn_on(self.actor)

  def terminate(self):
    for listen_state_handle in self.listen_state_handle_list:
      self.cancel_listen_state(listen_state_handle)
      
