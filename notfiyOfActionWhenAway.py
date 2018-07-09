import appdaemon.plugins.hass.hassapi as hass
import messages
import globals
#
# App to send notification when a sensor changes state
#
# Args:
#
#  sensor: sensor to monitor. example: sensor.upstairs_smoke
#  isHome: input_boolean which shows if someone is home. example: input_boolean.isHome
#  isHome_delay: delay to wait for user to come home before notifying. example: 10
# Release Notes
#
# Version 1.1:
#   Added isHome_delay
#
# Version 1.0:
#   Initial Version

class NotfiyOfActionWhenAway(hass.Hass):

  def initialize(self):
    self.user_name = globals.get_arg(self.args,"user_name")
    self.isHome_delay = globals.get_arg(self.args,"isHome_delay")
    self.isHome = globals.get_arg(self.args,"isHome")

    self.listen_state_handle_list = []
    self.timer_handle_list = []

    for sensor in globals.get_arg_list("sensor"):
      self.listen_state_handle_list.append(self.listen_state(self.state_change, sensor))
    
  def state_change(self, entity, attribute, old, new, kwargs):
    if new != "":
      if self.get_state(self.isHome) == "off":
        if entity.startswith("binary_sensor.motion_sensor") and new == "off":
          pass
        else:
          self.log("Waiting {} seconds for someone to come home".format(self.isHome_delay))
          self.timer_handle_list.append(self.run_in(self.notify_if_no_one_home,self.isHome_delay, entity = entity, new = new))

  def notify_if_no_one_home(self, **kwargs):
    if self.get_state(self.isHome) == "off":
      self.log("{} changed to {}".format(self.friendly_name(kwargs["entity"]), kwargs["new"]))
      self.call_service("notify/" + self.user_name,message=messages.device_change_alert().format(self.friendly_name(kwargs["entity"]), kwargs["new"]))

  def terminate(self):
    for listen_state_handle in self.listen_state_handle_list:
      self.cancel_listen_state(listen_state_handle)

    for timer_handle in self.timer_handle_list:
      self.cancel_timer(timer_handle)
      
