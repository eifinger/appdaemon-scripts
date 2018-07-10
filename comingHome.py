import appdaemon.plugins.hass.hassapi as hass
import globals
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
# Version 1.1:
#   Using globals
#
# Version 1.0:
#   Initial Version

class ComingHome(hass.Hass):

  def initialize(self):
    self.listen_state_handle_list = []

    self.sensor = globals.get_arg(self.args,"sensor")
    self.isHome = globals.get_arg(self.args,"isHome")
    self.actor = globals.get_arg(self.args,"actor")

    self.listen_state_handle_list.append(self.listen_state(self.state_change, self.sensor))
    
  def state_change(self, entity, attribute, old, new, kwargs):
    if new != "":
      isHome_state = self.get_state(self.isHome)
      if isHome_state == "off" and self.sun_down():
        self.log("{} changed to {}".format(self.friendly_name(entity), new))
        self.turn_on(self.actor)

  def terminate(self):
    for listen_state_handle in self.listen_state_handle_list:
      self.cancel_listen_state(listen_state_handle)
      
