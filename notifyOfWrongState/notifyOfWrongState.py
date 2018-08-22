import appdaemon.plugins.hass.hassapi as hass
import globals
#
# App which notifies of wrong states based on a state change
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
# entities_on (optional): list of entities which should be on
# entities_off (optional): list of entities which should off
# trigger_entity: entity which triggers this app. example: input_boolean.is_home
# trigger_state: new state of trigger_entity which triggers this app. example: "off"
# after_sundown (optional): Only trigger after sundown. example: True
# message_<LANG>: message to use in notification
# message_off_<LANG>: message to use in notification
# message_reed_<LANG>: message to use in notification
# message_reed_off_<LANG>: message to use in notification
# notify_name: who to notify. example: group_notifications
# use_alexa: use alexa for notification. example: False
#
# Release Notes
#
# Version 1.4.1:
#   fix wrong assignment of app_switch
#
# Version 1.4:
#   Generalize to notifyOfWrongState
#
# Version 1.3:
#   use Notify App
#
# Version 1.2:
#   message now directly in own yaml instead of message module
#
# Version 1.1:
#   Using globals and app_switch
#
# Version 1.0:
#   Initial Version

class NotifyOfWrongState(hass.Hass):

  def initialize(self):
    self.listen_state_handle_list = []

    self.app_switch = globals.get_arg(self.args,"app_switch")
    try:
      self.entities_on = globals.get_arg_list(self.args,"entities_on")
    except KeyError as identifier:
            self.entities_on = []
    try:
      self.entities_off = globals.get_arg_list(self.args,"entities_off")
    except KeyError as identifier:
            self.entities_off = []
    try:
      self.after_sundown = globals.get_arg(self.args,"after_sundown")
    except KeyError as identifier:
            self.after_sundown = None
    self.trigger_entity = globals.get_arg(self.args,"trigger_entity")
    self.trigger_state = globals.get_arg(self.args,"trigger_state")
    self.message = globals.get_arg(self.args,"message_DE")
    self.message_off = globals.get_arg(self.args,"message_off_DE")
    self.message_reed = globals.get_arg(self.args,"message_reed_DE")
    self.message_reed_off = globals.get_arg(self.args,"message_reed_off_DE")
    self.notify_name = globals.get_arg(self.args,"notify_name")
    self.use_alexa = globals.get_arg(self.args,"use_alexa")

    self.notifier = self.get_app('Notifier')
    
    self.listen_state_handle_list.append(self.listen_state(self.state_change, self.trigger_entity))
    
  def state_change(self, entity, attribute, old, new, kwargs):
    self.log("app_switch is: {}".format(self.app_switch))
    self.log("app_switch_state is: {}".format(self.get_state(self.app_switch)))
    if self.get_state(self.app_switch) == "on":
      self.log("new is: {}".format(self.get_state(new)))
      if new != "" and new == self.trigger_state:
        self.log("after_sundown is: {}".format(self.after_sundown))
        self.log("self.sun_down() is: {}".format(self.sun_down()))
        if self.after_sundown == None or ( ( self.after_sundown == True and self.sun_down() ) or self.after_sundown == False ):
          #entities_off
          for entity in self.entities_off:
            state = self.get_state(entity)
            self.log("{} is{}".format(self.friendly_name(entity),state))
            if state == "on":
              self.turn_off(entity)
              self.log(self.message.format(self.friendly_name(entity)))
              self.notifier.notify(self.notify_name, self.message.format(self.friendly_name(entity)), useAlexa=self.use_alexa)
            if state == "open":
              self.log(self.message_reed.format(self.friendly_name(entity)))
              self.notifier.notify(self.notify_name, self.message_reed.format(self.friendly_name(entity)), useAlexa=self.use_alexa)
          #entities_on
          for entity in self.entities_on:
            state = self.get_state(entity)
            if state == "off":
              self.turn_on(entity)
              self.log(self.message_off.format(self.friendly_name(entity)))
              self.notifier.notify(self.notify_name, message=self.message_off.format(self.friendly_name(entity)), useAlexa=self.use_alexa)
            if state == "closed":
              self.log(self.message_reed_off.format(self.friendly_name(entity)))
              self.notifier.notify(self.notify_name, message=self.message_reed_off.format(self.friendly_name(entity)), useAlexa=self.use_alexa)

  def terminate(self):
    for listen_state_handle in self.listen_state_handle_list:
      self.cancel_listen_state(listen_state_handle)
      
