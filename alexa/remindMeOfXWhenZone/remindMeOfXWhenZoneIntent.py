import appdaemon.plugins.hass.hassapi as hass
import datetime

__ZONE_ACTION_ENTER__ = "kommen"
__ZONE_ACTION_LEAVE__ = "verlassen"


class RemindMeOfXWhenZoneIntent(hass.Hass):
    def initialize(self):
        self.timer_handle_list = []
        self.listen_state_handle_list = []

        self.device_tracker = self.args["device_tracker"]
        self.notify_name = self.args["notify_name"]
        self.remindMessageSkeleton = self.args["remindMessageSkeleton"]

        self.notifier = self.get_app("Notifier")
        return

    def getIntentResponse(self, slots, devicename):
        ############################################
        # an Intent to give back the state from a light.
        # but it also can be any other kind of entity
        ############################################
        try:
            # get zone_name for friendly name used when talking to alexa
            zone_name = None
            for key, value in self.args["zoneMapping"].items():
                if key == slots["zone"].lower():
                    zone_name = value
            # listen to a state change of the zone
            if zone_name == None:
                raise Exception(
                    "Could not find zonemapping for: {}".format(slots["zone"].lower())
                )
            else:
                self.listen_state_handle_list.append(
                    self.listen_state(
                        self.remind_callback,
                        self.device_tracker,
                        zone=slots["zone"],
                        zoneAction=slots["zoneAction"],
                        reminder=slots["reminder"],
                    )
                )
                # set correct zoneAction response
                if slots["zoneAction"] == __ZONE_ACTION_ENTER__:
                    text = self.args["textLine"] + self.args["textEnter"]
                else:
                    text = self.args["textLine"] + self.args["textLeave"]
        except Exception as e:
            self.log("Exception: {}".format(e))
            self.log("slots: {}".format(slots))
            text = self.random_arg(self.args["Error"])
        return text

    def remind_callback(self, entity, attribute, old, new, kwargs):
        if kwargs["zoneAction"] == __ZONE_ACTION_ENTER__:
            if new != old and new == kwargs["zone"]:
                self.log("Notifying")
                self.notifier.notify(
                    self.notify_name,
                    self.remindMessageSkeleton + kwargs["reminder"],
                    useAlexa=False,
                )
        elif kwargs["zoneAction"] == __ZONE_ACTION_LEAVE__:
            if new != old and old == kwargs["zone"]:
                self.log("Notifying")
                self.notifier.notify(
                    self.notify_name,
                    self.remindMessageSkeleton + kwargs["reminder"],
                    useAlexa=False,
                )

    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
