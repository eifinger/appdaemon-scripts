import appdaemon.plugins.hass.hassapi as hass
import globals
#
# App which notifies you when a power usage sensor indicated a device is on/off
#
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
# sensor: power sensor. example: sensor.dishwasher_power_usage
# notify_name: Who to notify. example: group_notifications
# delay: seconds to wait until a the device is considered "off". example: 60
# threshold: amount of "usage" which indicated the device is on. example: 2
# alternative_name: Name to use in notification. example: Waschmaschine
#
# Release Notes
#
# Version 1.3:
#   use Notify App
#
# Version 1.2:
#   message now directly in own yaml instead of message module
#
# Version 1.1:
#   Added app_switch
#
# Version 1.0:
#   Initial Version

class PowerUsageNotification(hass.Hass):

    def initialize(self):
    
        self.timer_handle_list = []
        self.listen_event_handle_list = []
        self.listen_state_handle_list = []

        self.app_switch = globals.get_arg(self.args,"app_switch")
        self.sensor = globals.get_arg(self.args,"sensor")
        self.alternative_name = globals.get_arg(self.args,"alternative_name")
        self.notify_name = globals.get_arg(self.args,"notify_name")
        self.delay = globals.get_arg(self.args,"delay")
        self.threshold = globals.get_arg(self.args,"threshold")
        self.message = globals.get_arg(self.args,"message_DE")
        self.message_off = globals.get_arg(self.args,"message_off_DE")

        self.triggered = False
        self.isWaitingHandle = None

        self.notifier = self.get_app('Notifier')

        # Subscribe to sensors
        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.sensor))

    
    def state_change(self, entity, attribute, old, new, kwargs):
        if self.get_state(self.app_switch) == "on":
            # Initial: power usage goes up
            if ( new != None and new != "" and not self.triggered and float(new) > self.threshold ):
                self.triggered = True
                self.log("Power Usage is: {}".format(float(new)))
                self.log("Setting triggered to: {}".format(self.triggered))
                self.notifier.notify(self.notify_name, self.message.format(self.alternative_name))
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
        self.notifier.notify(self.notify_name, self.message_off.format(self.alternative_name))
        

    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)