import appdaemon.plugins.hass.hassapi as hass
import globals
import messages
#
# App to send notification when a sensor changes state
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
# sensor: sensor to monitor e.g. sensor.upstairs_smoke
# isHome: input_boolean which shows if someone is home eg input_boolean.isHome
# Release Notes
#
# Version 1.1:
#   Using globals and app_switch
#
# Version 1.0:
#   Initial Version

class DetectWrongStateWhenLeaving(hass.Hass):

  def initialize(self):
    self.listen_state_handle_list = []

    self.app_switch = globals.get_arg_list(self.args,"app_switch")
    self.sensors = globals.get_arg_list(self.args,"sensors")
    self.isHome = globals.get_arg(self.args,"isHome")
    
    self.listen_state_handle_list.append(self.listen_state(self.state_change, self.isHome))
    
  def state_change(self, entity, attribute, old, new, kwargs):
    if self.get_state(self.app_switch) == "on":
      if new != "" and new == "off":
        for sensor in self.sensors:
          state = self.get_state(sensor)
          if state == "on":
            self.turn_off(sensor)
            self.log(messages.forgot_light_on().format(self.friendly_name(sensor)))
            self.call_service("notify/group_notifications",message=messages.forgot_light_on().format(self.friendly_name(sensor)))
          if state == "open":
            self.log(messages.forgot_window_open().format(self.friendly_name(sensor)))
            self.call_service("notify/group_notifications",message=messages.forgot_window_open().format(self.friendly_name(sensor)))

  def terminate(self):
    for listen_state_handle in self.listen_state_handle_list:
      self.cancel_listen_state(listen_state_handle)
      
