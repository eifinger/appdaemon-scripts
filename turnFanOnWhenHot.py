import appdaemon.plugins.hass.hassapi as hass
import globals
import datetime

#
# App to Turn on fan when temp is above a threshold and someone is in the room
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
# temp_sensor: temp sensor to monitor. example: sensor.large_lamp_temperature
# threshold_entity: entity which holds the temp threshold which must be reached. example: input_number.turn_fan_on_when_hot_threshold
# location_sensors: location sensors of users. example: sensor.location_user_one,sensor.location_user_two
# room: Room name in which one of the users must be. example: Wohnzimmer
# actor: actor to turn on
# delay: seconds to wait before turning off. example: 120
# Release Notes
#
# Version 1.3:
#   Added delay
#
# Version 1.2:
#   Using entities from HA now. Added turned_on_by_me
#
# Version 1.1:
#   Only turn on when someone is in the room. Turn off otherwise
#
# Version 1.0:
#   Initial Version

class TurnFanOnWhenHot(hass.Hass):

  def initialize(self):
    self.listen_state_handle_list = []
    self.timer_handle_list = []

    self.app_switch = globals.get_arg(self.args,"app_switch")
    self.temp_sensor = globals.get_arg(self.args,"temp_sensor")
    self.threshold_entity = globals.get_arg(self.args,"threshold_entity")
    self.location_sensors = globals.get_arg_list(self.args,"location_sensors")
    self.room = globals.get_arg(self.args,"room")
    self.actor = globals.get_arg(self.args,"actor")
    self.delay = globals.get_arg(self.args,"delay")

    self.turned_on_by_me = False #Giggedi

    self.turn_off_timer_handle = None

    self.listen_state_handle_list.append(self.listen_state(self.state_change, self.temp_sensor))
    for sensor in self.location_sensors:
      self.listen_state_handle_list.append(self.listen_state(self.state_change, sensor))
    
  def state_change(self, entity, attribute, old, new, kwargs):
    if self.get_state(self.app_switch) == "on":
      turn_on = False
      if (self.get_state(self.temp_sensor) != None and self.get_state(self.temp_sensor) != "unkown" 
      and self.get_state(self.threshold_entity) != None
      and float(self.get_state(self.temp_sensor)) > float(self.get_state(self.threshold_entity))):
        for sensor in self.location_sensors:
          if self.get_state(sensor) == self.room:
            if self.get_state(self.actor) != "on":
              self.log("{} is {}. This is above theshold of {}".format(self.friendly_name(self.temp_sensor), self.get_state(self.temp_sensor), self.get_state(self.threshold_entity)))
              self.log("{} is in {}".format(sensor, self.room))
              self.log("Turning on {}".format(self.friendly_name(self.actor)))
              self.turn_on(self.actor)
              self.turned_on_by_me = True
            turn_on = True
            if self.turn_off_timer_handle != None:
              self.log("handle is: {}".format(self.turn_off_timer_handle))
              self.log("list size is: {}".format(len(self.timer_handle_list)))
              self.timer_handle_list.remove(self.turn_off_timer_handle)
              self.cancel_timer(self.turn_off_timer_handle)
              self.turn_off_timer_handle = None
      if not turn_on and self.turned_on_by_me:
        if self.get_state(self.actor) != "off":
          self.turn_off_timer_handle = self.run_in(self.turn_off_callback,self.delay)
          self.timer_handle_list.append(self.turn_off_timer_handle)
            

  def turn_off_callback(self, kwargs):
    """Turn off the actor again if the timer was not cancelled in the meantime"""
    self.log("Turning off {}".format(self.friendly_name(self.actor)))
    self.turn_off(self.actor)
    self.turned_on_by_me = False
    self.turn_off_timer_handle = None


  def terminate(self):
    for listen_state_handle in self.listen_state_handle_list:
      self.cancel_listen_state(listen_state_handle)

    for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)
      
