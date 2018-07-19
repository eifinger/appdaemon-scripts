import appdaemon.plugins.hass.hassapi as hass
import messages

class DeviceNotify(hass.Hass):

  def initialize(self):
    self.listen_event_handle_list = []

    self.listen_event_handle_list.append(self.listen_event(self.newDevice, "device_tracker_new_device"))

  def newDevice(self, event_name, data, kwargs):
    self.log("event_name: {}".format(event_name))
    self.log("data: {}".format(data))
    message = messages.unknown_device_connected().format(data)
    self.call_service("notify/group_notifications",message=message)

  def terminate(self):
    for listen_event_handle in self.listen_event_handle_list:
      self.cancel_listen_event(listen_event_handle)
