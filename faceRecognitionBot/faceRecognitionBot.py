import appdaemon.plugins.hass.hassapi as hass
import globals
import messages
import shutil
import os
import time
import datetime
import requests
#
# App which runs face detection and notifies the user with the result
#
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
# sensor: binary sensor to use as trigger
# button: xiaomi button to use as a trigger
# camera : camera entity. example: camera.ip_webcam
# local_file_camera: local file camera entity. example: camera.saved_image
# known_faces: comma separated names of known faces. example: Tina,Markus
# notify_name: Who to notify. example: group_notifications
# wol_switch: Wake on Lan switch which turns on the facebox server. example: switch.facebox_wol
# user_id: The user_id of the telegram user to ask whether he knows an unknown face
# number_of_images: Number of images to take. example: 10
# waitBeforeSnapshot: How many seconds to wait before triggering the inital snapshot. example: 2.5
# message_face_identified: Message to send if a face got identified.
# message_unkown_face: Message to send if a face is unknown
# message_provide_name
# message_name_provided
# ip: Ip of facerec_service. example: 192.168.0.1
# port: port of facerec_service. example: 8080
#
# Release Notes
#
# Version 1.2:
#   Rework to FaceRecognitionBot
#
# Version 1.1:
#   Take Snapshot before sending WoL
#
# Version 1.0:
#   Initial Version

ATTR_BOUNDING_BOX = 'bounding_box'
ATTR_CLASSIFIER = 'classifier'
ATTR_IMAGE_ID = 'image_id'
ATTR_MATCHED = 'matched'
CLASSIFIER = 'faces'
DATA_FACEBOX = 'facebox_classifiers'
TIMEOUT = 2
PROVIDE_NAME_TIMEOUT = 5
IDENTIFIER_DELIMITER = ","

class FaceRecognitionBot(hass.Hass):

    def initialize(self):
    
        self.timer_handle_list = []
        self.listen_event_handle_list = []
        self.listen_state_handle_list = []

        self.app_switch = globals.get_arg(self.args,"app_switch")
        self.sensor = globals.get_arg(self.args,"sensor")
        self.button = globals.get_arg(self.args,"button")
        self.camera = globals.get_arg(self.args,"camera")
        self.local_file_camera = globals.get_arg(self.args,"local_file_camera")
        self.known_faces = globals.get_arg_list(self.args,"known_faces")
        self.notify_name = globals.get_arg(self.args,"notify_name")
        self.wol_switch = globals.get_arg(self.args,"wol_switch")
        self.user_id = globals.get_arg(self.args,"user_id")
        self.number_of_images = globals.get_arg(self.args,"number_of_images")
        self.waitBeforeSnapshot = globals.get_arg(self.args,"waitBeforeSnapshot")
        self.message_face_identified = globals.get_arg(self.args,"message_face_identified")
        self.message_unkown_face = globals.get_arg(self.args,"message_unkown_face")
        self.message_provide_name = globals.get_arg(self.args,"message_provide_name")
        self.message_name_provided = globals.get_arg(self.args,"message_name_provided")
        
        self.ip = globals.get_arg(self.args,"ip")
        self.port = globals.get_arg(self.args,"port")
        

        self.facebox_source_directory = globals.get_arg(self.args,"facebox_source_directory")
        if not self.facebox_source_directory.endswith("/"):
            self.facebox_source_directory = self.facebox_source_directory + "/"
        self.facebox_unknown_directory = globals.get_arg(self.args,"facebox_unknown_directory") 
        if not self.facebox_unknown_directory.endswith("/"):
            self.facebox_unknown_directory = self.facebox_unknown_directory + "/"
        self.facebox_noface_directory = globals.get_arg(self.args,"facebox_noface_directory") 
        if not self.facebox_noface_directory.endswith("/"):
            self.facebox_noface_directory = self.facebox_noface_directory + "/"

        self.notifier = self.get_app('Notifier')

        self._url_check = "http://{}:{}/{}".format(self.ip, self.port, CLASSIFIER)
        self.provide_name_timeout_start = None
        self.last_identifier = None

        # Subscribe to sensors
        self.listen_event_handle_list.append(self.listen_event(self.button_clicked, "click"))
        self.listen_state_handle_list.append(self.listen_state(self.triggered,self.sensor))

        self.listen_event_handle_list.append(self.listen_event(self.receive_telegram_callback, 'telegram_callback'))
        self.listen_event_handle_list.append(self.listen_event(self.receive_telegram_text, 'telegram_text'))

    def button_clicked(self, event_name, data, kwargs):
        """Extra callback method to trigger the face detection on demand by pressing a Xiaomi Button"""
        if data["entity_id"] == self.button:
            if data["click_type"] == "single":
                self.timer_handle_list.append(self.run_in(self.takeSnapshots,self.waitBeforeSnapshot))

    def triggered(self, entity, attribute, old, new, kwargs):
        """State Callback to start the face detection process"""
        if self.get_state(self.app_switch) == "on":
            if new == "on":
                self.timer_handle_list.append(self.run_in(self.takeSnapshots,self.waitBeforeSnapshot))

    def takeSnapshots(self, kwargs):
        """Take a snapshot. Save to a file."""
        file_locations = []
        directory = self.facebox_source_directory + time.strftime("%Y%m%d%H%M%S")
        if not os.path.exists(directory):
                os.makedirs(directory)
        for i in range(0,self.number_of_images-1):
            filename = directory + "/" + time.strftime("%Y%m%d%H%M%S") + str(i) + ".jpg"
            self.log("Calling camera/snapshot and saving it to: {}".format(filename))
            self.call_service("camera/snapshot", entity_id = self.camera, filename = filename)
            file_locations.append(filename)
        self.timer_handle_list.append(self.run_in(self.processImages,5, file_locations=file_locations))

    def processImages(self, kwargs):
        """Trigger image processing for all images and process the results"""
        result_dict_dict = {}
        for filename in kwargs["file_locations"]:
            response = self.post_image(self._url_check, filename)
            if response is not None:
                result_dict = {}
                response_json = response.json()
                result_dict["count"] = response_json['count']
                result_dict["faces"] = response_json['faces']
                result_dict["matchedFacesCount"] = len(response_json['faces'])
                result_dict_dict[filename] = result_dict
        maxCount = self._getMaxCountFromResult(result_dict_dict)
        faceNames = self._getFaceNamesFromResult(result_dict_dict)
        if maxCount > 1:
            self.log("At least one time detected more than one face")
            #TODO
        elif maxCount == 1:
            self.log("Always detected one face or none at all")
            #check if always the same face
            if self._getNumberOfDistinctFaces(result_dict_dict) > 1:
                self.log("Not always the same face")
                #TODO
            else:
                self.log("Always the same face")
                if len(faceNames) > 0 and faceNames[0] in self.known_faces:
                    self.log(self.message_face_identified.format(self.name))
                    self.notifier.notify(self.notify_name, self.message_face_identified.format(self.name)) 
                    #TODO copy file for training
                    #directory = self.facebox_source_directory + face
                    #self.copyFile(directory, self.filename)
                else:
                    #get a file where the unknown face was detected and send it
                    filename = self._getFileWithUnknownFaceFromResult(result_dict_dict)
                    self.notifier.notify(self.notify_name, self.message_unkown_face) 
                    #send photo
                    self.call_service("TELEGRAM_BOT/SEND_PHOTO", file=filename)
                    #copy all files where a face was detected to the unkown folder
                    identifier = self._copyFilesToUnknown(result_dict_dict)
                    if identifier == "":
                        self.log("Identifier is empty", level="ERROR")
                    else:
                        self.ask_for_name(identifier)
        else:
            self.log("Detected no faces")
            #get directory of images and post that in telegram

    def _getMaxCountFromResult(self, result_dict_dict):
        """Get the maximum number of faces found in the pictures"""
        count_list = [d["count"] for d in result_dict_dict.values()]
        return max(count_list)

    def _getNumberOfDistinctFaces(self, result_dict_dict):
        """Check how many distinct faces got identified"""
        return len(set([d["faces"]["id"] for d in result_dict_dict.values()]))

    def _getFaceNamesFromResult(self, result_dict_dict):
        """Return a list of names for the identified faces"""
        return list(set([d["faces"]["id"] for d in result_dict_dict.values()]))

    def _getFileWithUnknownFaceFromResult(self, result_dict_dict):
        """Get the first file from the result which has an unmatched face"""
        for filename in result_dict_dict.keys():
            if result_dict_dict[filename]["count"] > 0:
                return filename
    
    def _copyFilesToUnknown(self, result_dict_dict):
        """Copy all files where the face was detected to the unknown folder.
        Returns the timestamp under which all files can be identified"""
        identifier = ""
        for filename in result_dict_dict.keys():
            if result_dict_dict[filename]["count"] > 0:
                filename_without_path = os.path.split(filename)[1]
                identifier = filename_without_path[:len(filename_without_path)-1]
                new_filename = self.facebox_unknown_directory + filename_without_path
                self.log("Copy file from {} to {}".format(filename, new_filename))
                shutil.copyfile(filename, new_filename)
        return identifier
    
    def _copyFilesFromUnkownToDirectoryByIdentifier(self, directory, identifier):
        """Copy all files in the unknown folder which belong to an identifier (a timestamp) to a new directory"""
        if not os.path.exists(directory):
            os.makedirs(directory)
        for file in os.listdir(self.facebox_unknown_directory):
            if file.contains(identifier):
                filename = os.path.join(self.facebox_unknown_directory, file)
                new_filename = os.path.join(directory, file)
                self.log("Copy file from {} to {}".format(filename, new_filename))
                shutil.copyfile(filename, new_filename)

    def post_image(self, url, image):
        """Post an image to the classifier."""
        try:
            response = requests.post(
                url,
                files={"file": open(image, 'rb')},
                timeout=TIMEOUT
                )
            return response
        except requests.exceptions.ConnectionError:
            self.log("ConnectionError")
                

    def ask_for_name(self, identifier):
        """Asks the user if he knows the face in the photo.
        The identifier is needed to link the user reply back to this message"""
        keyboard = [("Unbekannt","/unkown" + IDENTIFIER_DELIMITER + identifier)]
        for face in self.known_faces:
            keyboard.append((face,"/" + face + IDENTIFIER_DELIMITER + identifier))
        self.call_service('telegram_bot/send_message',
                          target=self.user_id,
                          message="",
                          inline_keyboard=keyboard)

    def receive_telegram_callback(self, event_name, data, kwargs):
        """Event listener for Telegram callback queries."""
        self.log("callback data: {}".format(data))
        data_callback = data['data']
        callback_id = data['id']
        chat_id = data['chat_id']
        message_id = data["message"]["message_id"]
        text = data["message"]["text"]

        for face in self.known_faces:
            if data_callback.startswith("/" + IDENTIFIER_DELIMITER + face):
                self.log("Received Telegram Callback for {}".format(face))
                self.call_service('telegram_bot/answer_callback_query',
                              message="Dankeschön!",
                              callback_query_id=callback_id)
                identifier = data_callback.split(IDENTIFIER_DELIMITER)[1]
                directory = self.facebox_source_directory + face
                self._copyFilesFromUnkownToDirectoryByIdentifier(directory, identifier)  

        if data_callback.startswith('/unkown'):  # Keyboard editor:
            # Answer callback query
            self.call_service('telegram_bot/answer_callback_query',
                              message="Dankeschön!",
                              callback_query_id=callback_id)
            self.call_service('telegram_bot/edit_message',
                              chat_id=chat_id,
                              message_id=message_id,
                              message=text,
                              inline_keyboard=[])
        self.notifier.notify(self.notify_name, self.message_provide_name.format(PROVIDE_NAME_TIMEOUT))
        self.provide_name_timeout_start = datetime.datetime.now()
        self.last_identifier = data_callback.split(IDENTIFIER_DELIMITER)[1]

    def receive_telegram_text(self, event_name, data, kwargs):
        """Telegram text listener"""
        self.log("callback data: {}".format(data))
        data_callback = data['data']
        callback_id = data['id']
        chat_id = data['chat_id']
        message_id = data["message"]["message_id"]
        text = data["message"]["text"]

        if self.self.provide_name_timeout_start != None and (datetime.datetime.now() - self.provide_name_timeout_start < datetime.timedelta(minutes=PROVIDE_NAME_TIMEOUT)):
            self.notifier.notify(self.notify_name, self.message_name_provided.format(text))
            directory = self.facebox_source_directory + text
            self._copyFilesFromUnkownToDirectoryByIdentifier(directory,self.last_identifier)
        else:
            self.log("PROVIDE_NAME_TIMEOUT exceeded")

        
    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)