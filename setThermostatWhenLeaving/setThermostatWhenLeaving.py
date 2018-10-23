import appdaemon.plugins.hass.hassapi as hass
import globals
#
# App which sets a thermostat to a target temperature when leaving
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.warm_bath_before_wakeup
# sensor: door sensor
# climate_entity: climate entity to set. example: climate.bad_thermostat
# target_entity: the entity holding the target temp. example: warm_bath_before_wakeup
# message (optional): message to use in notification
# notify_name (optional): who to notify. example: group_notifications
# use_alexa (optional): use alexa for notification. example: False
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class SetThermostatWhenLeaving(hass.Hass):

  def initialize(self):
    self.timer_handle_list = []
    self.listen_state_handle_list = []

    self.app_switch = globals.get_arg(self.args,"app_switch")
    self.sensor = globals.get_arg(self.args,"sensor")
    self.climate_entity = globals.get_arg(self.args,"climate_entity")
    self.target_entity = globals.get_arg(self.args,"target_entity")
    try:
      self.message = globals.get_arg(self.args,"message")
    except KeyError:
      self.message = None
    try:
      self.notify_name = globals.get_arg(self.args,"notify_name")
    except KeyError:
      self.notify_name = None
    try:
      self.use_alexa = globals.get_arg(self.args,"use_alexa")
    except KeyError:
      self.use_alexa = False

    self.notifier = self.get_app('Notifier')

    self.listen_state_handle_list.append(self.listen_state(self.state_change, self.sensor))
    
  def state_change(self, entity, attribute, old, new, kwargs):
    if self.get_state(self.app_switch) == "on":
      if new == "off" and old != new:
        if self.message != None:
          self.log(self.message.format(self.friendly_name(self.climate_entity), self.get_state(self.target_entity)))
        if self.notify_name != None:
          self.notifier.notify(self.notify_name, self.message.format(self.friendly_name(self.climate_entity), self.get_state(self.target_entity)), useAlexa=self.use_alexa)
        self.call_service("climate/turn_on", entity_id=self.climate_entity)
        self.call_service("climate/set_temperature", entity_id=self.climate_entity, temperature=self.get_state(self.target_entity))

  def terminate(self):
    for timer_handle in self.timer_handle_list:
      self.cancel_timer(timer_handle)

    for listen_state_handle in self.listen_state_handle_list:
      self.cancel_listen_state(listen_state_handle)
      
