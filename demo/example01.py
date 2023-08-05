# SPDX-FileCopyrightText: 2023 Julian Schauder <pytraeger@schauder.info>
#
# SPDX-License-Identifier: MIT

import time
import logging

from pytraeger.manager import Manager as TraegerManager
from pytraeger.grill import grill as grillclass



#Log Boilerplate
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_LOGGER: logging.Logger = logging.getLogger(__package__)
_LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
_LOGGER.addHandler(ch)



def call_me(event_grill: grillclass):
    _LOGGER.info("Message from %s. Grill: %-5s | Probe: %-5s",
                    event_grill.identifier,
                    event_grill.data['status']['grill'],event_grill.data['status']['probe'] )


a = TraegerManager(interval_idle=10, interval_busy=5)
for grill in a.api.grills:
    grill.register_listener(call_me)


while True:
    time.sleep(60)
