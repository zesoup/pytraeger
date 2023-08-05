# SPDX-FileCopyrightText: 2023 Julian Schauder <pytraeger@schauder.info>
#
# SPDX-License-Identifier: MIT

import threading
import time
import logging
import os

from pytraeger.mqtt import Mqtt
from pytraeger.api import Api


_LOGGER: logging.Logger = logging.getLogger(__package__)
_LOGGER.setLevel(logging.DEBUG)


class Manager:
    def __init__(self,
                 username="",
                 password="",
                 interval_idle=60*5,
                 interval_busy=10,
                 ):
        if username == "":
            self.username = os.environ["PYTRAEGER_USERNAME"]
        else:
            self.username = username
        if password == "":
            self.password = os.environ["PYTRAEGER_PASSWORD"]
        else:
            self.password = password

        self.interval_idle = interval_idle
        self.interval_busy = interval_busy
        self.api = Api(self.username, self.password,
                       self.interval_idle, self.interval_busy)
        self.mqtt_client = Mqtt(self.api.get_mqtt_endpoint(),
                                [grill.identifier for grill in self.api.grills])
        self.mqtt_client.set_datahook(self.mqtt_event_dispatcher)

        self.start_thread_apipolling()

    def start_thread_apipolling(self):
        for grill in self.api.grills:
            threading.Thread(target=poll_updates, args=(
                grill.identifier, self.api)).start()
        threading.Thread(target=watchdog, args=()).start()

    def mqtt_event_dispatcher(self, topic, data):
        for grill in self.api.grills:
            if topic.endswith(grill.identifier):
                grill.push_data(data)
                _LOGGER.debug("Message Received from Grill(%s): Online : %s",
                              topic, data["status"]["connected"]
                              )
                break


def watchdog():
    # After two hours, kill the program.
    # The current implementation should die after exactly 1h due to outdated tokens.
    # If an unexpected bug prevents natural death by age, initiate death by watchdog
    time.sleep(60*60*2)
    os._exit(1)


def poll_updates(grill_identifier, parent_api: Api):
    # Make sure to pull the grill via the identifier.
    # Might only be usefull for grill reinstanciations.
    while True:
        try:
            grill_object = None
            for grill in parent_api.grills:
                if grill.identifier == grill_identifier:
                    grill_object = grill
                    break

            if grill_object.is_on:
                time.sleep(parent_api.interval_busy)
            else:
                time.sleep(parent_api.interval_idle)
            _LOGGER.debug("Polling Update for %s",
                          grill_identifier
                          )

            parent_api.update_grill(grill_identifier)
        except Exception as exception:
            _LOGGER.critical(exception)
            os._exit(1)
