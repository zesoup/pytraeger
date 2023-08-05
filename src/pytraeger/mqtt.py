# SPDX-FileCopyrightText: 2023 Julian Schauder <pytraeger@schauder.info>
#
# SPDX-License-Identifier: MIT

import urllib

import logging
import ssl
import json

import paho.mqtt.client as _mqtt

_LOGGER: logging.Logger = logging.getLogger(__package__)
_LOGGER.setLevel(logging.DEBUG)


class Mqtt:
    def __init__(self, connectstring, grills, immediate_init=True):
        self.connectstring = connectstring
        self.grills = grills
        self.client = None
        self.datahook = None
        if immediate_init:
            self.init()
            self.start()

    def start(self):
        self.client.loop_start()

    def set_datahook(self, hook):
        self.datahook = hook

    def mqtt_onconnect(self, client_instance, userdata, flags, rc):
        _LOGGER.debug("Client Connected")

        for grill in self.grills:
            client_instance.subscribe(
                ("prod/thing/update/{}".format(grill), 1))
        _LOGGER.debug("Grill Connected")

    def mqtt_onconnectfail(self, client, userdata):
        _LOGGER.debug(
            "Connect Fail Callback. Client:%s userdata: %s", client, userdata)
        _LOGGER.debug("Grill Connect Failed! MQTT Client Kill.")

    def mqtt_onlog(self, client, userdata, level, buf):
        _LOGGER.debug(
            "OnLog Callback. Client:%s userdata:%s level:%s buf: %s", 
            client, userdata, level, buf)

    def mqtt_onsubscribe(self, client, userdata, mid, granted_qos):
        _LOGGER.debug(
            "OnSubscribe Callback. Client:%s userdata:%s mid:%s granted_qos:%s", 
            client, userdata, mid, granted_qos)

    def mqtt_onmessage(self, client, userdata, message):
        _LOGGER.debug("Message for Grill: %s", message.topic)

        data = json.loads(message.payload)
        try:
            self.datahook(message.topic, data)
        except Exception as e:
            _LOGGER.warning(e)

    def init(self):
        mqtt_client = _mqtt.Client(
            transport="websockets", reconnect_on_failure=False, clean_session=True)
        mqtt_client.on_connect = self.mqtt_onconnect
        mqtt_client.on_connect_fail = self.mqtt_onconnectfail
        mqtt_client.enable_logger(_LOGGER)
        mqtt_client.on_subscribe = self.mqtt_onsubscribe
        mqtt_client.on_message = self.mqtt_onmessage
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        mqtt_client.tls_set_context(context)
        mqtt_client.reconnect_delay_set(min_delay=3, max_delay=5)
        mqtt_parts = urllib.parse.urlparse(self.connectstring)

        headers = {
            "Host": "{0:s}".format(mqtt_parts.netloc),
        }
        mqtt_client.ws_set_options(path="{}?{}".format(
            mqtt_parts.path, mqtt_parts.query), headers=headers)
        _LOGGER.debug("Connecting to %s", mqtt_parts.netloc)
        mqtt_client.connect(mqtt_parts.netloc, port=443, keepalive=30)
        self.client = mqtt_client
