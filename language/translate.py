#!/usr/bin/env python3
"""
Translate class responsible for localisation
"""

import logging
from pathlib import Path
from utils import match
from utils.config import ConfigBase
from utils.load_yaml import yaml_file_to_str, yaml_str_to_dict, yaml_file_to_dict

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
    languageCode:str = ""
    _cache:dict = {}

    @classmethod
    def init(cls, languageCode:str = "", global_context:dict = {}):

        cls.global_context = global_context

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
    def localise(cls, texts:dict, texts_key:str = None, context:dict = {}, cache_key = None):

        # localise is expensive to call a lot, so cache context free values.  This is fine as language does not change per execution
        if context is None or len(context) == 0:
            if cache_key is None:
                # TODO making texts hashable via str(texts) is one way, there might be faster other ways e.g. frozenset
                cache_key = str(texts)
            if (cached_value := cls._cache.get((cache_key, texts_key), None)) is not None:
                return cached_value

        languageCode = cls.languageCode
        if languageCode not in texts:
            logger.warning(f"Could not find language code '{languageCode}' in text dict.  Using default.")
            if (languageCode := cls.defLanguageCode) not in texts:
                logger.warning(f"Could not find language code '{languageCode}' in text dict.")

        textsLanguage = texts.get(languageCode, {texts_key:f"Could not find texts in language '{languageCode}'"})
        if not match.is_empty(texts_key):
            # textsLanguage is a dict
            textsLanguageText = textsLanguage.get(texts_key, f"Could not find text for key '{texts_key}'")
        else:
            # textsLanguage is the actual string
            textsLanguageText = textsLanguage

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
            cls._cache[(cache_key, texts_key)] = output

        return output
        #return env.from_string(texts.get(languageCode, {texts_key:f"Could not find texts in language '{languageCode}'"}).get(texts_key, f"Could not find text for key '{texts_key}'")).render(context | cls.translations | cls.global_context)

    @classmethod
    def localiseYamlFile(cls, filepath:Path) -> dict:

        yaml_str = yaml_file_to_str(filepath)

        localised_yaml_str = env.from_string(yaml_str).render(cls.translations | cls.global_context)

        return yaml_str_to_dict(localised_yaml_str)

    @classmethod
    def getTranslation(cls, key:str):
        return cls.translations.get("translate", {}).get(key, None)