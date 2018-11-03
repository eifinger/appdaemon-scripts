import appdaemon.plugins.hass.hassapi as hass
import globals
#
# App which increments a counter on a given service call
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.warm_bath_before_wakeup
# domain: domain of the service call. example: homeassistant
# service: service name of the service call. example: update_entity
# entity_id: entity_id in the service call. example: sensor.travel_time_home_user_one
# counter: increase a counter each time the service gets called. example: counter.google_maps_api_calls 
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class IncreaseCounterOnServiceCall(hass.Hass):

  def initialize(self):
    self.timer_handle_list = []
    self.listen_event_handle_list = []

    self.app_switch = globals.get_arg(self.args,"app_switch")
    self.domain = globals.get_arg(self.args,"domain")
    self.service = globals.get_arg(self.args,"service")
    self.entity_id = globals.get_arg(self.args,"entity_id")
    self.counter = globals.get_arg(self.args,"counter")

    self.listen_event_handle_list.append(self.listen_event(self.call_service_callback, "call_service"))
    
  def call_service_callback(self, event_name, data, kwargs):
    self.log(event_name + ': ' + str(data))
    if (self.get_state(self.app_switch) == "on" and data["domain"] == self.domain 
    and data["service"] == self.service and data["service_data"]["entity_id"] == self.entity_id):
      self.call_service("counter/increment", entity_id=self.counter)
      self.log("Incremented {} to {}".format(self.friendly_name(self.counter), self.get_state(self.counter)))

  def terminate(self):
    for timer_handle in self.timer_handle_list:
      self.cancel_timer(timer_handle)

    for listen_event_handle in self.listen_event_handle_list:
      self.cancel_listen_event(listen_event_handle)
      
