import appdaemon.plugins.hass.hassapi as hass
import messages
#
# App to send notification when a sensor changes state
#
# Args:
#
# sensor: sensor to monitor e.g. sensor.upstairs_smoke
# isHome: input_boolean which shows if someone is home eg input_boolean.isHome
# Release Notes
#
# Version 1.0:
#   Initial Version

class DetectWrongStateWhenLeaving(hass.Hass):

  def initialize(self):
    self.listen_state_handle_list = []
    
    self.listen_state_handle_list.append(self.listen_state(self.state_change, self.args["isHome"]))
    
  def state_change(self, entity, attribute, old, new, kwargs):
    if new != "" and new == "off":
      for sensor in self.split_device_list(self.args["sensor"]):
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
      
