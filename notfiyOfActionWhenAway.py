import appdaemon.plugins.hass.hassapi as hass
import messages
import secrets
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
    self.user_name = self.args["user_name"]
    if self.user_name.startswith("secret_"):
      self.user_name = self.get_secret(self.user_name)
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
            self.call_service("notify/" + self.user_name,message=messages.device_change_alert().format(self.friendly_name(entity), new))
      else:
        self.log("isHome is not defined", level= "ERROR")


  def get_secret(self, key):
      if key in secrets.secret_dict:
          return secrets.secret_dict[key]
      else:
          self.log("Could not find {} in secret_dict".format(key))

  def terminate(self):
    for listen_state_handle in self.listen_state_handle_list:
      self.cancel_listen_state(listen_state_handle)
      
