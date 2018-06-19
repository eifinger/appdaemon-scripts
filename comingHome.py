import appdaemon.plugins.hass.hassapi as hass
#
# App to Turn on Lobby Lamp when Door openes and no one is Home
#
# Args:
#
# sensor: door sensor
# isHome: input_boolean which shows if someone is home eg input_boolean.isHome
# actor: actor to turn on
# Release Notes
#
# Version 1.0:
#   Initial Version

class ComingHome(hass.Hass):

  def initialize(self):
    self.listen_state_handle_list = []

    if "sensor" in self.args:
      for sensor in self.split_device_list(self.args["sensor"]):
        self.listen_state_handle_list.append(self.listen_state(self.state_change, sensor))
    
  def state_change(self, entity, attribute, old, new, kwargs):
    if new != "":
      if "isHome" in self.args:
        isHome = self.get_state(self.args["isHome"])
        if isHome == "off" and self.get_state("sun.sun") == "below_horizon":
          self.log("{} changed to {}".format(self.friendly_name(entity), new))
          self.turn_on(self.args["actor"])
      else:
        self.log("isHome is not defined", level= "ERROR")

  def terminate(self):
    for listen_state_handle in self.listen_state_handle_list:
      self.cancel_listen_state(listen_state_handle)
      
