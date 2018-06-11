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

class NotfiyOfActionWhenAway(hass.Hass):

  def initialize(self):
    self.listen_state_handle_list = []

    if "sensor" in self.args:
      for sensor in self.split_device_list(self.args["sensor"]):
        self.listen_state_handle_list.append(self.listen_state(self.state_change, sensor))
    
  def state_change(self, entity, attribute, old, new, kwargs):
    if new != "":
      if "isHome" in self.args:
        isHome = self.get_state(self.args["isHome"])
        if isHome == "off":
          if entity == "binary_sensor.motion_sensor_158d00012aab97" and new == "off":
            pass
          else:
            self.log("{} changed to {}".format(self.friendly_name(entity), new))
            self.call_service("notify/slack",message=messages.device_change_alert().format(self.friendly_name(entity), new))
      else:
        self.log("isHome is not defined", level= "ERROR")

  def terminate(self):
    for listen_state_handle in self.listen_state_handle_list:
      self.cancel_listen_state(listen_state_handle)
      
