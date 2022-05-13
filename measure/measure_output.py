#!/usr/bin/env python3
"""
Class MeasureOutput
"""

import logging
import utils.load_yaml
from utils.load_yaml import yaml_register_class
from utils.output import FormatOutput
import jsonpickle

import utils.logging
from utils.keymaster import get_column_name_for_key
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

# from jinja2 import Environment, FileSystemLoader, select_autoescape
# env = Environment(
#     loader = FileSystemLoader(searchpath="./"),
#     autoescape=select_autoescape()
# )

class Measurement:

    def __init__(self, config, this_model_title, this_model_version, other_model_title, other_model_version, section_key, tag_tuple, key_tag_list:list):
        yaml_register_class(Measurement)

        template_text_file = config.get("output").get("template-text-file")

        self.templated_texts = utils.load_yaml.yaml_file_to_dict(template_text_file).get("output-texts")
        self.config = config
        self.this_model_title = this_model_title
        self.this_model_version = this_model_version
        self.other_model_title = other_model_title
        self.other_model_version = other_model_version
        self.section_key = section_key
        self.tag_tuple = tag_tuple
        self.key_tag_list = key_tag_list
        self.count = 0
        self.distances = []

    def addCount(self, count):
        """ The total number of possible distances to measure for the tagged data """
        # Basically the number of rows
        self.count = count

    def addDistance(self, distance):
        self.distances.append(distance)

    def _get_state(self):

        output = {}
        
        context = {"section":self.section_key, "this_model_name":self.this_model_title, "other_model_name":self.other_model_title}
        measure_from_this_model = self.config["measure-tag"]["measure-this-model-against-other-model"]
        measure_from_other_model = self.config["measure-tag"]["measure-other-model-against-this-model"]
        measure_compare_missing = self.config["measure-tag"]["measure-compare-missing"]
        measure_compare_extra = self.config["measure-tag"]["measure-compare-extra"]

        measuring = {}
        measuring["section"] = self.section_key.getProperty("section")
        measuring["columns"] = []
        for col_name, tag_tuple in self.key_tag_list:
            column = {"name":get_column_name_for_key(col_name)}
            if tag_tuple[3] is not None:
                column["filter"] = tag_tuple[3]
            measuring["columns"].append(column)

        this_model = {"title":self.this_model_title, "version":self.this_model_version}
        other_model = {"title":self.other_model_title, "version":self.other_model_version}

        if measure_from_this_model in self.tag_tuple[1] and measure_compare_missing in self.tag_tuple[2]:
            output["from"] = this_model
            output["measuring"] = measuring
            output["to"] = other_model
        elif measure_from_this_model in self.tag_tuple[1] and measure_compare_extra in self.tag_tuple[2]:
            output["from"] = this_model
            output["measuring"] = measuring
            output["to"] = other_model
        elif measure_from_other_model in self.tag_tuple[1] and measure_compare_missing in self.tag_tuple[2]:
            output["from"] = other_model
            output["measuring"] = measuring
            output["to"] = this_model
        elif measure_from_other_model in self.tag_tuple[1] and measure_compare_extra in self.tag_tuple[2]:
            output["from"] = other_model
            output["measuring"] = measuring
            output["to"] = this_model

        output["distance-metric"] = len(self.distances)
        if len(self.distances) > 0:
            output["distances"] = []
            for row in self.distances:
                row_output = []
                for col_key, col_value in row:
                    col_output = {}
                    #col_output[get_column_name_for_key(col_key)] = col_value
                    col_output["column-name"] = get_column_name_for_key(col_key)
                    col_output["column-value"] = col_value
                    row_output.append(col_output)
                output["distances"].append(row_output)

        return output    

    def __getstate__(self):
        """ Used by jsonpickle to state of class to output """
        return self._get_state()

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_dict(node._get_state())

class MeasureOutput(FormatOutput):

    def __init__(self, output_config:dict):

        super().__init__(output_config)

        #template_text_file = output_config.get("template-text-file")

        #self.templated_texts = utils.load_yaml.yaml_file_to_dict(template_text_file).get("output-texts")

        self.measures = []

    def get_measure_metric(self) -> str:
        
        total_count = 0
        total_distances = 0
        for measurement in self.measures:
            total_count = total_count + measurement.count
            total_distances = total_distances + len(measurement.distances)
        return "{0:.0%}".format(total_distances/total_count)

    def getMeasureDetails(self):

        details = {}
        details["measure-metric"] = self.get_measure_metric()
        details["measurements"] = self.measures

        return details

    def _get_state(self):

        #details = {}
        #details["measure-metric"] = self.get_measure_metric()
        #details["measurements"] = self.measures
        self.details = self.getMeasureDetails()

        output = super()._get_state()

        return output

    def addMeasure(self, measurement:Measurement):
        self.measures.append(measurement)

    # def getSuccess(self, text_key:str, template_values:dict) -> dict:

    #     success_text = env.from_string(self.templated_texts.get(text_key)).render(template_values)

    #     return self._getOutput("Success", success_text, template_values["tm_version"])

    # def getError(self, text_key:str, template_values:dict) -> dict:

    #     error_text = env.from_string(self.templated_texts.get(text_key)).render(template_values)

    #     return self._getOutput("Error", error_text)

    def __getstate__(self):
        """ Used by jsonpickle to state of class to output """
        return self._get_state()

    def tojson(self):
        return jsonpickle.encode(self, unpicklable=False)