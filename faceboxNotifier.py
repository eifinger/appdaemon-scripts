import appdaemon.plugins.hass.hassapi as hass
import globals
import messages
import shutil
import os
import time
#
# App which runs facebox face detection and notifies the result
#
#
# Args:
#
# sensor: binary sensor to use as trigger
# button: xiaomi button to use as a trigger
# camera : camera entity. example: camera.ip_webcam
# filename : filename to write image file to. example: /config/www/facebox/tmp/image.jpg
# image_processing: image_processing entity to call. example: image_processing.facebox_saved_images
# known_faces: comma separated names of known faces. example: Tina,Markus
# notify_name: Who to notify. example: group_notifications
# wol_switch: Wake on Lan switch which turns on the facebox server. example: switch.facebox_wol
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
        self.button = globals.get_arg(self.args,"button")
        self.camera = globals.get_arg(self.args,"camera")
        self.filename = globals.get_arg(self.args,"filename")
        self.image_processing = globals.get_arg(self.args,"image_processing")
        self.known_faces = globals.get_arg_list(self.args,"known_faces")
        self.notify_name = globals.get_arg(self.args,"notify_name")
        self.wol_switch = globals.get_arg(self.args,"wol_switch")

        self.facebox_source_directory = "/config/www/facebox/"
        self.facebox_unknown_directory = "/config/www/facebox/unknown"

        # Subscribe to sensors
        self.listen_event_handle_list.append(self.listen_event(self.button_clicked, "click"))
        self.listen_state_handle_list.append(self.listen_state(self.triggered,self.sensor))

    def button_clicked(self, event_name, data, kwargs):
        if data["entity_id"] == self.button:
            if data["click_type"] == "single":
                self.timer_handle_list.append(self.run_in(self.sendWakeOnLan,1.5))

    def triggered(self, entity, attribute, old, new, kwargs):
        if new == "on":
            self.timer_handle_list.append(self.run_in(self.sendWakeOnLan,1.5))

    def sendWakeOnLan(self, kwargs):
        self.log("Sending WoL")
        self.turn_on(self.wol_switch)
        self.timer_handle_list.append(self.run_in(self.takeSnapshot,1.5))

    def takeSnapshot(self, kwargs):
        self.log("Calling camera/snapshot")
        self.call_service("camera/snapshot", entity_id = self.camera, filename = self.filename)
        self.timer_handle_list.append(self.run_in(self.triggerImageProcessing,2))

    def triggerImageProcessing(self, kwargs):
        self.log("Calling image_processing/scan")
        self.call_service("image_processing/scan", entity_id = self.image_processing)
        self.timer_handle_list.append(self.run_in(self.processImageProcessingResult,2))

    def processImageProcessingResult(self, kwargs):
        image_processing_state = self.get_state(self.image_processing, attribute = "all")
        matched_faces = image_processing_state["attributes"]["matched_faces"]
        total_faces = image_processing_state["attributes"]["total_faces"]
        if total_faces == 0:
            self.log("No faces were detected.")
        elif total_faces == 1:
            face_identified = False
            for face in self.known_faces:
                if face in matched_faces:
                    face_identified = True
                    self.log(messages.identified_face().format(face))
                    self.call_service("notify/" + self.notify_name,message=messages.identified_face().format(face))
                    #copy file for training
                    directory = self.facebox_source_directory + face
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    filename =  directory + "/" + time.strftime("%Y%m%d%H%M%S.jpg")
                    self.log("Copy file from {} to {}".format(self.filename, filename))
                    shutil.copyfile(self.filename, filename)
            if not face_identified:
                self.log("Unknown face")
                self.call_service("notify/" + self.notify_name,message=messages.unknown_face_detected())
                #copy file for training
                directory = self.facebox_unknown_directory
                if not os.path.exists(directory):
                    os.makedirs(directory)
                filename =  directory + "/" + time.strftime("%Y%m%d%H%M%S.jpg")
                self.log("Copy file from {} to {}".format(self.filename, filename))
                shutil.copyfile(self.filename, filename)

        
    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)