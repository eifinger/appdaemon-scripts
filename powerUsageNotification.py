import appdaemon.plugins.hass.hassapi as hass
import globals
import messages

#
# App which notifies you when a power usage sensor indicated a device is on/off
#
#
# Args:
#
# sensor: power sensor. example: sensor.dishwasher_power_usage
# notify_name: Who to notify. example: group_notifications
# delay: seconds to wait until a the device is considered "off". example: 60
# threshold: amount of "usage" which indicated the device is on. example: 2
# alternative_name: Name to use in notification. example: Waschmaschine
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class PowerUsageNotification(hass.Hass):

    def initialize(self):
    
        self.timer_handle_list = []
        self.listen_event_handle_list = []
        self.listen_state_handle_list = []

        self.sensor = globals.get_arg(self.args,"sensor")
        self.alternative_name = globals.get_arg(self.args,"alternative_name")
        self.notify_name = globals.get_arg(self.args,"notify_name")
        self.delay = globals.get_arg(self.args,"delay")
        self.threshold = globals.get_arg(self.args,"threshold")

        self.triggered = False
        self.isWaitingHandle = None

        # Subscribe to sensors
        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.sensor))

    
    def state_change(self, entity, attribute, old, new, kwargs):
        # Initial: power usage goes up
        if ( new != None and new != "" and not self.triggered and float(new) > self.threshold ):
            self.triggered = True
            self.log("Power Usage is: {}".format(float(new)))
            self.log("Setting triggered to: {}".format(self.triggered))
            self.call_service("notify/" + self.notify_name,message=messages.power_usage_on().format(self.alternative_name))
        # Power usage goes down below threshold
        elif ( new != None and new != "" and self.triggered and self.isWaitingHandle == None and float(new) <= self.threshold):
            self.log("Waiting: {} seconds to notify.".format(self.delay))
            self.isWaitingHandle = self.run_in(self.notify_device_off,self.delay)
            self.log("Setting isWaitingHandle to: {}".format(self.isWaitingHandle))
            self.timer_handle_list.append(self.isWaitingHandle)
        # Power usage goes up before delay
        elif( new != None and new != "" and self.triggered and self.isWaitingHandle != None and float(new) > self.threshold):
            self.log("Cancelling timer")
            self.cancel_timer(self.isWaitingHandle)
            self.isWaitingHandle = None
            self.log("Setting isWaitingHandle to: {}".format(self.isWaitingHandle))


    def notify_device_off(self, kwargs):
        """Notify User that device is off. This may get cancelled if it turns on again in the meantime"""
        self.triggered = False
        self.log("Setting triggered to: {}".format(self.triggered))
        self.isWaitingHandle = None
        self.log("Setting isWaitingHandle to: {}".format(self.isWaitingHandle))
        self.log("Notifying user")
        self.call_service("notify/" + self.notify_name,message=messages.power_usage_off().format(self.alternative_name))
        

    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)