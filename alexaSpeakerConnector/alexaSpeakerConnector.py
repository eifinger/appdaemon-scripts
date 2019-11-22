import appdaemon.plugins.hass.hassapi as hass
import globals

#
# App to Turn on Receiver Bluetooth when Alexa is playing something so it plays on the big speakers
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
# alexa_entity: the alexa media player entity. example: media_player.kevins_echo_dot_oben
# alexa_entity_source: source to set alexa to. example: Denon AVR-X1300W
# receiver: Receiver to turn on. example: media_player.denon_avr_x1300w
# receiver_source: source to set receiver to. example: Bluetooth
#
# Release Notes
#
# Version 1.2.0:
#   Introduce INITIAL_VOLUME
#
# Version 1.1.1:
#   Fix WAITING_TIME
#
# Version 1.1:
#   Introduce WAITING_TIME
#
# Version 1.0:
#   Initial Version

WAITING_TIME = 10
INITIAL_VOLUME = 0.3


class AlexaSpeakerConnector(hass.Hass):
    def initialize(self):
        self.listen_state_handle_list = []
        self.timer_handle_list = []

        self.app_switch = globals.get_arg(self.args, "app_switch")
        self.alexa_entity = globals.get_arg(self.args, "alexa_entity")
        self.alexa_entity_source = globals.get_arg(self.args, "alexa_entity_source")
        self.receiver = globals.get_arg(self.args, "receiver")
        self.receiver_source = globals.get_arg(self.args, "receiver_source")

        self.listen_state_handle_list.append(
            self.listen_state(self.state_change, self.alexa_entity)
        )

    def state_change(self, entity, attribute, old, new, kwargs):
        if self.get_state(self.app_switch) == "on":
            if new.lower() == "playing" and old.lower() != "playing":
                self.log("{} changed to {}".format(self.alexa_entity, new))
                # Only trigger when the receiver is off. Otherwise its probably playing something
                if self.get_state(self.receiver) == "off":
                    self.log(
                        "Setting source of {} to: {}".format(
                            self.receiver, self.receiver_source
                        )
                    )
                    self.call_service(
                        "media_player/select_source",
                        entity_id=self.receiver,
                        source=self.receiver_source,
                    )
                    self.call_service(
                        "media_player/volume_set",
                        entity_id=self.receiver,
                        volume_level=INITIAL_VOLUME,
                    )
                    self.timer_handle_list.append(
                        self.run_in(self.run_in_callback, WAITING_TIME)
                    )

    def run_in_callback(self, kwargs):
        """
        Callback method to introduce a waiting time for the receiver to come 'online'
        :return:
        """
        self.log(
            "Setting source of {} to: {}".format(
                self.alexa_entity, self.alexa_entity_source
            )
        )
        self.call_service(
            "media_player/select_source",
            entity_id=self.alexa_entity,
            source=self.alexa_entity_source,
        )

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)

        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)
