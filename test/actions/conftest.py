#!/usr/bin/env python3

import pytest
from pathlib import Path
from ruamel.yaml import YAML
import data.key
import utils.load_yaml
from verifiers.verifiers import Verifiers

# Turn a normal dict with strings for keys, into a dict with data.key.key for keys
def getKeycopy(sourcedict, destdict):

    for keyentry, valueentry in sourcedict.items():
        dictkey = data.key.key(keyentry)

        if isinstance(valueentry, dict):
            valuedict = {}
            getKeycopy(valueentry, valuedict)    
            destdict[dictkey] = valuedict
        elif isinstance(valueentry, list):
            valuelist = []
            for listentry in valueentry:
                # Every list entry is a dict
                valuedict = {}
                getKeycopy(listentry, valuedict)
                valuelist.append(valuedict)
            destdict[dictkey] = valuelist
        else:
            destdict[dictkey] = valueentry
            
    return 

@pytest.fixture(autouse=True)
def example_threat_model():

    modelyaml = """
    model-details:
      document-ID: CMP1234
      document-name: example threat model
      current-version: "1.0"
      approved-version: "1.0"
    components:
      details:
        - name: Component name 1
          location: Location 1
          purpose: Purpose 1
          in-scope: Yes
          tech-stack: tech stack 1
        - name: Component name 2
          location: Location 2
          purpose: Purpose 2
          in-scope: No
          tech-stack: 
      access-control:
        - component: Component name 1
          identity: identity 1
          authentication-method: authn 1
          authorisation-method: authz 1
        - component: Component name 1
          identity: identity 2
          authentication-method: authn 2
          authorisation-method: authz 2
    assets:
      functional:
        - type: type 1
          name: Functional name 1
          description: asset description 1
          security-impacts:
            - impact-type: Confidentiality
              description: Description impact 1
          locations:
            - location: asset location 1
        - type: type 2
          name: Functional name 2
          description: asset description 2
          security-impacts:
            - impact-type: Integrity
              description: Description impact 2
          locations:
            - location: asset location 2
      technical:
        - type: tech type 1
          name: tech name 1
          description: tech description 1
          security-impacts:
            - impact-type: Confidentiality
              description: tech impact 1
          locations:
            - location: known location 1
          functional-assets-affected:
            - functional-asset-affected: Functional name 1
        - type: tech type 2
          name: tech name 2
          description: tech description 2
          security-impacts:
            - impact-type: Integrity
              description: tech impact 2
          locations:
            - location: Component name 2
          functional-assets-affected:
            - functional-asset-affected: Functional name 2
    threats-and-controls:
      - components:
          - component: Component name 1
        assets:
          - asset: Functional name 1
        threat-description: threat desc 1
        existing-controls:
          - control: existing control 1
        tickets:
          - ticket: '1234'
      - components:
          - component: Component name 1
        assets:
          - asset: type 1
        threat-description: threat desc 1
        existing-controls:
          - control: existing control 1
        tickets:
          - ticket: '1234'
      - components:
          - component: Component name 1
        assets:
          - asset: All assets stored in asset location 1
        threat-description: threat desc 1
        existing-controls:
          - control: existing control 1
        tickets:
          - ticket: '1234'
      - components:
          - component: Component name 1
        assets:
          - asset: Functional name 2
        threat-description: threat desc 2
        existing-controls:
          - control: existing control 1
        tickets:
      - components:
          - component: Component name 1
        assets:
          - asset: tech name 1
        threat-description: threat desc 3
        existing-controls:
          - control: existing control 2
        tickets:
          - ticket: '5678'
      - components:
          - component: Component name 1
        assets:
          - asset: tech name 2
        threat-description: threat desc 4
        existing-controls:
          - control: existing control 3
        tickets:
          - ticket: '9101'
    """

    yaml=YAML(typ='safe')
    modeldict = yaml.load(modelyaml)

    modelKeydict = {}
    getKeycopy(modeldict, modelKeydict)
    
    for key_entry, value_entry in modelKeydict.items():
        key_entry.addProperty("section", key_entry.name)
        key_entry.addProperty("value", value_entry)
        #print(key_entry.name)
        if key_entry.name == "components" or key_entry.name == "assets":
            for subkey_entry, subvalue_entry in value_entry.items():
                #print(subkey_entry.name)
                subkey_entry.addProperty("section", subkey_entry.name)
                subkey_entry.addProperty("value", subvalue_entry)

    #print(modeldict)
    #print()
    #print(modelKeydict)

    error_config_str = """
                      default-severity: error
                      location-text: "{}"
                      entry-text: "For entry with '{}' equal to '{}'"
                      """
    error_config = utils.load_yaml.yaml_str_to_dict(error_config_str)

    verifiers = Verifiers({"errors":error_config})

    # Add tags to dict keys
    verifiers.assign_key_tags(modelKeydict)
    # Add row identifiers
    verifiers.assign_row_identifiers(None, modelKeydict)
    
    #for listentry in modelKeydict["components"]["details"]:
    #    namevalue = listentry.pop("name")
    #    listentry[data.key.key("name", ["globally-unique", "row-identifier"])] = namevalue

    return modelKeydict

if __name__ == "__main__":
  example_threat_model()