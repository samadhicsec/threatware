#!/usr/bin/env python3

import logging

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

class key:

    def __init__(self, name:str, tags:list = None):
        # Fun python fact, don't have default value be somethign you want to change e.g. list, 
        # because default values are initialised once so all class instances will share them
        self.name = name
        if tags is None:
            self.tags = list()
        else:   
            self.tags = list(tags)  # This is apparently key otherwise we will edit the passed in list 
        self.properties = {}

    def copy(obj):
        if isinstance(obj, key):
            return key(obj.name, obj.tags)
        return None

    def addTag(self, tag:str):
        if not tag in self.tags:
            self.tags.append(tag)

    def addTags(self, tags:list):
        for tag in tags:
            self.addTag(tag)

    def hasTag(self, tag):
        return tag in self.tags

    def getTags(self):
        return self.tags

    def addProperty(self, property_name, property_value):
        if property_name is not None and isinstance(property_name, str) and property_name != "":
            self.properties[property_name] = property_value

    def getProperty(self, property_name):
        return self.properties.get(property_name, None)

    def __str__(self):
        return self.name
    
    def __repr__(self):
        if not self.tags:
            return self.name
        else:
            return f"<name:{self.name}, tags:{self.tags}>"

    def __eq__(self, other):

        if isinstance(other, str):
            return self.name == other

        if isinstance(other, key):
            return (self.name == other.name)
            #return (self.name == other.name) and (self.tags.sort() == other.tags.sort())

        return NotImplemented

    def __hash__(self):
        return hash(self.name)
