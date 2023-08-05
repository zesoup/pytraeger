<!--
SPDX-FileCopyrightText: 2023 Julian Schauder <pytraeger@schauder.info>

SPDX-License-Identifier: MIT
-->

# PyTraeger
This Project enables Traeger Grill Monitoring.
For my Use-Case a Grafana Dashboard utilizes a PostgreSQL Database (demo/example02.py).

This lib does 3 things.
1) It initiates authentication with AWS
2) It starts the MQTT-Client (thread 1)
3) It polls for updates (thread 2)
4) *It dies after 2 hours as i havent had time to implement accesstoken reneval yet*


Usage in a Nutshell:
```
-- DEMO 1 --
from pytraeger.manager import Manager as TraegerManager

def call_me(event_grill):
    _LOGGER.info("Message from %s. Grill: %-5s | Probe: %-5s",
                    event_grill.identifier,
                    event_grill.data['status']['grill'],event_grill.data['status']['probe'] )


a = TraegerManager(interval_idle=10, interval_busy=5)
for grill in a.api.grills:
    grill.register_listener(call_me)
```

# Getting Started

Fill the environmentfile.
```
cat .devcontainer/devcontainer.env 
PYTRAEGER_PASSWORD=xxx
PYTRAEGER_USERNAME=xxx

# Optional for DB. Enabled in Dockerfile
PGHOST=xxx
PGUSER=xxx
PGPASSWORD=xxx
```
```
$ docker build . -t traegertest
$ docker run --env-file .devcontainer/devcontainer.env  traegertest
2023-08-04 20:00:31,474 - root - INFO - Debugging of API
2023-08-04 20:00:37,449 - root - INFO - Message from XXXXXXXXX. Grill: 35    | Probe: 37
2023-08-04 20:00:42,569 - root - INFO - Message from XXXXXXXXX. Grill: 35    | Probe: 37
```

# Known Issues:

* EMail-Login is case sensitive
* Accesstoken reneval is not implemented.
* The Watchdog
* DB-Usecase doesnt clean up