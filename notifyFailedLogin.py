import appdaemon.plugins.hass.hassapi as hass
import messages
import secrets
#
# App to send notification when a login attemp fails
#
# Args:
#  user_name: who to notifiy
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class NotifyFailedLogin(hass.Hass):

  def initialize(self):
    self.user_name = self.args["user_name"]
    if self.user_name.startswith("secret_"):
          self.user_name = self.get_secret(self.user_name)
    self.listen_state_handle_list = []
    self.listen_state_handle_list.append(self.listen_state(self.state_change, "persistent_notification.httplogin"))
    
  def state_change(self, entity, attribute, old, new, kwargs):
    if new != "" and new == "notifying":
        message = self.get_state("persistent_notification.httplogin",attribute="message")
        self.log(message)
        self.call_service("notify/" + self.user_name,message=messages.failed_login_detected().format(message))

  def get_secret(self, key):
      if key in secrets.secret_dict:
          return secrets.secret_dict[key]
      else:
          self.log("Could not find {} in secret_dict".format(key))

  def terminate(self):
    for listen_state_handle in self.listen_state_handle_list:
      self.cancel_listen_state(listen_state_handle)
      