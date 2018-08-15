import appdaemon.plugins.hass.hassapi as hass
import globals
#
# App which notifies if 
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
# entities_on (optional): list of entities which should be on
# entities_off (optional): list of entities which should off
# isHome: input_boolean which shows if someone is home eg input_boolean.isHome
# message_<LANG>: message to use in notification
# message_off_<LANG>: message to use in notification
# message_reed_<LANG>: message to use in notification
# message_reed_off_<LANG>: message to use in notification
#
# Release Notes
#
# Version 1.2:
#   message now directly in own yaml instead of message module
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
    try:
      self.entities_on = globals.get_arg_list(self.args,"entities_on")
    except KeyError as identifier:
            self.entities_on = []
    try:
      self.entities_off = globals.get_arg_list(self.args,"entities_off")
    except KeyError as identifier:
            self.entities_off = []
    self.isHome = globals.get_arg(self.args,"isHome")
    self.message = globals.get_arg(self.args,"message_DE")
    self.message_off = globals.get_arg(self.args,"message_off_DE")
    self.message_reed = globals.get_arg(self.args,"message_reed_DE")
    self.message_reed_off = globals.get_arg(self.args,"message_reed_off_DE")
    
    self.listen_state_handle_list.append(self.listen_state(self.state_change, self.isHome))
    
  def state_change(self, entity, attribute, old, new, kwargs):
    if self.get_state(self.app_switch) == "on":
      if new != "" and new == "off":
        #entities_off
        for entity in self.entities_off:
          state = self.get_state(entity)
          if state == "on":
            self.turn_off(entity)
            self.log(self.message.format(self.friendly_name(entity)))
            self.call_service("notify/group_notifications",message=self.message.format(self.friendly_name(entity)))
          if state == "open":
            self.log(self.message_reed.format(self.friendly_name(entity)))
            self.call_service("notify/group_notifications",message=self.message_reed.format(self.friendly_name(entity)))
        #entities_on
        for entity in self.entities_on:
          state = self.get_state(entity)
          if state == "off":
            self.turn_off(entity)
            self.log(self.message_off.format(self.friendly_name(entity)))
            self.call_service("notify/group_notifications",message=self.message_off.format(self.friendly_name(entity)))
          if state == "closed":
            self.log(self.message_reed_off.format(self.friendly_name(entity)))
            self.call_service("notify/group_notifications",message=self.message_reed_off.format(self.friendly_name(entity)))

  def terminate(self):
    for listen_state_handle in self.listen_state_handle_list:
      self.cancel_listen_state(listen_state_handle)
      
