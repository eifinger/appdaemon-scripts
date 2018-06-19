import appdaemon.appapi as appapi
import messages

class DeviceNotify(appapi.AppDaemon):

  def initialize(self):
    self.listen_event_handle_list = []

    self.listen_event_handle_list.append(self.listen_event(self.newDevice, "device_tracker"))

  def newDevice(self, event_name, data, kwargs):
    if event_name == "device_tracker_new_device":
        message = messages.unknown_device_connected().format(data)
        self.call_service("notify/group_notifications",message=message)

  def terminate(self):
    for listen_event_handle in self.listen_event_handle_list:
      self.cancel_listen_event(listen_event_handle)
