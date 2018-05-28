import appdaemon.plugins.hass.hassapi as hass
import messages
#
# App to send notification when a login attemp fails
#
# Args:

# Release Notes
#
# Version 1.0:
#   Initial Version

class NotifyFailedLogin(hass.Hass):

  def initialize(self):
    self.listen_state_handle_list = []
    self.listen_state_handle_list.append(self.listen_state(self.state_change, "persistent_notification.httplogin"))
    
  def state_change(self, entity, attribute, old, new, kwargs):
    if new != "" and new != "unkown":
        self.log("Failed login attempt detected.")
        self.call_service("notify/slack",message=messages.failed_login_detected())

  def terminate(self):
    for listen_state_handle in self.listen_state_handle_list:
      self.cancel_listen_state(listen_state_handle)
      