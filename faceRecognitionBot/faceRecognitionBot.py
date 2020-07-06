import json
from json import JSONDecodeError

import appdaemon.plugins.hass.hassapi as hass  # pylint: disable=import-error
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
# notify_name: Who to notify. example: group_notifications
# wol_switch: Wake on Lan switch which turns on the facebox server. example: switch.facebox_wol
# user_id: The user_id of the telegram user to ask whether he knows an unknown face
# number_of_images: Number of images to take. example: 10
# waitBeforeSnapshot: How many seconds to wait before triggering the inital snapshot. example: 2.5
# message_face_identified: Message to send if a face got identified.
# message_unkown_face: Message to send if a face is unknown
# message_provide_name
# message_name_provided
# message_name_provided_callback
# ip: Ip of facerec_service. example: 192.168.0.1
# port: port of facerec_service. example: 8080
#
# Release Notes
#
# Version 1.3.beta:
#   Fully working
#
# Version 1.2:
#   Rework to FaceRecognitionBot
#
# Version 1.1:
#   Take Snapshot before sending WoL
#
# Version 1.0:
#   Initial Version
CLASSIFIER = "faces"
TIMEOUT = 20
PROVIDE_NAME_TIMEOUT = 5
IDENTIFIER_DELIMITER = "_"
FILENAME_DELIMITER = "-"
MAXIMUM_DISTANCE = 0.40
UNKNOWN_FACE_NAME = "unkown"


class FaceRecognitionBot(hass.Hass):
    def initialize(self):

        # handle lists
        self.timer_handle_list = []
        self.listen_event_handle_list = []
        self.listen_state_handle_list = []

        # args
        self.app_switch = self.args["app_switch"]
        self.sensor = self.args["sensor"]
        self.button = self.args["button"]
        self.camera = self.args["camera"]
        self.local_file_camera = self.args["local_file_camera"]
        self.filename = self.args["filename"]
        self.notify_name = self.args["notify_name"]
        self.wol_switch = self.args["wol_switch"]
        self.user_id = self.args["user_id"]
        self.number_of_images = self.args["number_of_images"]
        self.waitBeforeSnapshot = self.args["waitBeforeSnapshot"]
        self.message_face_identified = self.args["message_face_identified"]
        self.message_unkown_face = self.args["message_unkown_face"]
        self.message_unkown_face_with_known = self.args[
            "message_unkown_face_with_known"
        ]
        self.message_provide_name = self.args["message_provide_name"]
        self.message_name_provided = self.args["message_name_provided"]
        self.message_name_provided_callback = self.args[
            "message_name_provided_callback"
        ]
        self.facebox_healthcheck_filename = self.args["facebox_healthcheck_filename"]
        self.healthcheck_face_name = self.args["healthcheck_face_name"]
        self.ip = self.args["ip"]
        self.port = self.args["port"]

        # optional args
        self.facebox_source_directory = self.args["facebox_source_directory"]
        if not self.facebox_source_directory.endswith("/"):
            self.facebox_source_directory = self.facebox_source_directory + "/"
        self.facebox_unknown_directory = self.args["facebox_unknown_directory"]
        if not self.facebox_unknown_directory.endswith("/"):
            self.facebox_unknown_directory = self.facebox_unknown_directory + "/"
        self.facebox_noface_directory = self.args["facebox_noface_directory"]
        if not self.facebox_noface_directory.endswith("/"):
            self.facebox_noface_directory = self.facebox_noface_directory + "/"
        self.facebox_known_faces_directory = self.args["facebox_known_faces_directory"]
        if not self.facebox_known_faces_directory.endswith("/"):
            self.facebox_known_faces_directory = (
                self.facebox_known_faces_directory + "/"
            )

        # App dependencies
        self.notifier = self.get_app("Notifier")

        # Subscribe to sensors
        self.listen_state_handle_list.append(
            self.listen_state(self.triggered, self.sensor)
        )
        # Subscribe to custom triggers
        self.listen_event_handle_list.append(
            self.listen_event(self.button_clicked, "xiaomi_aqara.click")
        )
        self.listen_event_handle_list.append(
            self.listen_event(self.learn_faces_event_callback, "eifinger_learn_faces")
        )
        # subscribe to telegram events
        self.listen_event_handle_list.append(
            self.listen_event(self.receive_telegram_callback, "telegram_callback")
        )
        self.listen_event_handle_list.append(
            self.listen_event(self.receive_telegram_text, "telegram_text")
        )
        # Teach periodic run
        # self.timer_handle_list.append(self.run_in(self.check_health_callback, 5))

        # custom variables

        self.valid_filetypes = (".jpg", ".png", ".jpeg")

        self.teach_url = "http://{}:{}/faces".format(self.ip, self.port)
        self.health_url = "http://{}:{}/faces".format(self.ip, self.port)
        self.check_url = "http://{}:{}".format(self.ip, self.port)

        self.run_in_initial_delay = 43200
        self.run_in_delay = self.run_in_initial_delay
        self.run_in_error_delay = 60

        self.exclude_folders = (
            "healthcheck",
            "multiple",
            "noface",
            "tmp",
            "unknown",
            "new",
        )

        self.provide_name_timeout_start = None
        self.last_identifier = None
        self.last_message_id = None
        self.last_from_first = None

    ###############################################################
    # Teacher
    ###############################################################
    def check_health_callback(self, kwargs):
        """Check health.
        
        Runs repeatedly until it is veryfied that the classifier is healthy and faces are trained.
        
        If it is healthy and trained it will check again after run_in_initial_delay"""
        try:
            if self.check_classifier_health():
                self.check_if_trained(None)
                self.timer_handle_list.append(
                    self.run_in(self.check_health_callback, self.run_in_delay)
                )
        except requests.exceptions.HTTPError as exception:
            self.log(
                "Error trying to turn on entity. Will try again in 1s. Error: {}".format(
                    exception
                ),
                level="WARNING",
            )
            self.timer_handle_list.append(self.run_in(self.check_health_callback, 1))

    def learn_faces_event_callback(self, event_name, data, kwargs):
        """Callback function for manual trigger of face learning"""
        self.log("Event received. Triggering Face Learning")
        self.teach_faces(self.facebox_known_faces_directory, self.exclude_folders)

    def teach_name_by_file(self, teach_url, name, file_path):
        """Teach the classifier a single name using a single file."""
        file_name = file_path.split("/")[-1]
        file = {"file": open(file_path, "rb")}

        teach_url = teach_url + "?id=" + name
        response = requests.post(teach_url, files=file)

        if response.status_code == 200:
            self.log("File: {} taught with name: {}".format(file_name, name))
            return True

        elif response.status_code == 400:
            self.log(
                "Teaching of file: {} failed with message: {}".format(
                    file_name, response.text
                )
            )
            return False

    def check_classifier_health(self):
        """Check if classifier is reachable under health_url and returns HTTP 200"""
        try:
            response = requests.get(self.health_url)
            if response.status_code == 200:
                self.log("Health-check passed")
                self.run_in_delay = self.run_in_initial_delay
                self.log("Setting run_in_delay to {}".format(self.run_in_delay))
                return True
            else:
                self.log("Health-check failed")
                self.log(response.status_code)
                # check for recurring error
                if self.run_in_delay < self.run_in_initial_delay:
                    self.run_in_delay = self.run_in_delay * 2
                else:
                    self.run_in_delay = self.run_in_error_delay
                return False
        except requests.exceptions.RequestException as exception:
            self.log("Server is unreachable", level="WARNING")
            self.log(exception, level="WARNING")
            # check for recurring error
            if self.run_in_delay < self.run_in_initial_delay:
                self.run_in_delay = self.run_in_delay * 2
            else:
                self.run_in_delay = self.run_in_error_delay
            self.log("Setting run_in_delay to {}".format(self.run_in_delay))

    def check_if_trained(self, kwargs):
        """Check if faces are trained. If not train them.
        
        Checks for a picture with a known result if the classifier returns the correct result
        """
        response = self.post_image(self.check_url, self.facebox_healthcheck_filename)
        if (
            response
            and response.status_code == 200
            and len(response.json()["faces"]) > 0
            and response.json()["faces"][0]["id"] == self.healthcheck_face_name
        ):
            self.log("Faces are still taught")
        else:
            self.log("Faces are not taught")
            self.teach_faces(self.facebox_known_faces_directory, self.exclude_folders)

    def teach_faces(self, folderpath, exclude_folders=[]):
        """Teach faces.

        Will iterate over all subdirectories of 'folderpath' and teach the name within
        that subdirectory with the name of the subdirectory"""
        self.log("Teaching faces")
        for folder_name in self.list_folders(folderpath):
            if not folder_name in exclude_folders:
                folder_path = os.path.join(folderpath, folder_name)
                for file in os.listdir(folder_path):
                    if file.endswith(self.valid_filetypes):
                        file_path = os.path.join(folder_path, file)
                        self.teach_name_by_file(self.teach_url, folder_name, file_path)

    def teach_name_by_directory(self, name, folderpath):
        """Teach faces in a directory for a given anme"""
        self.log("Teaching faces in dir: {}".format(folderpath))
        for file in os.listdir(folderpath):
            if file.endswith(self.valid_filetypes):
                file_path = os.path.join(folderpath, file)
                self.teach_name_by_file(self.teach_url, name, file_path)

    ###############################################################
    # Classifier
    ###############################################################
    def button_clicked(self, event_name, data, kwargs):
        """Extra callback method to trigger the face detection on demand by pressing a Xiaomi Button"""
        if data["entity_id"] == self.button:
            if data["click_type"] == "single":
                self.timer_handle_list.append(
                    self.run_in(self.takeSnapshots, self.waitBeforeSnapshot)
                )

    def triggered(self, entity, attribute, old, new, kwargs):
        """State Callback to start the face detection process"""
        if self.get_state(self.app_switch) == "on":
            if new == "on":
                self.timer_handle_list.append(
                    self.run_in(self.takeSnapshots, self.waitBeforeSnapshot)
                )

    def takeSnapshots(self, kwargs):
        """Take a snapshot. Save to a file."""
        file_locations = []
        timestamp = time.strftime("%Y%m%d%H%M%S")
        directory = self.facebox_source_directory + "new/" + timestamp
        if not os.path.exists(directory):
            os.makedirs(directory)
        for i in range(0, self.number_of_images):
            filename = (
                directory + "/" + timestamp + FILENAME_DELIMITER + str(i) + ".jpg"
            )
            self.log("Calling camera/snapshot and saving it to: {}".format(filename))
            self.call_service(
                "camera/snapshot", entity_id=self.camera, filename=filename
            )
            file_locations.append(filename)
        self.timer_handle_list.append(
            self.run_in(self.processImages, 0, file_locations=file_locations)
        )

    def processImages(self, kwargs):
        """Trigger image processing for all images and process the results
        
         Get the classifier result for each image
         store it in a dictionary in the following format
         {filename:
                  {"count":int,
                   "faces":{
                             [
                               {"dist":float,
                                "id":name}
                             ]
                            },
                   "matchedFacesCount":int}
         }
        """
        result_dict_dict = {}
        for filename in kwargs["file_locations"]:
            response = self.post_image(self.check_url, filename)
            if response is not None:
                result_dict = {}
                self.log("response is: {}".format(response.text))
                try:
                    response_json = response.json()
                    result_dict["count"] = response_json["count"]
                    result_dict["faces"] = response_json["faces"]
                    result_dict["matchedFacesCount"] = len(response_json["faces"])
                    result_dict_dict[filename] = result_dict
                except JSONDecodeError:
                    self.log("JSONDecodeError. Skipping response")
        # get the maximum number of faces detected in one image
        maxCount = self._getMaxCountFromResult(result_dict_dict)
        # get a list of distinct recognized face names
        faceNames = self._getFaceNamesFromResult(result_dict_dict)
        self.log("Number of distinct faces: {}".format(len(faceNames)))
        if maxCount > 1:
            self.log("At least one time detected more than one face")
            # check if it contains an unknown face
            if UNKNOWN_FACE_NAME in faceNames:
                self._notifyUnkownFaceFound(result_dict_dict)
            else:
                for faceName in faceNames:
                    if faceName in self._getKnownFaces():
                        self.log(self.message_face_identified.format(faceName))
                        self.notifier.notify(
                            self.notify_name,
                            self.message_face_identified.format(faceName),
                        )
                        # copy file to saved image to display in HA
                        shutil.copy(filename, self.filename)
        elif maxCount == 1:
            self.log("Always detected one face")
            # check if always the same face
            if len(faceNames) > 1:
                self.log("Not always the same face")
                # TODO test!
                # at least one time detected a known face
                # notify of who was detected
                for faceName in faceNames:
                    if faceName in self._getKnownFaces():
                        self.log(self.message_face_identified.format(faceName))
                        self.notifier.notify(
                            self.notify_name,
                            self.message_face_identified.format(faceName),
                        )
                        # copy file to saved image to display in HA
                        shutil.copy(filename, self.filename)
                # process the unknown faces
                if UNKNOWN_FACE_NAME in faceNames:
                    self._processUnkownFaceFound(result_dict_dict)
            else:
                self.log("Always the same face")
                # Is it a known face?
                if len(faceNames) > 0 and faceNames[0] in self._getKnownFaces():
                    # always identified the same known person
                    self.log(self.message_face_identified.format(faceNames[0]))
                    self.notifier.notify(
                        self.notify_name,
                        self.message_face_identified.format(faceNames[0]),
                    )
                    # Move files to known face subdirectory
                    for filename in result_dict_dict:
                        # at this time we know it is at most 1 and it is always the same known face
                        if result_dict_dict[filename]["count"] == 1:
                            directory = (
                                self.facebox_known_faces_directory
                                + result_dict_dict[filename]["faces"][0]["id"]
                            )
                            new_filename = os.path.join(
                                directory, os.path.split(filename)[1]
                            )
                            # copy file to saved image to display in HA
                            shutil.copy(filename, self.filename)
                            self.log(
                                "Move file from {} to {}".format(filename, new_filename)
                            )
                            shutil.move(filename, new_filename)
                            # trigger teaching
                            self.teach_name_by_file(
                                self.teach_url,
                                result_dict_dict[filename]["faces"][0]["id"],
                                new_filename,
                            )
                else:
                    # unknown face
                    self._processUnkownFaceFound(result_dict_dict)
        else:
            self.log("Detected no faces")
            # get directory of images and post that in telegram

    def _processUnkownFaceFound(self, result_dict_dict):
        """Store the faces for later use and ask the user if he knows the unkown face"""
        # TODO check if the faces are similar
        # create a temp identifier, compare and delete identifier again
        # self._determineIfSameUnkownFace(result_dict_dict)
        # get a file where the unknown face was detected and send it
        filename = self._getFileWithUnknownFaceFromResult(result_dict_dict)
        # copy file to saved image to display in HA
        shutil.copy(filename, self.filename)
        # send photo
        self.log(f"Sending photo with filename: {filename}")
        self.call_service("telegram_bot/send_photo", file=filename, target=self.notify_name)
        # copy all files where a face was detected to the unkown folder
        identifier = self._copyFilesToUnknown(result_dict_dict)
        if identifier == "":
            self.log("Identifier is empty", level="ERROR")
        else:
            self.ask_for_name(identifier)

    def _notifyUnkownFaceFound(self, result_dict_dict):
        """Notify of an unkown face in a image where a known face was detected"""
        # get a file where the unknown face was detected and send it
        filename = self._getFileWithUnknownFaceFromResult(result_dict_dict)
        # copy file to saved image to display in HA
        shutil.copy(filename, self.filename)
        # send photo
        self.call_service("telegram_bot/send_photo", file=filename, target=self.notify_name)
        self.log(self.message_unkown_face_with_known)
        self.notifier.notify(self.notify_name, self.message_unkown_face_with_known)

    def _getMaxCountFromResult(self, result_dict_dict):
        """Get the maximum number of faces found in the pictures"""
        count_list = [d["count"] for d in result_dict_dict.values()]
        return max(count_list)

    def _getFaceNamesFromResult(self, result_dict_dict):
        """Return a list of names for the identified faces"""
        try:
            id_list = []
            for d in result_dict_dict.values():
                # check for unknown face
                if len(d["faces"]) == 0 and d["count"] == 1:
                    id_list.append(UNKNOWN_FACE_NAME)
                else:
                    for face in d["faces"]:
                        if face["dist"] < MAXIMUM_DISTANCE:
                            id_list.append(face["id"])
                        # if distance(similarity) too large, mark as unknown
                        else:
                            self.log(
                                "Similary distance of {} is larger than maximum threshold of {}".format(
                                    face["dist"], MAXIMUM_DISTANCE
                                )
                            )
                            id_list.append(UNKNOWN_FACE_NAME)
                            face["id"] = UNKNOWN_FACE_NAME
            self.log("FacesNames: {}".format(list(set(id_list))))
            return list(set(id_list))
        except TypeError:
            return []

    def _getFileWithUnknownFaceFromResult(self, result_dict_dict):
        """Get the first file from the result which has an unmatched face"""
        for filename in result_dict_dict.keys():
            if (
                result_dict_dict[filename]["count"] > 0
                and result_dict_dict[filename]["faces"][0]["id"] == UNKNOWN_FACE_NAME
            ):
                return filename

    def _determineIfSameUnkownFace(self, result_dict_dict):
        """Determine if the unkown face which was detected several times is the same unknown face"""
        # get all files with unknown faces
        unkown_faces = []
        for filename in result_dict_dict.keys():
            if (
                result_dict_dict[filename]["count"] == 1
                and result_dict_dict[filename]["faces"][0]["id"] == UNKNOWN_FACE_NAME
            ):
                unkown_faces.append(filename)
        # iterate over all files
        for k, filename in enumerate(unkown_faces):
            for i, filename in enumerate(unkown_faces):
                if i < k:
                    pass
                elif i == k:
                    # teach the first face
                    filename_without_path = os.path.split(filename)[1]
                    self.teach_name_by_file(
                        self.teach_url, filename_without_path, filename
                    )
                else:
                    response = self.post_image(self.check_url, filename)
                    response_json = response.json()
                    if response_json["count"] > 0:
                        if (
                            response_json["faces"][0]["id"] == filename_without_path
                            and response_json["faces"][0]["dist"] < MAXIMUM_DISTANCE
                        ):
                            # same face remove it from the list
                            unkown_faces.remove(filename)

    def _copyFilesToUnknown(self, result_dict_dict):
        """Copy all files where the unknown face was detected to the unknown folder.
        Returns the timestamp under which all files can be identified"""
        identifier = ""
        for filename in result_dict_dict.keys():
            if result_dict_dict[filename]["count"] > 0 and (
                len(result_dict_dict[filename]["faces"]) == 0
                or result_dict_dict[filename]["faces"][0]["id"] == UNKNOWN_FACE_NAME
            ):
                filename_without_path = os.path.split(filename)[1]
                # get the timestamp as identifier, strip everything after "-""
                identifier = filename_without_path.split(FILENAME_DELIMITER)[0]
                self.log("Identifier is: {}".format(identifier), level="DEBUG")
                new_filename = self.facebox_unknown_directory + filename_without_path
                self.log("Move file from {} to {}".format(filename, new_filename))
                shutil.move(filename, new_filename)
        return identifier

    def _copyFilesFromUnkownToDirectoryByIdentifier(self, directory, identifier):
        """Copy all files in the unknown folder which belong to an identifier (a timestamp) to a new directory"""
        if not os.path.exists(directory):
            os.makedirs(directory)
        for file in os.listdir(self.facebox_unknown_directory):
            if identifier in file:
                filename = os.path.join(self.facebox_unknown_directory, file)
                new_filename = os.path.join(directory, file)
                self.log("Move file from {} to {}".format(filename, new_filename))
                shutil.move(filename, new_filename)

    def _getKnownFaces(self):
        """Return a list of known face names.

        Iterates over the subdirectory names of facebox_known_faces_directory"""
        return self.list_folders(self.facebox_known_faces_directory)

    def list_folders(self, directory):
        """Returns a list of folders
        These are not full paths, just the folder."""
        folders = [
            dir
            for dir in os.listdir(directory)
            if os.path.isdir(os.path.join(directory, dir))
            and not dir.startswith(directory)
            and not dir.startswith(".")
        ]
        folders.sort(key=str.lower)
        return folders

    def post_image(self, url, image):
        """Post an image to the classifier."""
        try:
            response = requests.post(
                url, files={"file": open(image, "rb")}, timeout=TIMEOUT
            )
            return response
        except requests.exceptions.ConnectionError:
            self.log("ConnectionError")
        except requests.exceptions.ReadTimeout:
            self.log("ReadTimeout")

    ###############################################################
    # Telegram Bot
    ###############################################################

    def ask_for_name(self, identifier):
        """Asks the user if he knows the face in the photo.
        The identifier is needed to link the user reply back to this message"""
        self.log("Asking for name")
        keyboard = [[("Unbekannt", "/unkown" + IDENTIFIER_DELIMITER + identifier)]]
        for face in self._getKnownFaces():
            keyboard.append([(face, "/" + face + IDENTIFIER_DELIMITER + identifier)])
        self.log("keyboard is: {}".format(keyboard), level="DEBUG")
        self.call_service(
            "telegram_bot/send_message",
            target=self.user_id,
            message=self.message_unkown_face,
            inline_keyboard=keyboard,
        )

    def receive_telegram_callback(self, event_name, data, kwargs):
        """Event listener for Telegram callback queries."""
        self.log("callback data: {}".format(data))
        data_callback = data["data"]
        callback_id = data["id"]
        chat_id = data["chat_id"]
        message_id = data["message"]["message_id"]
        text = data["message"]["text"]
        from_first = data["from_first"]

        for face in self._getKnownFaces():
            if data_callback.startswith("/" + face + IDENTIFIER_DELIMITER):
                self.log("Received Telegram Callback for {}".format(face))
                self.call_service(
                    "telegram_bot/answer_callback_query",
                    message="Dankeschön!",
                    callback_query_id=callback_id,
                )
                self.call_service(
                    "telegram_bot/edit_message",
                    chat_id=chat_id,
                    message_id=message_id,
                    message=self.message_name_provided_callback.format(
                        from_first, face
                    ),
                    inline_keyboard=[],
                )
                identifier = data_callback.split(IDENTIFIER_DELIMITER)[1]
                directory = self.facebox_known_faces_directory + face
                self._copyFilesFromUnkownToDirectoryByIdentifier(directory, identifier)
                self.teach_name_by_directory(face, directory)

        if data_callback.startswith("/unkown"):
            # Answer callback query
            self.call_service(
                "telegram_bot/answer_callback_query",
                message="Dankeschön!",
                callback_query_id=callback_id,
            )
            self.call_service(
                "telegram_bot/edit_message",
                chat_id=chat_id,
                message_id=message_id,
                message=text,
                inline_keyboard=[],
            )
            self.notifier.notify(
                self.notify_name,
                self.message_provide_name.format(PROVIDE_NAME_TIMEOUT),
                useAlexa=False,
            )
            self.provide_name_timeout_start = datetime.datetime.now()
            self.last_identifier = data_callback.split(IDENTIFIER_DELIMITER)[1]
            self.last_message_id = message_id
            self.last_from_first = from_first

    def receive_telegram_text(self, event_name, data, kwargs):
        """Telegram text listener"""
        self.log("callback data: {}".format(data), level="DEBUG")
        chat_id = data["chat_id"]
        text = data["text"]

        if self.provide_name_timeout_start != None and (
            datetime.datetime.now() - self.provide_name_timeout_start
            < datetime.timedelta(minutes=PROVIDE_NAME_TIMEOUT)
        ):
            # Edit the last ask_for_name message
            self.call_service(
                "telegram_bot/edit_message",
                chat_id=chat_id,
                message_id=self.last_message_id,
                message=self.message_name_provided_callback.format(
                    self.last_from_first, text
                ),
                inline_keyboard=[],
            )
            # Say thanks
            self.notifier.notify(
                self.notify_name,
                self.message_name_provided.format(text),
                useAlexa=False,
            )
            # Copy files to new directory
            directory = self.facebox_known_faces_directory + text
            self._copyFilesFromUnkownToDirectoryByIdentifier(
                directory, self.last_identifier
            )
            self.teach_name_by_directory(text, directory)
        else:
            self.log("PROVIDE_NAME_TIMEOUT exceeded")

    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
