import appdaemon.plugins.hass.hassapi as hass
import globals
import requests
import os

#
# App which runs face detection and notifies the result
#
#
# Args:
#  app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
#  folderpath : Folder containing subfolders with images to train. example: /config/www/facebox
#  facebox_healthcheck_filename: entity_id of the facebox entity to use for health checking. It holds the local_file image camera of one kown face. example: image_processing.facebox_health_check_picture
#  healthcheck_face_name: name of the face. example: Viktor
#  ip: the ip of facerec_service. example: localhost
#  port: the port of facerec_service. example: 8080
#  
#
# Release Notes
#
# Version 1.1:
#   Reworked to FaceRecognitionTeacher
#
# Version 1.0:
#   Initial Version
class FaceRecognitionTeacher(hass.Hass):

    def initialize(self):
    
        self.timer_handle_list = []
        self.listen_event_handle_list = []
        self.listen_state_handle_list = []

        self.app_switch = globals.get_arg(self.args,"app_switch")
        self.folderpath = globals.get_arg(self.args,"folderpath")
        self.facebox_healthcheck_filename = globals.get_arg(self.args,"facebox_healthcheck_filename")
        self.healthcheck_face_name = globals.get_arg(self.args, "healthcheck_face_name")

        self.ip = globals.get_arg(self.args,"ip")
        self.port = globals.get_arg(self.args,"port")
        self.valid_filetypes = ('.jpg', '.png', '.jpeg')

        self.teach_url = "http://{}:{}/faces".format(self.ip, self.port)
        self.health_url = "http://{}:{}/faces".format(self.ip, self.port)
        self.check_url = "http://{}:{}".format(self.ip, self.port)

        self.run_in_initial_delay = 43200
        self.run_in_delay = self.run_in_initial_delay
        self.run_in_error_delay = 60

        self.faceRecognitionBot = self.get_app("faceRecognitionBot")

        self.exclude_folders = ("healthcheck", "multiple", "noface", "tmp", "unknown", "new")

        self.timer_handle_list.append(self.run_in(self.run_in_callback, 5))

        self.listen_event_handle_list.append(self.listen_event(self.event_callback,"eifinger_learn_faces"))
        
                
    def run_in_callback(self, kwargs):
        """Check health"""
        try:
            if self.check_classifier_health():
                self.check_if_trained(None)
                self.timer_handle_list.append(self.run_in(self.run_in_callback,self.run_in_delay))
        except requests.exceptions.HTTPError as exception:
            self.log("Error trying to turn on entity. Will try again in 1s. Error: {}".format(exception), level = "WARNING")
            self.timer_handle_list.append(self.run_in(self.run_in_callback, 1))

    def event_callback(self, event_name, data, kwargs):
        """Callback function for manual trigger of face learning"""
        self.log("Event received. Triggering Face Learning")
        self.run_in_callback(None)

    def teach_name_by_file(self, teach_url, name, file_path):
        """Teach facebox a single name using a single file."""
        file_name = file_path.split("/")[-1]
        file = {'file': open(file_path, 'rb')}

        teach_url = teach_url + "?id=" + name
        response = requests.post(teach_url, files=file)

        if response.status_code == 200:
            self.log("File: {} taught with name: {}".format(file_name, name))
            return True

        elif response.status_code == 400:
            self.log("Teaching of file: {} failed with message: {}".format(
                file_name, response.text))
            return False

    def check_classifier_health(self):
        """Check that classifier is reachable"""
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
            self.log("Server is unreachable", level = "WARNING")
            self.log(exception, level = "WARNING")
            # check for recurring error
            if self.run_in_delay < self.run_in_initial_delay:
                self.run_in_delay = self.run_in_delay * 2
            else:
                self.run_in_delay = self.run_in_error_delay
            self.log("Setting run_in_delay to {}".format(self.run_in_delay))        

    def check_if_trained(self, kwargs):
        """Check if faces are trained. If not train them"""
        response = self.faceRecognitionBot.post_image(self.check_url, self.facebox_healthcheck_filename)
        response_json = response.json()
        if response.status_code == 200 and len(response_json["faces"]) > 0 and response_json["faces"][0]["id"] == self.healthcheck_face_name:
            self.log("Faces are still taught")
        else:
            self.log("Faces are not taught")
            self.teach_faces()

    def list_folders(self, directory):
        """Returns a list of folders
        These are not full paths, just the folder."""
        folders = [dir for dir in os.listdir(directory)
               if os.path.isdir(os.path.join(directory, dir))
               and not dir.startswith(directory)
               and not dir.startswith('.')]
        folders.sort(key=str.lower)
        return folders

    def teach_faces(self):
        self.log("Teaching faces")
        for folder_name in self.list_folders(self.folderpath):
            if not folder_name in self.exclude_folders:
                folder_path = os.path.join(self.folderpath, folder_name)
                for file in os.listdir(folder_path):
                    if file.endswith(self.valid_filetypes):
                        file_path = os.path.join(folder_path, file)
                        self.teach_name_by_file(self.teach_url,
                            folder_name,
                            file_path)
        
    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)

    