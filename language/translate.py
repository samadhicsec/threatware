#!/usr/bin/env python3
"""
Translate class responsible for localisation
"""

import logging
from pathlib import Path
from utils import match
from utils.config import ConfigBase
from utils.load_yaml import yaml_file_to_str, yaml_str_to_dict, yaml_file_to_dict
from utils.request import Request

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

from jinja2 import Environment, FileSystemLoader, select_autoescape
env = Environment(
    loader = FileSystemLoader(searchpath="./"),
    autoescape=select_autoescape()
)

TRANSLATE_CONFIG_YAML = "translate.yaml"
TRANSLATE_CONFIG_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(TRANSLATE_CONFIG_YAML))

class Translate:

    translations:dict = {}
    global_context:dict = {}
    defLanguageCode:str = "default"
    defOutputFormatKey:str = "default"
    languageCode:str = ""
    _cache:dict = {}

    @classmethod
    def init(cls):
    #def init(cls, languageCode:str = "", global_context:dict = {}):

        #cls.global_context = global_context
        cls.global_context = {"request": Request.get()}
        languageCode = Request.lang

        yaml_config_dict = yaml_file_to_dict(ConfigBase.getConfigPath(TRANSLATE_CONFIG_YAML_PATH))

        if languageCode is None or languageCode == "":
            languageCode = cls.defLanguageCode

        if languageCode not in yaml_config_dict:
            logger.warning(f"Could not find language code '{languageCode}' in translation file '{TRANSLATE_CONFIG_YAML_PATH}'.  Using {cls.defLanguageCode}.")
            languageCode = cls.defLanguageCode
            if languageCode not in yaml_config_dict:
                logger.warning(f"Could not find language code '{languageCode}' in translation file '{TRANSLATE_CONFIG_YAML_PATH}'.")

        cls.languageCode = languageCode
        cls.translations = yaml_config_dict.get(cls.languageCode, {})

    @classmethod
    def localise(cls, texts:dict, texts_key:str = None, context:dict = {}, cache_key = None, ignore_format:bool = False):

        # localise is expensive to call a lot, so cache context free values.  This is fine as language does not change per execution
        if context is None or len(context) == 0:
            if cache_key is None:
                # TODO making texts hashable via str(texts) is one way, there might be faster other ways e.g. frozenset
                cache_key = str(texts)
            if (cached_value := cls._cache.get((cache_key, texts_key, ignore_format), None)) is not None:
                return cached_value

        if texts is None or len(texts) == 0:
            logger.error("Translate requires a dict of texts to localise from, but an empty dict was provided.")
            return ""

        # Get the language code (set in init)
        languageCode = cls.languageCode
        if languageCode not in texts:
            logger.warning(f"Could not find language code '{languageCode}' in text dict.  Using default.")
            if (languageCode := cls.defLanguageCode) not in texts:
                logger.warning(f"Could not find language code '{languageCode}' in text dict.")

        # Get the set of texts for that language
        textsLanguage = texts.get(languageCode, {texts_key:f"Could not find texts in language '{languageCode}'"})

        if not match.is_empty(texts_key):
            # textsLanguage is a dict
            # Lookup the texts_key in the set of texts for that language
            textsLanguageText = textsLanguage.get(texts_key, f"Could not find text for key '{texts_key}'")
        elif isinstance(textsLanguage, str):
            # textsLanguage is the actual string
            # Edge case where we want aren't looking for a key in a set of language texts, but rather 
            # have a set of language texts for a single key (which hasn't been passed in), so we want to 
            # just return the text associated with the language code
            textsLanguageText = textsLanguage
        else:
            # Since no texts_key has been passed in, and we can't translate an empty string, we'll just return an empty string
            # This can happen in error handling when an unexpected error occurs and we are trying to localise the error message
            logger.debug(f"No localisation text key passed in, so we can't choose a localised text from the supplied texts.  Returning an empty string.")
            return ""

        # We may have different versions of the text for different output formats e.g. json vs html
        if isinstance(textsLanguageText, dict):
            format = Request.format
            if ignore_format is True:
                format = "default"
            # Check if the requested output format text is available, otherwise use the default
            if format in textsLanguageText:
                textsLanguageText = textsLanguageText.get(format)
            elif cls.defOutputFormatKey in textsLanguageText:
                textsLanguageText = textsLanguageText.get(cls.defOutputFormatKey)
            else:
                logger.warning(f"The localised texts didn't have a format entry matching '{format}' or the default '{cls.defOutputFormatKey}'.")
                
        if isinstance(textsLanguageText, str):
            output = env.from_string(textsLanguageText).render(context | cls.translations | cls.global_context)
        elif isinstance(textsLanguageText, list):
            output = []
            for textsLanguageTextEntry in textsLanguageText:
                # Assume all entries are strings
                output.append(env.from_string(textsLanguageTextEntry).render(context | cls.translations | cls.global_context))
        else:
            logger.warning(f"Unsupported type '{type(textsLanguageText)}' passed to method.  Returning un-localised value.")
            output = textsLanguageText

        if context is None or len(context) == 0:
            cls._cache[(cache_key, texts_key, ignore_format)] = output

        return output

    @classmethod
    def localiseYamlFile(cls, filepath:Path) -> dict:

        yaml_str = yaml_file_to_str(filepath)

        localised_yaml_str = env.from_string(yaml_str).render(cls.translations | cls.global_context)

        return yaml_str_to_dict(localised_yaml_str)

    @classmethod
    def getTranslation(cls, key:str):
        return cls.translations.get("translate", {}).get(key, None)