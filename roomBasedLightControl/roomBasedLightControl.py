import appdaemon.plugins.hass.hassapi as hass
import datetime
import globals
#
# App which turns on the light based on the room the user is currently in
#
#
# Args:
# room_sensor: the sensor which shows the room the user is in. example: sensor.mqtt_room_user_one
# entity: The entity which gets turned on by alexa/snips. example: input_boolean.room_based_light
# mappings:
#  livingroom:
#    room: name of the room
#    entity: entity to turn on
#
# Release Notes
#
# Version 1.2:
#   None Check
#
# Version 1.1:
#   Using globals
#
# Version 1.0:
#   Initial Version

class RoomBasedLightControl(hass.Hass):

    def initialize(self):

        self.listen_state_handle_list = []
        self.timer_handle_list = []

        self.room_sensor = globals.get_arg(self.args,"room_sensor")
        self.entity = globals.get_arg(self.args,"entity")
        self.mappings = self.args["mappings"]

        self.mappings_dict = {}

        for mapping in self.mappings:
            self.mappings_dict[self.mappings[mapping]["room"]] = self.mappings[mapping]["entity"]

        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.entity))

    def state_change(self, entity, attributes, old, new, kwargs):
        self.log("{} turned {}".format(self.friendly_name(self.entity),new))
        room = self.get_state(self.room_sensor)
        self.log("User is in room {}".format(room))
        mapped_entity = self.mappings_dict.get(room)
        self.log("Entity for that room is: {}".format(mapped_entity))
        if mapped_entity != None:
            if new == "on":
                self.log("Turning {} on".format(mapped_entity))
                self.turn_on(mapped_entity)
            elif new == "off":
                self.log("Turning {} off".format(mapped_entity))
                self.turn_off(mapped_entity)

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)