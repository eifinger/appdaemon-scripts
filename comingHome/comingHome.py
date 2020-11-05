import appdaemon.plugins.hass.hassapi as hass
import datetime

#
# App to Turn on Lobby Lamp when Door openes and no one is Home
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
# sensor: door sensor
# isHome: input_boolean which shows if someone is home eg input_boolean.isHome
# actor (optional): actor to turn on. example: script.receiver_set_source_bluetooth
# service (optional): service to call. example: media_player.volume_set
# service_data (optional): dictionary of attributes for the service call.
# after_sundown (optional): whether to only trigger after sundown. example: True
# Release Notes
#
# Version 1.4.2:
#   unwrap service_data
#
# Version 1.4.1:
#   fix duplicate line for self.actor
#
# Version 1.4:
#   Add service and service_data and make actor optional
#
# Version 1.3.2:
#   Check for new != old
#
# Version 1.3.1:
#   Actually implement isHome
#
# Version 1.3:
#   Added app_switch
#
# Version 1.2:
#   Added after_sundown
#
# Version 1.1:
#   Using globals
#
# Version 1.0:
#   Initial Version


class ComingHome(hass.Hass):
    def initialize(self):
        """
        Initialize the service.

        Args:
            self: (todo): write your description
        """
        self.listen_state_handle_list = []

        self.app_switch = self.args["app_switch"]
        self.sensor = self.args["sensor"]
        self.isHome = self.args["isHome"]
        self.actor = self.args.get("actor")
        self.service = self.args.get("service")
        self.service_data = self.args.get("service_data")
        self.after_sundown = self.args.get("after_sundown")

        self.delay = 2

        self.listen_state_handle_list.append(
            self.listen_state(self.state_change, self.sensor)
        )

    def state_change(self, entity, attribute, old, new, kwargs):
        """
        Changes the state of an entity.

        Args:
            self: (todo): write your description
            entity: (todo): write your description
            attribute: (str): write your description
            old: (str): write your description
            new: (str): write your description
        """
        if self.get_state(self.app_switch) == "on":
            if new != "" and new != old:
                isHome_attributes = self.get_state(self.isHome, attribute="all")
                isHome_state = isHome_attributes["state"]
                last_changed = self.convert_utc(isHome_attributes["last_changed"])
                if isHome_state == "off" or (
                    datetime.datetime.now(datetime.timezone.utc) - last_changed
                    <= datetime.timedelta(seconds=self.delay)
                ):
                    if self.after_sundown is not None and self.after_sundown:
                        if self.sun_down():
                            self.turn_on_actor(self.actor, entity, new)
                            self.my_call_service(
                                self.service, self.service_data, entity, new
                            )
                    else:
                        self.turn_on_actor(self.actor, entity, new)
                        self.my_call_service(
                            self.service, self.service_data, entity, new
                        )

    def turn_on_actor(self, actor, entity, new):
        """
        Turn on on the actor.

        Args:
            self: (todo): write your description
            actor: (float): write your description
            entity: (todo): write your description
            new: (str): write your description
        """
        if self.actor is not None:
            self.log("{} changed to {}".format(self.friendly_name(entity), new))
            self.turn_on(actor)

    def my_call_service(self, service, service_data, entity, new):
        """
        Calls the given service.

        Args:
            self: (todo): write your description
            service: (todo): write your description
            service_data: (str): write your description
            entity: (todo): write your description
            new: (todo): write your description
        """
        if self.service is not None:
            if self.service_data is not None:
                self.log("{} changed to {}".format(self.friendly_name(entity), new))
                self.call_service(service, **service_data)

    def terminate(self):
        """
        Terminate all active tasks.

        Args:
            self: (todo): write your description
        """
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
