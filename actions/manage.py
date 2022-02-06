#!/usr/bin/env python3
"""
Manage a threat model
"""

from curses import meta
import logging
from pathlib import Path
from utils.error import ManageError
from utils.model import assign_row_identifiers
from utils import match
from manage import manage_config
from manage.manage_output import ManageOutput
from manage.metadata import IndexMetaData, ThreatModelMetaData
from manage.metadata import MetadataIndexEntry, ThreatModelVersionMetaData
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


def indexdata(config:dict, ID:str) -> MetadataIndexEntry:
    """ Given a document ID retrieve the metadata associated with the threat model """

    if ID is None:
        logger.error(f"An ID must be provided")
        raise ManageError("internal-error", {})

    with IndexStorage(config.get("storage", {}), False) as storage:
    
        index = IndexMetaData(config.get("metadata", {}), storage)
        
        entry = index.getIndexEntry(ID)
        if entry is None:
            logger.error(f"An entry with ID '{ID}' was not found")
            raise ManageError("no-index-ID", {"ID":ID})

        return entry
            

def create(config:dict, IDprefix:str, scheme:str, location:str):
    """ Given a document location and id format, generate the unique document ID, and store and return the result """

    if IDprefix is None or scheme is None or location is None:
        logger.error(f"An ID prefix, scheme and location, must all be provided")
        raise ManageError("internal-error", {})

    with IndexStorage(config.get("storage", {})) as storage:

        index = IndexMetaData(config.get("metadata", {}), storage)

        entry = index.getIndexEntryByLocation(scheme, location)
        if entry is not None:
            logger.info(f"Cannot create ID for threat model in location '{location}' as that location is used by threat model '{entry.ID}'")
            raise ManageError("index-entry-exists", {"scheme":scheme, "location":location, "ID":entry.ID})
    
        new_ID = index.createIndexEntryID(IDprefix)

        new_entry = MetadataIndexEntry()
        new_entry.ID = new_ID
        new_entry.scheme = scheme
        new_entry.location = location

        index.setIndexEntry(new_ID, new_entry)


# def submit_old(config:dict, output:ManageOutput, location:str, schemeID:str, model:dict):
#     """ 
#     Submit the threat model for approval 
    
#     Given config and a threat model ID, check to see this TM has been submitted before, and if not create dir.  Otherwise, get the TM, get the version,
#     and metadata, and create/update metadata for that version.
#     """
#     try:
#         assign_row_identifiers(model)

#         # Parse for complete metadata to store
#         tmvmd = ThreatModelVersionMetaData()
#         docID, current_version, approved_version = tmvmd.fromModel(schemeID, location, model)

#         storage = ThreatModelStorage(config.get("storage", {}), docID)

#         with ThreatModelMetaData(config.get("metadata", {}), storage, docID) as tm_metadata:                
#             # Add/update the metadata related to this version
#             tm_metadata.setApprovedVersion(docID, tmvmd)

#     except ManageError as error:
#         return output.getError(error.text_key, error.template_values)

#     if match.equals(current_version, approved_version):
#         return output.getSuccess("success-approver", {"ID":docID, "tm_version":tmvmd})
#     else:
#         return output.getSuccess("success-submitter", {"ID":docID, "tm_version":tmvmd})


def submit(config:dict, output:ManageOutput, location:str, schemeID:str, model:dict):
    """ 
    Submit the threat model for approval 
    
    Given config and a threat model ID, check to see this TM has been submitted before, and if not create dir.  Otherwise, get the TM, get the version,
    and metadata, and create/update metadata for that version.
    """
    try:
        assign_row_identifiers(model)

        # Parse for the index metadata to store
        imd = MetadataIndexEntry({})
        current_version, approved_version = imd.fromModel(schemeID, location, model)

        # Parse for complete metadata to store
        tmvmd = ThreatModelVersionMetaData()
        tmvmd.fromModel(schemeID, location, model)

        with ThreatModelStorage(config.get("storage", {}), imd.ID) as storage:

            tm_metadata = ThreatModelMetaData(config.get("metadata", {}), storage, imd.ID)

            # Add/update the metadata related to this version
            tm_metadata.setApprovedVersion(imd.ID, imd, tmvmd)

            tm_metadata.persist()

    except ManageError as error:
        return output.getError(error.text_key, error.template_values)

    if match.equals(current_version, approved_version):
        return output.getSuccess("success-approver", {"ID":imd.ID, "tm_version":tmvmd})
    else:
        return output.getSuccess("success-submitter", {"ID":imd.ID, "tm_version":tmvmd})

def check():
    """ Given a document, check if the threat model has changed enough from teh approved version as to require re-approval """