# SPDX-FileCopyrightText: 2023 Julian Schauder <pytraeger@schauder.info>
#
# SPDX-License-Identifier: MIT

class grill:
    def __init__(self, identifier):
        self.identifier = identifier
        self.data = {}
        self.last_update = None
        self.is_on = True # Default Value of "ON" might speed-up initalization phase as it is primarily used for pollscheduling
        self.listeners = []
    
    def push_data(self, data):
        self.data = data
        self.is_on = data["status"]["connected"]
        for listener in self.listeners:
            try:
                listener(self)
            except:
                pass

    def register_listener(self, listener):
        self.listeners.append(listener)


    def __str__(self):
        return self.identifier