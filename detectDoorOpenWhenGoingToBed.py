import appdaemon.plugins.hass.hassapi as hass
import messages
import globals
#
# App to send notification when a sensor changes state
#
# Args:
#
# sensor: sensor to monitor e.g. sensor.upstairs_smoke
# entity: entity which triggers this app
# after_sundown: True
# notify_name: Who to notify. example: group_notifications
# Release Notes
#
# Version 1.0:
#   Initial Version

class DetectDoorOpenWhenGoingToBed(hass.Hass):

  def initialize(self):
    self.listen_state_handle_list = []
    self.timer_handle_list = []

    self.sensor = globals.get_arg(self.args,"sensor")
    self.entity = globals.get_arg(self.args,"entity")
    self.after_sundown = globals.get_arg(self.args,"after_sundown")
    self.notify_name = globals.get_arg(self.args,"notify_name")
    
    self.listen_state_handle_list.append(self.listen_state(self.state_change, self.entity))
    
  def state_change(self, entity, attribute, old, new, kwargs):
    self.log("new: {}".format(new))
    self.log("after_sundown: {}".format(self.after_sundown))
    self.log("sun_down: {}".format(self.sun_down()))
    if new != "" and new == "on" and ( ( self.after_sundown == True and self.sun_down() ) or self.after_sundown == False ):
        state = self.get_state(self.sensor)
        self.log("state: {}".format(state))
        if state == "open":
          self.log(messages.forgot_window_open().format(self.friendly_name(self.sensor)))
          self.call_service("notify/" + self.notify_name,message=messages.forgot_window_open().format(self.friendly_name(self.sensor)))

  def terminate(self):
    for listen_state_handle in self.listen_state_handle_list:
      self.cancel_listen_state(listen_state_handle)

    for timer_handle in self.timer_handle_list:
      self.cancel_timer(timer_handle)
      
