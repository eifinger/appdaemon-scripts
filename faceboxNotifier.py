import appdaemon.plugins.hass.hassapi as hass
import globals
import messages
import shutil
import os
import time
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

        self.facebox_source_directory = globals.get_arg(self.args,"facebox_source_directory")
        if not self.facebox_source_directory.endswith("/"):
            self.facebox_source_directory = self.facebox_source_directory + "/"
        self.facebox_unknown_directory = globals.get_arg(self.args,"facebox_unknown_directory") 
        if not self.facebox_unknown_directory.endswith("/"):
            self.facebox_unknown_directory = self.facebox_unknown_directory + "/"
        self.facebox_noface_directory = globals.get_arg(self.args,"facebox_noface_directory") 
        if not self.facebox_noface_directory.endswith("/"):
            self.facebox_noface_directory = self.facebox_noface_directory + "/"
            

        # Subscribe to sensors
        self.listen_event_handle_list.append(self.listen_event(self.button_clicked, "click"))
        self.listen_state_handle_list.append(self.listen_state(self.triggered,self.sensor))

        self.listen_event_handle_list.append(self.listen_event(self.receive_telegram_text, 'telegram_text'))
        self.listen_event_handle_list.append(self.listen_event(self.receive_telegram_callback, 'telegram_callback'))

    def button_clicked(self, event_name, data, kwargs):
        """Extra callback method to trigger the face detection on demand by pressing a Xiaomi Button"""
        if data["entity_id"] == self.button:
            if data["click_type"] == "single":
                self.timer_handle_list.append(self.run_in(self.sendWakeOnLan,1.5))

    def triggered(self, entity, attribute, old, new, kwargs):
        """State Callback to start the face detection process"""
        if new == "on":
            self.timer_handle_list.append(self.run_in(self.sendWakeOnLan,1.5))

    def sendWakeOnLan(self, kwargs):
        """Send a Wake on Lan package to the Facebox Server"""
        self.log("Sending WoL")
        self.turn_on(self.wol_switch)
        self.timer_handle_list.append(self.run_in(self.takeSnapshot,1.5))

    def takeSnapshot(self, kwargs):
        """Take a snapshot. Save to a file."""
        self.log("Calling camera/snapshot")
        self.call_service("camera/snapshot", entity_id = self.camera, filename = self.filename)
        self.timer_handle_list.append(self.run_in(self.triggerImageProcessing,2))

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
        matched_faces = image_processing_state["attributes"]["matched_faces"]
        total_faces = image_processing_state["attributes"]["total_faces"]
        if total_faces == 0:
            self.log("No faces were detected.")
            self.call_service("notify/" + self.notify_name,message=messages.noface_detected())
            #send file
            self.call_service("TELEGRAM_BOT/SEND_PHOTO", file=self.filename)
            if not os.path.exists(self.facebox_noface_directory):
                os.makedirs(self.facebox_noface_directory)
            filename =  self.facebox_noface_directory + "/" + time.strftime("%Y%m%d%H%M%S.jpg")
            self.log("Copy file from {} to {}".format(self.filename, filename))
            shutil.copyfile(self.filename, filename)
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
                #send file
                self.call_service("TELEGRAM_BOT/SEND_PHOTO", file=self.filename)
                #copy file for training
                directory = self.facebox_unknown_directory
                if not os.path.exists(directory):
                    os.makedirs(directory)
                filename =  directory + time.strftime("%Y%m%d%H%M%S.jpg")
                self.log("Copy file from {} to {}".format(self.filename, filename))
                shutil.copyfile(self.filename, filename)

    def receive_telegram_text(self, event_name, data, kwargs):
        """Text repeater."""
        assert event_name == 'telegram_text'
        user_id = data['user_id']
        msg = 'You said: ``` %s ```' % data['text']
        keyboard = [[("Edit message", "/edit_msg"),
                     ("Don't", "/do_nothing")],
                    [("Remove this button", "/remove button")]]
        self.call_service('telegram_bot/send_message',
                          title='*Dumb automation*',
                          target=user_id,
                          message=msg,
                          disable_notification=True,
                          inline_keyboard=keyboard)

    def receive_telegram_callback(self, event_name, data, kwargs):
        """Event listener for Telegram callback queries."""
        assert event_name == 'telegram_callback'
        data_callback = data['data']
        callback_id = data['id']
        chat_id = data['chat_id']
        # keyboard = ["Edit message:/edit_msg, Don't:/do_nothing",
        #             "Remove this button:/remove button"]
        keyboard = [[("Edit message", "/edit_msg"),
                     ("Don't", "/do_nothing")],
                    [("Remove this button", "/remove button")]]

        if data_callback == '/edit_msg':  # Message editor:
            # Answer callback query
            self.call_service('telegram_bot/answer_callback_query',
                              message='Editing the message!',
                              callback_query_id=callback_id,
                              show_alert=True)

            # Edit the message origin of the callback query
            msg_id = data['message']['message_id']
            user = data['from_first']
            title = '*Message edit*'
            msg = 'Callback received from %s. Message id: %s. Data: ``` %s ```'
            self.call_service('telegram_bot/edit_message',
                              chat_id=chat_id,
                              message_id=msg_id,
                              title=title,
                              message=msg % (user, msg_id, data_callback),
                              inline_keyboard=keyboard)

        elif data_callback == '/remove button':  # Keyboard editor:
            # Answer callback query
            self.call_service('telegram_bot/answer_callback_query',
                              message='Callback received for editing the '
                                      'inline keyboard!',
                              callback_query_id=callback_id)

            # Edit the keyboard
            new_keyboard = keyboard[:1]
            self.call_service('telegram_bot/edit_replymarkup',
                              chat_id=chat_id,
                              message_id='last',
                              inline_keyboard=new_keyboard)

        elif data_callback == '/do_nothing':  # Only Answer to callback query
            self.call_service('telegram_bot/answer_callback_query',
                              message='OK, you said no!',
                              callback_query_id=callback_id)

        
    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)