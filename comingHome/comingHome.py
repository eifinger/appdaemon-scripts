import appdaemon.plugins.hass.hassapi as hass
import globals
import datetime
#
# App to Turn on Lobby Lamp when Door openes and no one is Home
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
# sensor: door sensor
# isHome: input_boolean which shows if someone is home eg input_boolean.isHome
# actor: actor to turn on
# after_sundown (optionally): whether to only trigger after sundown. example: True
# Release Notes
#
# Version 1.3.1:
#   Actually implement isHome
#
# Version 1.3:
#   Added app_switch
#
# Version 1.2:
#   Added after_sundown
#
# Version 1.1:
#   Using globals
#
# Version 1.0:
#   Initial Version

class ComingHome(hass.Hass):

  def initialize(self):
    self.listen_state_handle_list = []

    self.app_switch = globals.get_arg(self.args,"app_switch")
    self.sensor = globals.get_arg(self.args,"sensor")
    self.isHome = globals.get_arg(self.args,"isHome")
    self.actor = globals.get_arg(self.args,"actor")
    try:
      self.after_sundown = globals.get_arg(self.args,"after_sundown")
    except KeyError:
      self.after_sundown = None

    self.delay = 2

    self.listen_state_handle_list.append(self.listen_state(self.state_change, self.sensor))
    
  def state_change(self, entity, attribute, old, new, kwargs):
    if self.get_state(self.app_switch) == "on":
      if new != "":
        isHome_attributes = self.get_state(self.isHome, attribute = "all")
        isHome_state = isHome_attributes["state"]
        last_changed = self.convert_utc(isHome_attributes["last_changed"])
        if isHome_state == "off" or (datetime.datetime.now(datetime.timezone.utc) - last_changed <= datetime.timedelta(seconds=self.delay)):
          if self.after_sundown != None and self.after_sundown:
            if self.sun_down():
              self.log("{} changed to {}".format(self.friendly_name(entity), new))
              self.turn_on(self.actor)
          else:
            self.log("{} changed to {}".format(self.friendly_name(entity), new))
            self.turn_on(self.actor)

  def terminate(self):
    for listen_state_handle in self.listen_state_handle_list:
      self.cancel_listen_state(listen_state_handle)
      
