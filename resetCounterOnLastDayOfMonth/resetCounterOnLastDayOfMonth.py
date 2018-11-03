import appdaemon.plugins.hass.hassapi as hass
import datetime
import globals
#
# App which resets a counter on the last day of month
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.warm_bath_before_wakeup
# time: domain of the service call. example: homeassistant
# counter: increase a counter each time the service gets called. example: counter.google_maps_api_calls 
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class ResetCounterOnLastDayOfMonth(hass.Hass):

  def initialize(self):
    self.timer_handle_list = []

    self.app_switch = globals.get_arg(self.args,"app_switch")
    self.time = globals.get_arg(self.args,"time")
    self.counter = globals.get_arg(self.args,"counter")

    runtime = self.get_next_run_time()
    self.log("Next reset will be: {}".format(runtime))
    self.timer_handle_list.append(self.run_at(self.run_at_callback, runtime))

  def run_at_callback(self, kwargs):
    if self.get_state(self.app_switch) == "on":
      self.call_service("counter/reset", entity_id=self.counter)
      self.log("Reset {} to {}".format(self.friendly_name(self.counter), self.get_state(self.counter)))
      runtime = self.get_next_run_time()
      self.log("Next reset will be: {}".format(runtime))
      self.timer_handle_list.append(self.run_at(self.run_at_callback, runtime))

  def last_day_of_month(any_day):
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)  # this will never fail
    return next_month - datetime.timedelta(days=next_month.day)

  def get_next_run_time(self):
    today = datetime.date.today()
    last_day_of_month = self.last_day_of_month(today)
    hours = self.time.split(":",1)[0]
    minutes = self.time.split(":",1)[1]
    runtime = datetime.time(int(hours),int(minutes))

    return datetime.datetime.combine(last_day_of_month, runtime)
    

  def terminate(self):
    for timer_handle in self.timer_handle_list:
      self.cancel_timer(timer_handle)
      
