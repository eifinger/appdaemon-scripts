import appdaemon.plugins.hass.hassapi as hass
import globals
import secrets

#
# App which runs facebox face detection and notifies the result
#
#
# Args:
#
# sensor: binary sensor to use as trigger
# camera : camera entity. example: camera.ip_webcam
# filename : filename to write image file to. example: /config/www/facebox/tmp/image.jpg
# image_processing: image_processing entity to call. example: image_processing.facebox_saved_images
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class FaceboxNotifier(hass.Hass):

    def initialize(self):
    
        self.timer_handle_list = []
        self.listen_event_handle_list = []
        self.listen_state_handle_list = []

        self.sensor = globals.get_arg(self.args,"sensor")
        self.camera = globals.get_arg(self.args,"camera")
        self.filename = globals.get_arg(self.args,"filename")
        self.image_processing = globals.get_arg(self.args,"image_processing")

        # Subscribe to sensors
        self.listen_event_handle_list.append(self.listen_event(self.motion_detected, "motion"))
        self.listen_event_handle_list.append(self.listen_event(self.event_detected, "click"))
        #self.listen_state_handle_list.append(self.listen_state(self.triggered,self.sensor))

    def event_detected(self, event_name, data, kwargs):
        if data["entity_id"] == self.sensor:
            if data["click_type"] == "single":
                self.call_service("camera/snapshot", entity_id = self.camera, filename = self.filename)
                self.timer_handle_list.append(self.run_in(self.triggerImageProcessing,2))

    def motion_detected(self, event_name, data, kwargs):
        self.log("Motion: event_name: {}, data: {}".format(event_name,data))

    def triggered(self, entity, attribute, old, new, kwargs):
        self.call_service("camera/snapshot", entity_id = self.camera, filename = self.filename)
        self.timer_handle_list.append(self.run_in(self.triggerImageProcessing,2))

    def triggerImageProcessing(self, kwargs):
        self.call_service("image_processing/scan", entity_id = self.image_processing)
        
    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)