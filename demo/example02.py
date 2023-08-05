# SPDX-FileCopyrightText: 2023 Julian Schauder <pytraeger@schauder.info>
#
# SPDX-License-Identifier: MIT

import json
import logging
import time

import psycopg2

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


pgcon = psycopg2.connect("")

def push_to_db(event_grill: grillclass):
    # Implying create table events( t timestamp with time zone default now(), payload jsonb ) ;
    _LOGGER.info("Message from %s. Grill: %-5s | Probe: %-5s",
                event_grill.identifier,
                event_grill.data['status']['grill'],
                event_grill.data['status']['probe']
                )
    with pgcon.cursor() as curs:
        curs.execute("INSERT INTO events (payload) VALUES (%s)", [json.dumps( event_grill.data ) ] )
    pgcon.commit()


a = TraegerManager()
a.api.grills[0].register_listener(push_to_db)


while True:
    time.sleep(60)
