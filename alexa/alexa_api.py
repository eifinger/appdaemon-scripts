import appdaemon.plugins.hass.hassapi as hass
import random
import datetime


class alexa_api(hass.Hass):
    def initialize(self):
        self.register_endpoint(self.api_call)
        self.tempCardContent = ""

    def api_call(self, data):
        self.my_alexa_interpret_data(data)
        response = ""
        dialogDelegate = False
        endsession = False
        speech = None
        card = None
        logtext = ""
        if self.dialog == None:
            if self.requesttype == "LaunchRequest":
                speech = self.random_arg(self.args["launchRequest"])
                endSession = False
                dialogDelegate = False
                card = None
                self.alexalog("Launch request (activate command)", 100, "*")
            elif self.requesttype == "IntentRequest":
                speech = None
                endSession = False
                dialogDelegate = True
                card = None
                self.alexalog("start dialog", 100, "*")
            elif self.requesttype == "SessionEndedRequest":
                speech = None
                endSession = False
                dialogDelegate = False
                card = None
                self.alexalog("The session has ended", 100, "*")
            else:
                self.alexalog("Strange state", 100, "*")
        elif self.dialog == "STARTED":
            ############################################
            # conversation started, just response dialogDelegate
            ############################################
            speech = None
            endSession = False
            dialogDelegate = True
            card = None
            self.alexalog("dialog has been started", 100, "*")
        elif self.dialog == "IN_PROGRESS":
            speech = None
            endSession = False
            dialogDelegate = True
            card = None
            self.alexalog("dialog is in progress", 100, "*")
        elif self.dialog == "COMPLETED":
            try:
                intentResponse = self.getIntentResponse()
            except:
                intentResponse = self.random_arg(self.args["responseError"])
            if intentResponse == "stop":
                ############################################
                # user used stop intent, stop conversation
                ############################################
                speech = self.random_arg(self.args["conversationEnd"])
                endSession = True
                dialogDelegate = False
                card = True
                cardContent = self.tempCardContent
                self.tempCardContent = ""
                self.alexalog(
                    "dialog has been completed, Dialog stopped by user", 100, "*"
                )
            else:
                ############################################
                # user just responded yes, so just a question
                ############################################
                speech = self.random_arg(self.args["nextConversationQuestion"])
                endSession = False
                dialogDelegate = False
                card = None
                self.tempCardContent = self.tempCardContent + self.intentname + "\n"
                self.alexalog(
                    "dialog has been completed, User just responded yes", 100, "*"
                )
        if speech != None:
            speech = self.cleanup_text(speech)
        if card:
            response = self.my_alexa_response(
                EndSession=endSession,
                DialogDelegate=dialogDelegate,
                speech=speech,
                card=True,
                title=self.args["cardTitle"],
                content=cardContent,
            )
            self.alexalog(" ", 100, "X")
            self.alexalog(" ", 100, "X")
            self.alexalog(" ", 100, "X")
        else:
            response = self.my_alexa_response(
                EndSession=endSession,
                DialogDelegate=dialogDelegate,
                speech=speech,
                card=None,
            )
        if speech != None:
            if self.intentname == None:
                self.alexaresponselog("No Intent : " + speech)
            else:
                self.alexaresponselog(self.intentname + " : " + speech)
        return response, 200

    def my_alexa_interpret_data(self, data):
        ############################################
        # create vars from the data
        ############################################
        self.allslots = {}
        self.slots = {}
        self.dialog = self.my_alexa_dialog_state(data)
        self.requesttype = self.my_alexa_request_type(data)
        self.alexa_error = self.my_alexa_error(data)
        self.intentname = self.my_alexa_intent_name(data)
        if self.intentname != None:
            if "." in self.intentname:
                splitintent = self.intentname.split(".")
                self.intentname = splitintent[1]
        device = data["context"]["System"]["device"]["deviceId"]
        self.devicename = self.args["devices"]["unknownDevice"]
        for devicename, deviceid in self.args["devices"].items():
            if deviceid == device:
                self.devicename = devicename
        if self.devicename == self.args["devices"]["unknownDevice"]:
            self.log(device)
        ############################################
        # get slots out of the data
        ############################################
        if (
            "request" in data
            and "intent" in data["request"]
            and "slots" in data["request"]["intent"]
        ):
            self.allslots = data["request"]["intent"]["slots"]
        slottext = "slots: "
        for slot, slotvalue in self.allslots.items():
            if "value" in slotvalue:
                self.slots[slot] = slotvalue["value"].lower()
            else:
                self.slots[slot] = ""
        if self.intentname == "searchYoutubeIntent":
            self.slots["search"] = (
                self.slots["searchfielda"]
                + self.slots["searchfieldb"]
                + self.slots["searchfieldc"]
                + self.slots["searchfieldd"]
            )
        ############################################
        # log that data came in
        ############################################
        self.alexalog("data came in.", 100, "#")
        self.alexalog(
            "dialogstate = "
            + str(self.dialog)
            + " and requesttype = "
            + str(self.requesttype)
        )
        self.alexalog("intent = " + str(self.intentname))
        slottext = "slots: "
        for slot, slotvalue in self.slots.items():
            slottext = slottext + slot + "= " + str(slotvalue) + ", "
        self.alexalog(slottext)
        self.alexalog("error = " + str(self.alexa_error))
        self.alexalog(" ", 100, "#")

    def my_alexa_intent_name(self, data):
        ############################################
        # find the intent name in the data
        ############################################
        if (
            "request" in data
            and "intent" in data["request"]
            and "name" in data["request"]["intent"]
        ):
            return data["request"]["intent"]["name"]
        else:
            return None

    def my_alexa_dialog_state(self, data):
        ############################################
        # find the dialog state in the data
        ############################################
        if "request" in data and "dialogState" in data["request"]:
            return data["request"]["dialogState"]
        else:
            return None

    def my_alexa_intent(self, data):
        ############################################
        # find the requesttype in the data
        ############################################
        if "request" in data and "intent" in data["request"]:
            return data["request"]["intent"]
        else:
            return None

    def my_alexa_request_type(self, data):
        ############################################
        # find the requesttype in the data
        ############################################
        if "request" in data and "type" in data["request"]:
            return data["request"]["type"]
        else:
            return None

    def my_alexa_error(self, data):
        ############################################
        # get an error out of the data
        ############################################
        if (
            "request" in data
            and "error" in data["request"]
            and "message" in data["request"]["error"]
        ):
            return data["request"]["error"]["message"]
        else:
            return None

    def my_alexa_slot_value(self, data, slot):
        ############################################
        # get a slot value from the data
        ############################################
        if (
            "request" in data
            and "intent" in data["request"]
            and "slots" in data["request"]["intent"]
            and slot in data["request"]["intent"]["slots"]
            and "value" in data["request"]["intent"]["slots"][slot]
        ):
            return data["request"]["intent"]["slots"][slot]["value"]
        else:
            return ""

    def my_alexa_response(
        self,
        EndSession=False,
        DialogDelegate=False,
        speech=None,
        card=None,
        title=None,
        content=None,
    ):
        ############################################
        # put the speechfield from the response toghether
        ############################################
        response = {"shouldEndSession": EndSession}
        if DialogDelegate:
            response["directives"] = [
                {"type": "Dialog.Delegate", "updatedIntent": None}
            ]
        if speech is not None:
            response["outputSpeech"] = {
                "type": "SSML",
                "ssml": "<speak>" + speech + "</speak>",
            }
        if card is not None:
            response["card"] = {"type": "Simple", "title": title, "content": content}

        speech = {"version": "1.0", "response": response, "sessionAttributes": {}}
        return speech

    def random_arg(self, argName):
        ############################################
        # pick a random text from a list
        ############################################
        if isinstance(argName, list):
            text = random.choice(argName)
        else:
            text = argname
        return text

    def floatToStr(self, myfloat):
        ############################################
        # replace . with , for better speech
        ############################################
        floatstr = str(myfloat)
        floatstr = floatstr.replace(".", ",")
        return floatstr

    def cleanup_text(self, text):
        ############################################
        # replace some text like temperary slots with its value
        ############################################
        # self.log(text)
        for slotname, slotvalue in self.slots.items():
            text = text.replace("{{" + slotname + "}}", slotvalue)
        text = text.replace("{{device}}", self.devicename)

        text = text.replace("_", " ")
        text = text.replace("...", "<break time='2s'/>")
        return text

    def alexalog(self, logtext, repeat=0, surrounding=""):
        ############################################
        # put an entry in the alexa log
        ############################################
        if self.args["logging"] == "true" or self.args["logging"] == "True":
            runtime = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S.%f")
            if repeat > 0:
                surrounding = surrounding * repeat
            try:
                log = open(self.args["logfile"], "a")
                if logtext == " ":
                    log.write(runtime + ";  " + surrounding + "\n")
                else:
                    if surrounding != "":
                        log.write(runtime + ";  " + surrounding + "\n")
                    log.write(runtime + ";  " + logtext + "\n")
                    if surrounding != "":
                        log.write(runtime + ";  " + surrounding + "\n")
                log.close()
            except:
                self.log("ALEXA LOGFILE CANT BE WRITTEN!!")

    def alexaresponselog(self, logtext):
        ############################################
        # put an entry in the alexa responses log
        ############################################
        if self.args["logging"] == "true" or self.args["logging"] == "True":
            runtime = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S.%f")
            try:
                log = open(self.args["responselogfile"], "a")
                log.write(runtime + ";  " + logtext + "\n")
                log.close()
            except:
                self.log("ALEXA RESPONSELOGFILE CANT BE WRITTEN!!")

    def getIntentResponse(self):
        ############################################
        # perform the intent end get the response back
        # from the intent apps
        ############################################
        if self.intentname == "StopIntent":
            return "stop"
        if self.intentname == "yesIntent":
            return "next"
        alexa = self.get_app(self.intentname)
        return alexa.getIntentResponse(self.slots, self.devicename)
