import appdaemon.plugins.hass.hassapi as hass
import globals
import requests

#
# App which runs facebox face detection and notifies the result
#
#
# Args:
#  folderpath : Folder containing subfolders with images to train. example: /config/www/facebox
#  image_processing_healthcheck: entity_id of the facebox entity to use for health checking. It holds the local_file image camera of one kown face. example: image_processing.facebox_health_check_picture
#  healthcheck_face_name: name of the face. example: Viktor
#  ip: the ip of facebox. example: localhost
#  port: the port of facebox. example: 8080
#  
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class FaceboxTeacher(hass.Hass):

    def initialize(self):
    
        self.timer_handle_list = []
        self.listen_event_handle_list = []
        self.listen_state_handle_list = []

        self.folderpath = globals.get_arg(self.args,"folderpath")
        self.image_processing_healthcheck = globals.get_arg(self.args, "image_processing_healthcheck")
        self.healthcheck_face_name = globals.get_arg(self.args, "healthcheck_face_name")

        self.ip = globals.get_arg(self.args,"ip")
        self.port = globals.get_arg(self.args,"port")
        self.valid_filetypes = ('.jpg', '.png', '.jpeg')

        self.teach_url = "http://{}:{}/facebox/teach".format(self.ip, self.port)
        self.health_url = "http://{}:{}/info".format(self.ip, self.port)

        self.timer_handle_list.append(self.run_minutely(self.run_minutely_callback, None))
        
                
    def run_minutely_callback(self, kwargs):
        """Check health every minute"""
        if self.check_classifier_health():
            self.check_if_trained()

    def teach_name_by_file(teach_url, name, file_path):
        """Teach facebox a single name using a single file."""
        file_name = file_path.split("/")[-1]
        file = {'file': open(file_path, 'rb')}
        data = {'name': name, "id": file_name}

        response = requests.post(teach_url, files=file, data=data)

        if response.status_code == 200:
            self.log("File:{} taught with name:{}".format(file_name, name))
            return True

        elif response.status_code == 400:
            self.log("Teaching of file:{} failed with message:{}".format(
                file_name, response.text))
            return False

    def check_classifier_health(self):
        """Check that classifier is reachable"""
        try:
            response = requests.get(self.health_url)
            if response.status_code == 200:
                self.log("Health-check passed")
                return True
            else:
                self.log("Health-check failed")
                self.log(response.status_code)
                return False
        except requests.exceptions.RequestException as exception:
            self.log("Server is unreachable")
            self.log(exception)

    def check_if_trained(self):
        """Initiate healthcheck on facebox"""
        self.call_service("image_processing/scan", entity_id = self.image_processing_healthcheck)
        self.timer_handle_list.append(self.run_in(self.check_if_trained_callback,2))

    def check_if_trained_callback(self, kwargs):
        """Check if faces are trained. If not train them"""
        image_processing_state = self.get_state(self.image_processing_healthcheck, attribute = "all")
        matched_faces = image_processing_state["attributes"]["matched_faces"]
        total_faces = image_processing_state["attributes"]["total_faces"]
        if total_faces == 1:
            face_identified = False
            for face in self.known_faces:
                if face == self.healthcheck_face_name:
                    face_identified = True
                    self.log("Faces are still taught")
            if not face_identified:
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
        for folder_name in list_folders(self.folderpath):
            if folder_name != "unknown" and folder_name != "healthcheck":
                folder_path = os.path.join(self.folderpath, folder_name)
                for file in os.listdir(folder_path):
                    if file.endswith(self.valid_filetypes):
                        file_path = os.path.join(folder_path, file)
                        teach_name_by_file(teach_url=self.teach_url,
                            name=folder_name,
                            file_path=file_path)
        
    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)

    