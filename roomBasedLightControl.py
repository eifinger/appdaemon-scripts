import appdaemon.plugins.hass.hassapi as hass
import datetime
import secrets
import messages

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
# Version 1.0:
#   Initial Version

class RoomBasedLightControl(hass.Hass):

    def initialize(self):

        self.listen_state_handle_list = []
        self.timer_handle_list = []

        self.room_sensor = self.get_arg("room_sensor")
        self.entity = self.get_arg("entity")
        self.mappings = self.args["mappings"]

        self.mappings_dict = {}

        for mapping in self.mappings:
            self.mappings_dict[self.mappings[mapping]["room"]] = self.mappings[mapping]["entity"]

        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.entity))

    def state_change(self, entity, attributes, old, new, kwargs):
        self.log("{} turned {}".format(self.friendly_name(self.entity),new))
        room = self.get_state(self.room_sensor)
        self.log("User is in room {}".format(room))
        entity = self.mappings_dict.get(room)
        self.log("Entity for that room is: {}".format(entity))

        if new == "on":
            self.log("Turning {} on".format(entity))
            self.turn_on(entity)
        elif new == "off":
            self.log("Turning {} off".format(entity))
            self.turn_off(entity)

    def get_arg(self, key):
        key = self.args[key]
        if key.startswith("secret_"):
            if key in secrets.secret_dict:
                return secrets.secret_dict[key]
            else:
                self.log("Could not find {} in secret_dict".format(key))
        else:
            return key

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)