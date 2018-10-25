import appdaemon.plugins.hass.hassapi as hass
import globals
import datetime
#
# App which sets a thermostat to a target temperature based on a time from an entity
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.warm_bath_before_wakeup
# time_entity: sensor which determines when to run in the format 14:30. example: sensor.alarm_time
# upfront_time: how many minutes before the time_sensor to run. example: 60
# duration: After how many minutes should the thermostat be set back to its previous value. example: 60
# climat_entity: climate entity to set. example: climate.bad_thermostat
# target_entity: the entity holding the target temp. example: warm_bath_before_wakeup
# message: message to use in notification
# notify_name: who to notify. example: group_notifications
# use_alexa: use alexa for notification. example: False
#
# Release Notes
#
# Version 1.1:
#   Actually set the previous temp
#
# Version 1.0:
#   Initial Version

class SetThermostat(hass.Hass):

  def initialize(self):
    self.timer_handle_list = []
    self.listen_state_handle_list = []

    self.app_switch = globals.get_arg(self.args,"app_switch")
    self.time_entity = globals.get_arg(self.args,"time_entity")
    self.upfront_time = globals.get_arg(self.args,"upfront_time")
    self.duration = globals.get_arg(self.args,"duration")
    self.climat_entity = globals.get_arg(self.args,"climat_entity")
    self.target_entity = globals.get_arg(self.args,"target_entity")
    self.message = globals.get_arg(self.args,"message")
    self.notify_name = globals.get_arg(self.args,"notify_name")
    self.use_alexa = globals.get_arg(self.args,"use_alexa")

    self.notifier = self.get_app('Notifier')

    self.run_timer = None
    
    self.listen_state_handle_list.append(self.listen_state(self.state_change, self.time_entity))
    self.state_change(None,None,None,"Run",None)
    
  def state_change(self, entity, attribute, old, new, kwargs):
    if new != "":
      if self.run_timer != None:
        self.cancel_timer(self.run_timer)
      time_entity_state = self.get_state(self.time_entity)
      runtime = datetime.time(int(time_entity_state.split(":")[0]),int(time_entity_state.split(":")[1]))
      today = datetime.date.today()
      rundatetime = datetime.datetime.combine(today, runtime)
      event_time = rundatetime - datetime.timedelta(minutes=int(self.upfront_time))

      #check if event is in the past
      if datetime.datetime.now() > event_time:
          event_time = event_time + datetime.timedelta(days=1)

      self.run_timer = self.run_at(self.trigger_thermostat, event_time)
      self.timer_handle_list.append(self.run_timer)
      self.log("Theromstat will trigger at {}".format(event_time))

  def trigger_thermostat(self, kwargs):
    if self.get_state(self.app_switch) == "on":
      self.log(self.message.format(self.friendly_name(self.climat_entity), self.get_state(self.target_entity)))
      self.notifier.notify(self.notify_name, self.message.format(self.friendly_name(self.climat_entity), self.get_state(self.target_entity)), useAlexa=self.use_alexa)
      self.log("Turning {} on".format(self.climat_entity))
      self.call_service("climate/turn_on", entity_id=self.climat_entity)
      self.previous_temp = self.get_state(self.climat_entity, attribute="all")["attributes"]["temperature"]
      self.call_service("climate/set_temperature", entity_id=self.climat_entity, temperature=self.get_state(self.target_entity))
      self.log("Resetting Thermostat in {} minutes.".format(self.duration))
      self.timer_handle_list.append(self.run_in(self.reset_thermostat, float(self.duration)*60))

  def reset_thermostat(self, kwargs):
    if self.previous_temp != None:
      self.log(self.message.format(self.friendly_name(self.climat_entity), self.previous_temp))
      self.notifier.notify(self.notify_name, self.message.format(self.friendly_name(self.climat_entity), self.previous_temp), useAlexa=self.use_alexa)
      self.call_service("climate/set_temperature", entity_id=self.climat_entity, temperature=self.previous_temp)

    

  def terminate(self):
    for timer_handle in self.timer_handle_list:
      self.cancel_timer(timer_handle)

    for listen_state_handle in self.listen_state_handle_list:
      self.cancel_listen_state(listen_state_handle)
      
