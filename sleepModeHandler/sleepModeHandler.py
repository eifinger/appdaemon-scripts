import appdaemon.plugins.hass.hassapi as hass


#
# App which sets the sleep mode on/off
#
# Args:
#   app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
#   sleepmode: input_boolean holding the sleepmode. example: input_boolean.sleepmode
#   users: configuration for users
#
# Release Notes
#
# Version 1.2:
#   Add use_alexa
#
# Version 1.1:
#   Only send notification if sleepmode is actually changed
#
# Version 1.0:
#   Initial Version


class SleepModeHandler(hass.Hass):
    def initialize(self):
        """
        Initialize the client

        Args:
            self: (todo): write your description
        """
        self.listen_state_handle_list = []

        self.app_switch = self.args["app_switch"]
        self.sleepmode = self.args["sleepmode"]
        self.users = self.args["users"]
        self.notify_name = self.args["notify_name"]
        self.message_sleeping = self.args["message_sleeping"]
        self.message_awake = self.args["message_awake"]

        try:
            self.use_alexa = self.args["use_alexa"]
        except KeyError:
            self.use_alexa = False

        self.notifier = self.get_app("Notifier")

        for user in self.users:
            self.listen_state_handle_list.append(
                self.listen_state(self.state_change, user["sleep_mode"])
            )

    def state_change(self, entity, attribute, old, new, kwargs):
        """
        Changes the state of the state change.

        Args:
            self: (todo): write your description
            entity: (todo): write your description
            attribute: (str): write your description
            old: (str): write your description
            new: (str): write your description
        """
        if self.get_state(self.app_switch) == "on":
            if new != "" and new != old:
                if new == "on":
                    if self.are_all_that_are_home_sleeping():
                        if self.get_state(self.sleepmode) == "off":
                            self.log("All at home are sleeping")
                            self.turn_on(self.sleepmode)
                            self.notifier.notify(
                                self.notify_name,
                                self.message_sleeping,
                                useAlexa=self.use_alexa,
                            )
                elif new == "off":
                    if self.are_all_that_are_home_awake():
                        if self.get_state(self.sleepmode) == "on":
                            self.log("All at home are awake")
                            self.turn_off(self.sleepmode)
                            self.notifier.notify(
                                self.notify_name,
                                self.message_awake,
                                useAlexa=self.use_alexa,
                            )

    def are_all_that_are_home_sleeping(self):
        """
        Return true if all home home home home home home home home home

        Args:
            self: (todo): write your description
        """
        for user in self.users:
            if self.get_state(user["isHome"]) == "on":
                if self.get_state(user["sleep_mode"]) != "on":
                    return False
        return True

    def are_all_that_are_home_awake(self):
        """
        Check if all home home home home home home home home

        Args:
            self: (todo): write your description
        """
        for user in self.users:
            if self.get_state(user["isHome"]) == "on":
                if self.get_state(user["sleep_mode"]) == "on":
                    return False
        return True

    def terminate(self):
        """
        Terminate all active tasks.

        Args:
            self: (todo): write your description
        """
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
