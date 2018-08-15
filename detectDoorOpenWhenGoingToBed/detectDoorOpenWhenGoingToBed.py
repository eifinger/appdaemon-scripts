import appdaemon.plugins.hass.hassapi as hass
import globals
#
# App which sends a notification if the terrace is still open when all users are in bed
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
# sensor: sensor to monitor e.g. sensor.upstairs_smoke
# entity: entity which triggers this app
# after_sundown: True
# notify_name: Who to notify. example: group_notifications
# message_<LANG>: localized message to use in notification. e.g. "You left open {} Dummy."
#
# Release Notes
#
# Version 1.2:
#   message now directly in own yaml instead of message module
#
# Version 1.1:
#   Added app_switch
#
# Version 1.0:
#   Initial Version

class DetectDoorOpenWhenGoingToBed(hass.Hass):

  def initialize(self):
    self.listen_state_handle_list = []
    self.timer_handle_list = []

    self.sensor = globals.get_arg(self.args,"sensor")
    self.app_switch = globals.get_arg_list(self.args,"app_switch")
    self.entity = globals.get_arg(self.args,"entity")
    self.after_sundown = globals.get_arg(self.args,"after_sundown")
    self.notify_name = globals.get_arg(self.args,"notify_name")
    self.message = globals.get_arg(self.args,"message_DE")
    
    self.listen_state_handle_list.append(self.listen_state(self.state_change, self.entity))
    
  def state_change(self, entity, attribute, old, new, kwargs):
    if self.get_state(self.app_switch) == "on":
      self.log("new: {}".format(new), level = "DEBUG")
      self.log("after_sundown: {}".format(self.after_sundown), level = "DEBUG")
      self.log("sun_down: {}".format(self.sun_down()), level = "DEBUG")
      if new != "" and new == "on" and ( ( self.after_sundown == True and self.sun_down() ) or self.after_sundown == False ):
          state = self.get_state(self.sensor)
          self.log("state: {}".format(state))
          if state == "on":
            self.log(self.message.format(self.friendly_name(self.sensor)))
            self.call_service("notify/" + self.notify_name,message=self.message.format(self.friendly_name(self.sensor)))

  def terminate(self):
    for listen_state_handle in self.listen_state_handle_list:
      self.cancel_listen_state(listen_state_handle)

    for timer_handle in self.timer_handle_list:
      self.cancel_timer(timer_handle)
      
