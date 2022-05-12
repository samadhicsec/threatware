#!/usr/bin/env python3

import logging
from utils.load_yaml import yaml_register_class
from enum import Enum

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

class KeySerialiseType(Enum):
    NO_TAGS_PROPERTIES = 0
    TAGS = 1
    TAGS_PROPERTIES = 2


class key:
    yaml_tag = u'!Key'
    
    serialise_type:KeySerialiseType = KeySerialiseType.TAGS_PROPERTIES

    def __init__(self, name:str, tags:list = None):
        # Fun python fact, don't have default value be something you want to change e.g. list, 
        # because default values are initialised once so all class instances will share them
        self.name = name
        if tags is None:
            self.tags = list()
        else:   
            self.tags = list(tags)  # This is apparently key otherwise we will edit the passed in list 
        self.properties = {}

        yaml_register_class(key)

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
    
    # def __getstate__(self):
    #     # To customise jsonpickle output
    #     return {"name":self.__str__()}

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

    # @classmethod
    # def to_yaml(cls, representer, node):
    #     return representer.represent_str(node.name)

    @classmethod
    def config_serialisation(cls, meta_level:str):
         
        if meta_level == "none":
            cls.serialise_type = KeySerialiseType.NO_TAGS_PROPERTIES
        elif meta_level == "tags":
            cls.serialise_type = KeySerialiseType.TAGS
        elif meta_level == "properties":
            cls.serialise_type = KeySerialiseType.TAGS_PROPERTIES

    @classmethod
    def to_yaml(cls, representer, node):
        if cls.serialise_type == KeySerialiseType.NO_TAGS_PROPERTIES:
            return representer.represent_str(node.name)
        elif cls.serialise_type == KeySerialiseType.TAGS:
            return representer.represent_mapping(cls.yaml_tag, {"name":node.name, "tags":node.tags})
        elif cls.serialise_type == KeySerialiseType.TAGS_PROPERTIES:
            return representer.represent_mapping(cls.yaml_tag, {"name":node.name, "tags":node.tags, "properties":node.properties})

    @classmethod
    def from_yaml(cls, constructor, node):
        if cls.serialise_type == KeySerialiseType.NO_TAGS_PROPERTIES:
            
            logger.error(f"Deserialisation from a serialised Key that did not not include tags or properties should not be called.")
            return cls(str(constructor.construct_yaml_str(node)))

        elif cls.serialise_type == KeySerialiseType.TAGS:
            
            logger.error(f"Deserialisation from a serialised Key that did not not include properties should not be called.")

            key_dict = constructor.construct_mapping(node)

            key_obj = cls(key_dict["name"], key_dict["tags"])

            return key_obj

        elif cls.serialise_type == KeySerialiseType.TAGS_PROPERTIES:
            
            key_dict = constructor.construct_mapping(node)

            key_obj = cls(key_dict["name"], key_dict["tags"])

            for prop_name, prop_value in key_dict["properties"].items():
                key_obj.addProperty(prop_name, prop_value)

            return key_obj