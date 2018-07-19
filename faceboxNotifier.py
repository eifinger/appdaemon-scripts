import appdaemon.plugins.hass.hassapi as hass
import globals
import messages
import shutil
import os
import time
import datetime
#
# App which runs facebox face detection and notifies the user with the result
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
# user_id: The user_id of the telegram user to ask whether he knows an unknown face
#
# Release Notes
#
# Version 1.1:
#   Take Snapshot before sending WoL
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
        self.user_id = globals.get_arg(self.args,"user_id")

        self.facebox_source_directory = globals.get_arg(self.args,"facebox_source_directory")
        if not self.facebox_source_directory.endswith("/"):
            self.facebox_source_directory = self.facebox_source_directory + "/"
        self.facebox_unknown_directory = globals.get_arg(self.args,"facebox_unknown_directory") 
        if not self.facebox_unknown_directory.endswith("/"):
            self.facebox_unknown_directory = self.facebox_unknown_directory + "/"
        self.facebox_noface_directory = globals.get_arg(self.args,"facebox_noface_directory") 
        if not self.facebox_noface_directory.endswith("/"):
            self.facebox_noface_directory = self.facebox_noface_directory + "/"

        self.waitBeforeSnapshot = 1.5
            

        # Subscribe to sensors
        self.listen_event_handle_list.append(self.listen_event(self.button_clicked, "click"))
        self.listen_state_handle_list.append(self.listen_state(self.triggered,self.sensor))

        self.listen_event_handle_list.append(self.listen_event(self.receive_telegram_callback, 'telegram_callback'))

    def button_clicked(self, event_name, data, kwargs):
        """Extra callback method to trigger the face detection on demand by pressing a Xiaomi Button"""
        if data["entity_id"] == self.button:
            if data["click_type"] == "single":
                self.timer_handle_list.append(self.run_in(self.takeSnapshot,self.waitBeforeSnapshot))

    def triggered(self, entity, attribute, old, new, kwargs):
        """State Callback to start the face detection process"""
        if new == "on":
            self.timer_handle_list.append(self.run_in(self.takeSnapshot,self.waitBeforeSnapshot))

    def sendWakeOnLan(self, kwargs):
        """Send a Wake on Lan package to the Facebox Server"""
        self.log("Sending WoL")
        self.turn_on(self.wol_switch)
        self.timer_handle_list.append(self.run_in(self.takeSnapshot,1.5))

    def takeSnapshot(self, kwargs):
        """Take a snapshot. Save to a file."""
        self.log("Calling camera/snapshot")
        self.call_service("camera/snapshot", entity_id = self.camera, filename = self.filename)
        self.timer_handle_list.append(self.run_in(self.sendWakeOnLan,0))

    def triggerImageProcessing(self, kwargs):
        """Trigger Facebox image processing (on the saved file)"""
        self.log("Calling image_processing/scan")
        self.call_service("image_processing/scan", entity_id = self.image_processing)
        self.timer_handle_list.append(self.run_in(self.processImageProcessingResult,2))

    def processImageProcessingResult(self, kwargs):
        """Process the result of the facebox face detection. Based on the face detected, 
        move the image to a new directory to be used as additional training data.
        """
        image_processing_state = self.get_state(self.image_processing, attribute = "all")
        last_updated = image_processing_state["last_updated"]
        matched_faces = image_processing_state["attributes"]["matched_faces"]
        total_faces = image_processing_state["attributes"]["total_faces"]
        if (datetime.datetime.now(datetime.timezone.utc) - self.convert_utc(last_updated) ) > datetime.timedelta(seconds=4):
            self.log("Imageprocessing is down", level="WARNING")
            self.call_service("notify/" + self.notify_name,message=messages.facebox_not_responding())
            #send file
            self.call_service("TELEGRAM_BOT/SEND_PHOTO", file=self.filename)
            directory = self.facebox_unknown_directory
            self.copyFile(directory, self.filename)
        elif total_faces == 0:
            self.log("No faces were detected.")
            self.call_service("notify/" + self.notify_name,message=messages.noface_detected())
            #send file
            self.call_service("TELEGRAM_BOT/SEND_PHOTO", file=self.filename)
            self.copyFile(self.facebox_noface_directory, self.filename)
        elif total_faces == 1:
            face_identified = False
            for face in self.known_faces:
                if face in matched_faces:
                    face_identified = True
                    self.log(messages.identified_face().format(face))
                    self.call_service("notify/" + self.notify_name,message=messages.identified_face().format(face))
                    #copy file for training
                    directory = self.facebox_source_directory + face
                    self.copyFile(directory, self.filename)
            if not face_identified:
                self.log("Unknown face")
                #send photo
                self.call_service("TELEGRAM_BOT/SEND_PHOTO", file=self.filename)
                #copy file for training
                directory = self.facebox_unknown_directory
                new_filename = self.copyFile(directory, self.filename)
                self.ask_for_name(new_filename)
        elif total_faces > 1:
            for face in self.known_faces:
                if face in matched_faces:
                    self.log(messages.identified_face().format(face))
                    self.call_service("notify/" + self.notify_name,message=messages.identified_face().format(face))
            if total_faces != len(matched_faces):
                self.log("Unknown face")
                self.call_service("notify/" + self.notify_name,message=messages.unknown_face_detected())
                #send photo
                self.call_service("TELEGRAM_BOT/SEND_PHOTO", file=self.filename)
                

    def ask_for_name(self, filename):
        """Asks the user if he knows the face in the photo.
        The filename is needed to link the user reply back to this message"""
        keyboard = [("Unbekannt","/unkown" + filename)]
        for face in self.known_faces:
            keyboard.append((face,"/" + face + filename))
        self.call_service('telegram_bot/send_message',
                          target=self.user_id,
                          message=messages.unknown_face_detected(),
                          inline_keyboard=keyboard)

    def copyFile(self, directory, old_filename):
        """Copies a file from an old absolute path to a new directory and names it after the current timestamp appended by '.jpg'"""
        if not os.path.exists(directory):
            os.makedirs(directory)
        filename =  directory + time.strftime("%Y%m%d%H%M%S.jpg")
        self.log("Copy file from {} to {}".format(old_filename, filename))
        shutil.copyfile(old_filename, filename)
        return filename

    def receive_telegram_callback(self, event_name, data, kwargs):
        """Event listener for Telegram callback queries."""
        assert event_name == 'telegram_callback'
        data_callback = data['data']
        callback_id = data['id']
        chat_id = data['chat_id']
        self.log("callback data: {}".format(data))

        for face in self.known_faces:
            if data_callback.startswith("/" + face):
                self.call_service('telegram_bot/answer_callback_query',
                              message="Dankeschön!",
                              callback_query_id=callback_id)
                directory = self.facebox_source_directory + face
                old_file_path = self.facebox_unknown_directory + data_callback.split("/" + face,1)[1]
                self.copyFile(directory, old_file_path)      

        if data_callback.startswith('/unkown'):  # Keyboard editor:
            # Answer callback query
            self.call_service('telegram_bot/answer_callback_query',
                              message="Dankeschön!",
                              callback_query_id=callback_id)

        
    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)