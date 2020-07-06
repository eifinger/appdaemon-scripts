import appdaemon.plugins.hass.hassapi as hass
import socket
import os
import json
import requests

#
# App which forwards all logs to seq.
#
# Args:
#
# server_url: Server url of the seq instance to log to. example: "http://seq:5341/"
# api_key (optional): Api key to use.
#
# Release Notes
#
# Version 1.0:
#   Initial Version


class SeqSink(hass.Hass):
    def initialize(self):
        self.server_url = self.args["server_url"]
        if not self.server_url.endswith("/"):
            self.server_url += "/"
        self.server_url += "api/events/raw"

        self.session = requests.Session()
        self.session.headers["Content-Type"] = "application/json"

        api_key = self.args.get("api_key")
        if api_key:
            self.session.headers["X-Seq-ApiKey"] = api_key

        self.handle = self.listen_log(self.log_message_callback)

    def log_message_callback(self, app_name, ts, level, log_type, message, kwargs):
        if app_name != "seqSink":
            event_data = {
                "Timestamp": str(ts),
                "Level": str(level),
                "MessageTemplate": str(message),
                "Properties": {
                    "Type": "Appdaemon",
                    "AppName": str(app_name)
                },
            }
            request_body = {"Events": [event_data]}

            try:
                request_body_json = json.dumps(request_body)
            except TypeError:
                self.log(f"Could not serialize {request_body}")
                return

            try:
                response = self.session.post(
                    self.server_url,
                    data=request_body_json,
                    stream=True,  # prevent '362'
                )
                response.raise_for_status()
            except requests.RequestException as requestFailed:
                self.log(f"Could not serialize {message}")

                if not requestFailed.response:
                    self.log("Response from Seq was unavailable.")
                elif not requestFailed.response.text:
                    self.log("Response body from Seq was empty.")
                else:
                    self.log(f"Response body from Seq:{requestFailed.response.text}")

    def terminate(self):
        self.cancel_listen_log(self.handle)
