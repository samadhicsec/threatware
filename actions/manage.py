#!/usr/bin/env python3
"""
Manage a threat model
"""

import logging
from datetime import datetime
from dateutil.parser import parse
from utils.output import FormatOutput
from utils.error import ManageError, StorageError
from utils.model import assign_row_identifiers, assign_parent_keys
from data import find
from utils import match
from manage import manage_config
from manage.metadata import IndexMetaData, ThreatModelMetaData
from manage.metadata import MetadataIndexEntry, ThreatModelVersionMetaData
from manage.manage_storage import IndexStorage
from manage.manage_storage import ThreatModelStorage
from actions import measure

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))


def config():

    return manage_config.config()

def _output(config:dict):

    return FormatOutput(config.get("output", {}))


def indexdata(config:dict, execution_env, ID:str) -> MetadataIndexEntry:
    """ Given a document ID retrieve the metadata associated with the threat model """

    output = _output(config)

    try: 
        if ID is None:
            logger.error(f"An ID must be provided")
            raise ManageError("internal-error", {})

        with IndexStorage(config.get("storage", {}), execution_env, False) as storage:
        
            index = IndexMetaData(config.get("metadata", {}), storage)
            
            entry = index.getIndexEntry(ID)
            if entry is None:
                logger.error(f"An entry with ID '{ID}' was not found")
                raise ManageError("no-index-ID", {"ID":ID})

            output.setSuccess("success-indexdata", {"ID":ID}, entry)
    
    except StorageError as error:
        output.setError(error.text_key, error.template_values)
    except ManageError as error:
        output.setError(error.text_key, error.template_values)

    return output


def create(config:dict, execution_env, IDprefix:str, scheme:str, location:str):
    """ Given a document location and id format, generate the unique document ID, and store and return the result """

    output = _output(config)

    try:
        if IDprefix is None or scheme is None or location is None:
            logger.error(f"An ID prefix, scheme and location, must all be provided")
            raise ManageError("internal-error", {})

        with IndexStorage(config.get("storage", {}), execution_env, persist_changes=True, output_texts=output.templated_texts) as storage:

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

        output.setSuccess("success-create", {}, new_entry)

    except StorageError as error:
        output.setError(error.text_key, error.template_values)
    except ManageError as error:
        output.setError(error.text_key, error.template_values)

    return output


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


def submit(config:dict, execution_env, location:str, schemeID:str, model:dict):
    """ 
    Submit the threat model for approval 
    
    Given config and a threat model ID, check to see this TM has been submitted before, and if not create dir.  Otherwise, get the TM, get the version,
    and metadata, and create/update metadata for that version.
    """

    output = _output(config)

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

        with ThreatModelStorage(config.get("storage", {}), execution_env, imdCurrent.ID, persist_changes=True, output_texts=output.templated_texts) as storage:

            tm_metadata = ThreatModelMetaData(config.get("metadata", {}), storage, imdCurrent.ID)

            # Add/update the metadata related to this version
            tm_metadata.setApprovedVersion(imdCurrent.ID, imdCurrent, imdApproved, tmvmd)

            # The model will be recorded as well
            tm_metadata.setModel(approved_version, model)

            tm_metadata.persist()

        if match.equals(current_version, approved_version):
            output.setSuccess("success-approver", {"ID":imdCurrent.ID}, tmvmd)
        else:
            output.setSuccess("success-submitter", {"ID":imdCurrent.ID}, tmvmd)

    except StorageError as error:
        output.setError(error.text_key, error.template_values)
    except ManageError as error:
        output.setError(error.text_key, error.template_values)

    return output

def check(config:dict, execution_env, location:str, schemeID:str, model:dict, measure_config:dict, distance):
    """ Given a document, check if the threat model has changed enough from the approved version as to require re-approval """

    output = _output(config)

    approval_expiry_days = config["check"]["approval-expiry-days"]

    try:
        assign_row_identifiers(model)
        assign_parent_keys(model)

        # Get the Doc ID
        if (docIDtuple := find.key_with_tag(model, "document-id")) is None:
            logger.error(f"No document ID was found for the threat model at location {location}")
            raise ManageError("no-document-id", {"location":location})
        _, docID = docIDtuple

        with ThreatModelStorage(config.get("storage", {}), execution_env, docID, persist_changes=False) as storage:

            # Get the index data and metadata for the ID
            tm_metadata = ThreatModelMetaData(config.get("metadata", {}), storage, docID)

            indexentry = tm_metadata.index.getIndexEntryByLocation(schemeID, location)

            # Check if there is an approved version
            if indexentry is None or (approved_version := indexentry.approved_version) is None or indexentry.approved_date is None:
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
            #measure_config = measure.config(config.translator)
            # Update the tag prefix to not collide with any other measures configured
            measure_config["measure-tag"]["prefix"] = "check"
            #measure_output = measure.output(measure_config)
            #measure.distance(measure_config, measure_output, model, approved_model)
            measure_output = distance(measure_config, model, approved_model)

            # Are there new threats in the current TM
            # Are there new controls in the current TM
            meaure_metric = measure_output.get_measure_metric()
            if meaure_metric != "0%":
                # An approval is required
                output.setInformation("approval-required", {}, measure_output.getMeasureDetails())
            else:
                # An approval is not required
                output.setInformation("no-approval-required", {})

    except StorageError as error:
        output.setError(error.text_key, error.template_values)
    except ManageError as error:
        output.setError(error.text_key, error.template_values)

    return output
    

    

    
    
    

    