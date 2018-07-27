import appdaemon.plugins.hass.hassapi as hass
import globals
#
# App to Turn on fan when temp is above a threshold and someone is Home
#
# Args:
#
# temp_sensor: temp sensor to monitor. example: sensor.large_lamp_temperature
# threshold: temp treshhold which must be reached. example: 28
# location_sensors: location sensors of users. example: sensor.location_user_one,sensor.location_user_two
# room: Room name in which one of the users must be. example: Wohnzimmer
# actor: actor to turn on
# Release Notes
#
# Version 1.1:
#   Only turn on when someone is in the room. Turn off otherwise
#
# Version 1.0:
#   Initial Version

class TurnFanOnWhenHot(hass.Hass):

  def initialize(self):
    self.listen_state_handle_list = []

    self.temp_sensor = globals.get_arg(self.args,"temp_sensor")
    self.threshold = globals.get_arg(self.args,"threshold")
    self.location_sensors = globals.get_arg_list(self.args,"location_sensors")
    self.room = globals.get_arg(self.args,"room")
    self.actor = globals.get_arg(self.args,"actor")

    self.listen_state_handle_list.append(self.listen_state(self.state_change, self.temp_sensor))
    for sensor in self.location_sensors:
      self.listen_state_handle_list.append(self.listen_state(self.state_change, sensor))
    
  def state_change(self, entity, attribute, old, new, kwargs):
    turn_on = False
    if float(self.get_state(self.temp_sensor)) > self.threshold:
      for sensor in self.location_sensors:
        if self.get_state(sensor) == self.room:
          if self.get_state(self.actor) != "on":
            self.log("{} is {}. This is above theshold of {}".format(self.friendly_name(self.temp_sensor), self.get_state(self.temp_sensor), self.threshold))
            self.log("{} is in {}".format(sensor, self.room))
            self.log("Turning on {}".format(self.friendly_name(self.actor)))
            self.turn_on(self.actor)
          turn_on = True
    if not turn_on:
      if self.get_state(self.actor) != "off":
        self.log("Turning off {}".format(self.friendly_name(self.actor)))
        self.turn_off(self.actor)


  def terminate(self):
    for listen_state_handle in self.listen_state_handle_list:
      self.cancel_listen_state(listen_state_handle)
      
