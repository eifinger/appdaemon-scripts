import appdaemon.plugins.hass.hassapi as hass
import globals
#
# App to send notification when a login attempt fails
#
# Args:
#  notify_name: who to notifiy
#
# Release Notes
#
# Version 1.3.1:
#   Use consistent message variable
#
# Version 1.3:
#   use Notify App
#
# Version 1.2:
#   message now directly in own yaml instead of message module
#
# Version 1.1:
#   Using globals now
#
# Version 1.0:
#   Initial Version


class NotifyFailedLogin(hass.Hass):

    def initialize(self):

        self.timer_handle_list = []
        self.listen_event_handle_list = []
        self.listen_state_handle_list = []


        self.notify_name = globals.get_arg(self.args, "notify_name")
        self.message = globals.get_arg(self.args, "message")

        self.notifier = self.get_app('Notifier')

        self.listen_state_handle_list.append(self.listen_state(self.state_change, "persistent_notification.httplogin"))

    def state_change(self, entity, attribute, old, new, kwargs):
        if new != "" and new == "notifying":
            message = self.get_state("persistent_notification.httplogin",attribute="message")
            self.log(message)
            self.notifier.notify(self.notify_name, self.message.format(message), useAlexa=False)

    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
