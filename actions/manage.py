#!/usr/bin/env python3
"""
Manage a threat model
"""

import logging
from pathlib import Path
from utils.error import ManageError
from utils.model import assign_row_identifiers
from manage import manage_config
from manage.manage_output import ManageOutput
from manage.metadata import ThreatModelMetaData
from manage.metadata import ThreatModelVersionMetaData
from manage.storage.gitrepo import IndexStorage
from manage.storage.gitrepo import ThreatModelStorage

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

MANAGE_CONFIG_YAML = "manage_config.yaml"
MANAGE_CONFIG_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(MANAGE_CONFIG_YAML))

def config():

    return manage_config.config()

def output(config:dict):

    return ManageOutput(config.get("output", {}))


def metadata(config:dict, ID:str, location:str):
    """ Given a document ID or a location retrieve the metadata associated with the threat model """

    metadata = IndexStorage(config)

    if ID is not None:    
        entry = metadata.getIndexEntry(ID)
        if entry is not None:
            return entry
        else:
            return f"No management data exists for {ID}"
    elif location is not None:
        entry = metadata.getIndexEntryByLocation(location)
        if entry is not None:
            return entry
        else:
            return f"No management data exists for {location}"
    else:
        return f"Either an ID or location must be provided"

def create(config:dict, IDprefix:str, location:str):
    """ Given a document location and id format, generate the unique document ID, and store and return the result """

    with IndexStorage(config) as metadata:
        entry = metadata.getIndexEntryByLocation(location)
        if entry is not None:
            logger.info(f"Cannot create ID for threat model in location '{location}' as that location is used by threat model '{entry.ID}'")
            return f"Cannot create ID for threat model in location '{location}' as that location is used by threat model '{entry.ID}'"
    


def submit(config:dict, output:ManageOutput, location:str, scheme:dict, model:dict):
    """ 
    Submit the threat model for approval 
    
    Given config and a threat model ID, check to see this TM has been submitted before, and if not create dir.  Otherwise, get the TM, get the version,
    and metadata, and create/update metadata for that version.
    """
    try:
        assign_row_identifiers(model)

        # Parse for complete metadata to store
        tmvmd = ThreatModelVersionMetaData()
        docID = tmvmd.fromModel(location, model)

        storage = ThreatModelStorage(config.get("storage", {}), docID)

        with ThreatModelMetaData(config.get("metadata", {}), storage, docID) as tm_metadata:
                
            # Get the approved version of the TM
            #tm_index_entry = tm_metadata.getIndexEntry(ID)

            #if tm_index_entry is None:
            #    logger.error(f"Could not find metadata index entry for ID '{ID}'")
            #    return output.tojson(output.getError("no-index-ID", {"ID":ID}))

            
            # Make sure the submitted version is not the approved version
            #if tm_index_entry.approved_version == tmvmd.version:
            #    logger.error(f"Version of submitted threat model '{tmvmd.version}' is not allowed to match approved version of threat model '{tm_index_entry.approved_version}'")
            #    return output.tojson(output.getError("cant-update-approved-version", {"ID":ID, "approved-version":tm_index_entry.approved_version}))

            # Get the submitted version


            # Add/update the metadata related to this version
            tm_metadata.setApprovedVersion(docID, tmvmd)

            # Finish submission
            tm_metadata.can_commit = True

            #TODO output different messages with 'Approved Version' != 'Current Version' -> tell user change submitted, but needs approval, whereas
            # 'Approved Version' == 'Current Version' this is a message to the approver

    except ManageError as error:
        return output.getError(error.text_key, error.template_values)

    return output.getSuccess("success", {"ID":docID, "tm_version":tmvmd})

def check():
    """ Given a document, check if the threat model has changed enough from teh approved version as to require re-approval """