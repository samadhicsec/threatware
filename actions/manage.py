#!/usr/bin/env python3
"""
Manage a threat model
"""

import logging
from datetime import datetime
from dateutil.parser import parse
from utils.error import ManageError
from utils.model import assign_row_identifiers, assign_parent_keys
from data import find
from utils import match
from manage import manage_config
from manage.manage_output import ManageOutput
from manage.metadata import IndexMetaData, ThreatModelMetaData
from manage.metadata import MetadataIndexEntry, ThreatModelVersionMetaData
from manage.storage.gitrepo import IndexStorage
from manage.storage.gitrepo import ThreatModelStorage
from actions import measure

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))


def config(translator):

    return manage_config.config(translator)

def output(config:dict):

    return ManageOutput(config.get("output", {}))


def indexdata(config:dict, output:ManageOutput, ID:str) -> MetadataIndexEntry:
    """ Given a document ID retrieve the metadata associated with the threat model """

    try: 
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
    
    except ManageError as error:
        return output.getError(error.text_key, error.template_values)


def create(config:dict, output:ManageOutput, IDprefix:str, scheme:str, location:str):
    """ Given a document location and id format, generate the unique document ID, and store and return the result """

    try:
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

            new_entry = MetadataIndexEntry({})
            new_entry.ID = new_ID
            new_entry.scheme = scheme
            new_entry.location = location

            index.setIndexEntry(new_ID, new_entry)

            index.persist()

            return new_entry

    except ManageError as error:
        return output.getError(error.text_key, error.template_values)


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
        imdCurrent = MetadataIndexEntry({})
        current_version = imdCurrent.createCurrentVersionEntryFromModel(schemeID, location, model)

        imdApproved = MetadataIndexEntry({})
        approved_version = imdApproved.createApprovedVersionEntryFromModel(schemeID, location, model)

        # Parse for complete metadata to store
        tmvmd = ThreatModelVersionMetaData()
        tmvmd.fromModel(schemeID, location, model)

        with ThreatModelStorage(config.get("storage", {}), imdCurrent.ID) as storage:

            tm_metadata = ThreatModelMetaData(config.get("metadata", {}), storage, imdCurrent.ID)

            # Add/update the metadata related to this version
            tm_metadata.setApprovedVersion(imdCurrent.ID, imdCurrent, imdApproved, tmvmd)

            # The model will be recorded as well
            tm_metadata.setModel(approved_version, model)

            tm_metadata.persist()

    except ManageError as error:
        return output.getError(error.text_key, error.template_values)

    if match.equals(current_version, approved_version):
        return output.getSuccess("success-approver", {"ID":imdCurrent.ID, "tm_version":tmvmd})
    else:
        return output.getSuccess("success-submitter", {"ID":imdCurrent.ID, "tm_version":tmvmd})

def check(translator, config:dict, output:ManageOutput, location:str, schemeID:str, model:dict):
    """ Given a document, check if the threat model has changed enough from the approved version as to require re-approval """

    approval_expiry_days = config["check"]["approval-expiry-days"]

    try:
        assign_row_identifiers(model)
        assign_parent_keys(model)

        # Get the Doc ID
        if (docIDtuple := find.key_with_tag(model, "document-id")) is None:
            logger.error(f"No document ID was found for the threat model at location {location}")
            raise ManageError("no-document-id", {"location":location})
        _, docID = docIDtuple

        with ThreatModelStorage(config.get("storage", {}), docID, persist_changes=False) as storage:

            # Get the index data and metadata for the ID
            tm_metadata = ThreatModelMetaData(config.get("metadata", {}), storage, docID)

            indexentry = tm_metadata.index.getIndexEntryByLocation(schemeID, location)

            # Check if there is an approved version
            if (approved_version := indexentry.approved_version) is None or indexentry.approved_date is None:
                # Need an approval
                raise ManageError("no-approved-version", {})

            # Check if approved version has expired
            if indexentry.approved_date is not None:
                approvedDate = parse(indexentry.approved_date)
                if approvedDate is not None and (datetime.now() - approvedDate).days > approval_expiry_days:
                    raise ManageError("approved-version-expired", {"approval_expiry_days":approval_expiry_days})

            # Get approved version
            if (approved_model := tm_metadata.load_model(approved_version)) is None:
                raise ManageError("approved-version-didnt-load", {})
                      
            # Potentially need to add 'measure' tags in the right place
            
            # Use measure code to find things that don't match between a current TM and the most recent approved version
            measure_config = measure.config(translator)
            # Update the tag prefix to not collide with any other measures configured
            measure_config["measure-tag"]["prefix"] = "check"
            measure_output = measure.output(measure_config)
            measure.distance(measure_config, measure_output, model, approved_model)            

            # Are there new threats in the current TM
            # Are there new controls in the current TM
            meaure_metric = measure_output.get_measure_metric()
            if meaure_metric != "0%":
                # An approval is required
                return output.getInformation("approval-required", {}, measure_output)
            else:
                # An approval is not required
                return output.getInformation("no-approval-required", {})


    except ManageError as error:
        return output.getError(error.text_key, error.template_values)

    

    

    
    
    

    