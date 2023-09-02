# SPDX-FileCopyrightText: 2023 Julian Schauder <pytraeger@schauder.info>
#
# SPDX-License-Identifier: MIT

import datetime
import logging

import requests

from pytraeger.grill import grill as grill_class
from pytraeger.mqtt import Mqtt

AMAZON_COGNITO_GATEWAY = 'https://cognito-idp.us-west-2.amazonaws.com/'
AMAZON_API_ENDPOINT = 'https://1ywgyc65d1.execute-api.us-west-2.amazonaws.com/prod/'
TRAEGER_CLIENT_ID = "2fuohjtqv1e63dckp5v84rau0j"  # Seems to be the Traeger-ID

AMAZON_COMMAND_CODES = {
    "refresh": 90
}
HTTP_TIMEOUT = 20
_LOGGER: logging.Logger = logging.getLogger(__package__)
_LOGGER.setLevel(logging.DEBUG)


class Api:
    def __init__(self,
                 username="",
                 password="",
                 interval_idle=60*5,
                 interval_busy=10,
                 immediate_init=True
                 ):
        self.username = username
        self.password = password

        self.interval_idle = interval_idle
        self.interval_busy = interval_busy
        self.grills = [grill_class]  # will be of type pytraeger.grill

        self.cognito_details = None
        self.cognito_refreshtoken = None

        self.mqtt_endpoint = None
        self.mqtt_client = None
        if immediate_init:
            self.init()

    def init(self):
        _LOGGER.debug("Initialization of API")
        self.do_cognito()
        self.get_grills()

        # Asking Grills for an Update is nonessential but ensures a quick application boot
        for grill in self.grills:
            self.update_grill(grill.identifier)

    def get_amzdate(self):
        return datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')

    def do_cognito(self):
        _LOGGER.debug("Cognito Initiation")
        if self.cognito_details and self.cognito_details["Date"] + datetime.timedelta(seconds=self.cognito_details["ExpiresIn"]*.8) >= datetime.datetime.now():
            # Cognito Status seems up-to-date.
            # No Update will be done.
            _LOGGER.debug("Still Logged-In. No Cognito Refresh Triggered")
            return
        _LOGGER.debug("Cognito Refresh Triggered")
        if self.cognito_refreshtoken:
            _LOGGER.debug("Cognito Refreshmethod: Refreshtoken")
            # The upper being anything but none shows that we've logged in before.
            # A Refresh Token should be used insted of a full login.
            # The Assumption will be made, altough we could only be sure of the login-state after polling the API.
            # This might be less safe than logging in (e.g. host was suspended )
            data = {
                "ClientMetadata": {},
                "AuthParameters": {
                    "REFRESH_TOKEN": self.cognito_refreshtoken,
                    "USERNAME": self.username,
                },
                "AuthFlow": "REFRESH_TOKEN_AUTH",
                "ClientId": TRAEGER_CLIENT_ID
            }
        else: 
            _LOGGER.debug("Cognito Refreshmethod: Password Auth")
            data = {
                "ClientMetadata": {},
                "AuthParameters": {
                    "PASSWORD": self.password,
                    "USERNAME": self.username,
                },
                "AuthFlow": "USER_PASSWORD_AUTH",
                "ClientId": TRAEGER_CLIENT_ID
            }
        response = requests.post(AMAZON_COGNITO_GATEWAY,
                                 json=data,
                                 headers={'Content-Type': 'application/x-amz-json-1.1',
                                          'X-Amz-Date': self.get_amzdate(),
                                          'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth'
                                          }, timeout=HTTP_TIMEOUT)
        assert response.status_code == 200

        self.cognito_details = response.json(
        )["AuthenticationResult"]
        if "RefreshToken" in self.cognito_details:
            # First-Call-Only will provide a RefreshToken.
            self.cognito_refreshtoken = self.cognito_details["RefreshToken"]

        self.cognito_details["Date"] = datetime.datetime.now()
        _LOGGER.debug("Login successful")
        # TODO- Validity

    def get_grills(self):
        _LOGGER.debug("Inventory-Update")
        response = requests.get(AMAZON_API_ENDPOINT+"/users/self",
                                headers={
                                    'authorization': self.cognito_details["AccessToken"]}, timeout=HTTP_TIMEOUT)
        assert response.status_code == 200
        grills = response.json()["things"]
        self.grills = []
        for grill in grills:
            self.grills.append(grill_class(grill["thingName"]))
            _LOGGER.debug("Added ID: %s",
                          grill["thingName"]
                          )

    def update_grill(self, grill_identifier):
        response = requests.post(AMAZON_API_ENDPOINT+"/things/{}/commands".format(grill_identifier),
                                 json={
            'command': AMAZON_COMMAND_CODES["refresh"]
        },
            headers={
            'Authorization': self.cognito_details["AccessToken"],
            "Content-Type": "application/json",
            "Accept-Language": "en-us",
            'X-Amz-Date': self.get_amzdate(),
            "User-Agent": "Traeger/11 CFNetwork/1209 Darwin/20.2.0",
        }, timeout=HTTP_TIMEOUT)
        assert response.status_code == 200

    def get_mqtt_endpoint(self):
        self.mqtt_endpoint = requests.post(AMAZON_API_ENDPOINT+"/mqtt-connections",
                                           headers={
                                               'Authorization': self.cognito_details["AccessToken"],
                                               'X-Amz-Date': self.get_amzdate(),
                                               "Content-Type": "application/json",
                                               "Accept-Language": "en-us",
                                               "User-Agent": "Traeger/11 CFNetwork/1209 Darwin/20.2.0",
                                           }, timeout=HTTP_TIMEOUT).json()["signedUrl"]
        return self.mqtt_endpoint
