import appdaemon.plugins.hass.hassapi as hass
import datetime

#
# App which toggles entities for single/double/hold presses of Xiaomi buttons connected via deconz
#
# Args:
#
# id: id of the xiaomi button
# actor_single: actor to toggle on single click
# actor_double: actor to toggle on double click
# actor_hold: actor to dim on hold
#
# Release Notes
#
# Version 2.0.2
#   use else when toggling
#
# Version 2.0.1
#   use elif when toggling
#
# Version 2.0:
#   Removed unneeded workaround for yeelight
#
# Version 1.0:
#   Initial Version


class DeconzXiaomiButton(hass.Hass):
    def initialize(self):
        self.listen_event_handle_list = []
        self.timer_handle_list = []

        self.actor_single = self.args.get("actor_single")
        self.actor_double = self.args.get("actor_double")
        self.actor_hold = self.args.get("actor_hold")
        self.id = self.args["id"]

        self.dimmer_timer_handle = None

        self.listen_event_handle_list.append(
            self.listen_event(self.event_detected, "deconz_event")
        )

    def event_detected(self, event_name, data, kwargs):
        if data["id"] == self.id:
            if data["event"] == 1002 and self.actor_single is not None:
                self.log("ButtonClicked: {}".format(data["id"]))
                self.log("Toggling {}".format(self.actor_double))
                # Is on
                if self.get_state(self.actor_single) == "on":
                    self.log("Turning {} off".format(self.actor_single))
                    self.turn_off(self.actor_single)
                # Is off
                else:
                    self.log("Turning {} on".format(self.actor_single))
                    self.turn_on(self.actor_single)

            if data["event"] == 1004 and self.actor_double is not None:
                self.log("Double Button Click: {}".format(data["id"]))
                self.log("Toggling {}".format(self.actor_double))
                # Is on
                if self.get_state(self.actor_double) == "on":
                    self.turn_off(self.actor_double)
                # Is off
                else:
                    self.log("Turning {} on".format(self.actor_double))
                    self.turn_on(self.actor_double)

            if data["event"] == 1001 and self.actor_hold is not None:
                self.log("Long Button Click: {}".format(data["id"]))
                self.log("Starting Dimmer")
                self.dimmer_timer_handle = self.run_every(
                    self.dimmer_callback,
                    datetime.datetime.now(),
                    0.5,
                    entity_id=self.actor_hold,
                )
                self.timer_handle_list.append(self.dimmer_timer_handle)

            if data["event"] == 1003 and self.actor_hold is not None:
                self.log("Button Release: {}".format(data["id"]))
                self.log("Stopping Dimmer")
                if self.dimmer_timer_handle is not None:
                    self.cancel_timer(self.dimmer_timer_handle)

    def dimmer_callback(self, kwargs):
        """Dimm the by 10% light. If it would dim above 100% start again at 10%"""
        brightness_pct_old = (
            int(
                self.get_state(self.actor_hold, attribute="all")["attributes"][
                    "brightness"
                ]
            )
            / 255
        )
        brightness_pct_new = brightness_pct_old + 0.1
        if brightness_pct_new > 1:
            brightness_pct_new = 0.1
        self.call_service(
            "light/turn_on",
            entity_id=kwargs["entity_id"],
            brightness_pct=brightness_pct_new * 100,
        )

    def terminate(self):
        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)

        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)
