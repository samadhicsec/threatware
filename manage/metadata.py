#!/usr/bin/env python3
"""
Classes to manipulate for threat model metadata
"""
import logging
from pathlib import Path
from data.key import KeySerialiseType, key as Key
from utils import keymaster, match, tags, load_yaml
from utils.load_yaml import yaml_register_class
from data import find
from utils.error import ManageError
from manage.manage_storage import ThreatModelStorage

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

class MetadataIndexEntry:
    """
    This class stores the index metadata associated to a version of the threat model.  
    
    Its purpose is to hold sufficient data to determine if a threat model is Approved (and to identify that threat model). 
    """

    def __init__(self, config:dict, entry:dict):
        yaml_register_class(MetadataIndexEntry)

        self.approvedStatus = config.get("approved-status", "Approved")
        self.draftStatus = config.get("draft-status", "Draft")

        self.ID = entry.get("ID", None)
        self.title = entry.get("title", None)
        self.scheme = entry.get("scheme", None)
        self.location = entry.get("location", None)
        self.approved_version = entry.get("approved-version", None)
        self.version_status = entry.get("version-status", None)
        self.approver = entry.get("approver", None)
        self.approved_date = entry.get("approved-date", None)

    def _populate(self, scheme, location, model, version_tag):
        """ 
        This populates using the current version data from the model 
        
        """

        _, ddd_value = find.key_with_tag(model, "document-details-data")
        _, self.title = find.key_with_tag(ddd_value, "document-title")
        _, self.ID = find.key_with_tag(ddd_value, "document-id")
        _, version_tag_value = find.key_with_tag(ddd_value, version_tag)

        self.scheme = scheme
        self.location = location

        _, vhd_value = find.key_with_tag(model, "version-history-data")
        versions = find.keys_with_tag(vhd_value, "row-identifier")
        
        # If the version value is empty then there will be no match in the version history table
        if not match.is_empty(version_tag_value):
            for version_key, version_value in versions:
                if match.equals(version_tag_value, version_value):
                    version_row = version_key.getProperty("row")
                    self.version_status = find.key_with_tag(version_row, "version-status")[1]
                    self.approver = find.key_with_tag(version_row, "version-approver")[1]
                    self.approved_date = find.key_with_tag(version_row, "version-approved-date")[1]
                    break

            if self.isApproved():
                self.approved_version = version_tag_value

        return version_tag_value

    def createCurrentVersionEntryFromModel(self, scheme, location, model):
        """ 
        This populates using the current version data from the model 
        
        """

        return self._populate(scheme, location, model, "current-version")

    def createApprovedVersionEntryFromModel(self, scheme, location, model):
        """ 
        This populates using the approved version data from the model 
        
        """

        return self._populate(scheme, location, model, "approved-version")

    def isApproved(self) -> bool:
        """ An entry is considered approved if:
             - status is (localised) 'Approved'
             - approver is set
             - approved-date is set
        """
        if match.equals(self.version_status, self.approvedStatus)  and \
           self.approver is not None                       and \
           self.approved_date is not None:
            return True

        return False

    def hasApproval(self) ->  bool:
        """ Return true if an approver name and approved date exists for the threat model """
        if self.approver is not None and self.approved_date is not None:
            return True
        else:
            return False

    def stripApproval(self):

        self.approved_version = ""
        self.version_status = self.draftStatus
        self.approver = ""
        self.approved_date = ""

    def versionStatus(self) -> str:
        return self.version_status

    def get_state(self):
        return self._get_state()

    def _get_state(self):
        output = {}
        output["ID"] = self.ID
        output["title"] = self.title
        output["scheme"] = self.scheme
        output["location"] = self.location
        output["approved-version"] = self.approved_version
        output["version-status"] = self.version_status
        output["approver"] = self.approver
        output["approved-date"] = self.approved_date

        return output

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_dict(node._get_state())   


class ThreatModelVersionMetaData:
    """
    This class stores the metadata associated to a version of the threat model.  
    
    It could be any data in the threat model (tags are used to determine what data) and isn't necessarily sufficient data to determine if a threat model is Approved. 
    """
    def __init__(self, config = {}) -> None:
        yaml_register_class(ThreatModelVersionMetaData)

        self.version_meta_tag_prefix = config.get("version-meta-tag-prefix", "version-meta")
        self.version_meta = {}
        
        self.version = None
        
    def fromModel(self, scheme, location, model):

        # Find all the keys prefixed with tag "version-meta"
        for value_key, value_data in find.keys_with_tag_matching_regex(model, "^" + self.version_meta_tag_prefix):
            if value_data is not None:
                # Get the full tag that matches
                for tag in value_key.getTags():
                    if match.starts_ends(tag, self.version_meta_tag_prefix, ""):
                        if match.equals(tag, self.version_meta_tag_prefix):
                            self.version_meta[value_key.name] = value_data
                        else:
                            # meta data will only include a subset of the tagged data
                            if isinstance(value_data, list):
                                tag_prefix, tag_data_tag_name, tag_field_tag_name, tag_comparison = tags.get_quad_tag_parts(tag)
                                data_model_key, data_model_value = find.key_with_tag(model, tag_data_tag_name)
                                data_key, data_value = find.key_with_tag(data_model_value, tag_field_tag_name)
                                if len(value_data) > 0:
                                    row_identifier = keymaster.get_row_identifier_for_key(list(value_data[0].keys())[0])
                                    for row_dict in value_data:
                                        if match.equals(row_dict[row_identifier], data_value):
                                            self.version = data_value
                                            self.version_meta = self.version_meta | row_dict

        self.version_meta = self.version_meta | {"scheme":scheme, "location":location}

    def fromDict(self, version:str, meta_dict:dict) -> None:

        self.version = version
        self.version_meta = meta_dict

    def _get_state(self):
        return self.version_meta

    def __getstate__(self):
        """ Used by jsonpickle to state of class to output """
        return self._get_state()

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_dict(node._get_state())


class IndexMetaData:
    """
    Stores all MetadataIndexEntry for all versions of a threat model.

    Can retrieve entries, update new entries and persist all entries
    """

    def __init__(self, config:dict, storage) -> None:
        yaml_register_class(IndexMetaData)

        self.config = config
        self.index_filename = config.get("index-filename", "threatmodels.yaml")
        self.storage = storage

        self._load_index()

    def _load_index(self):

        self.indexdata = {}

        if (threatmodels := self.storage.load_yaml([], Path(self.storage.repodir).joinpath(self.index_filename))) is not None:
            for TMindex_list_entry in threatmodels.get("threatmodels", []):
                mdie = MetadataIndexEntry(self.config, TMindex_list_entry)
                self.indexdata[mdie.ID] = mdie
        else:
            logger.warning(f"No {self.index_filename} was loaded.  This should only happen when the metadata repo is first created and is empty.")

    def getIndexEntry(self, ID:str) -> MetadataIndexEntry:
        return self.indexdata.get(ID, None)

    def getIndexEntryByLocation(self, location:str) -> MetadataIndexEntry:

        location_based_index = {entry.location:entry for entry in self.indexdata.values()}

        return location_based_index.get(location, None)

    def getIDByLocation(self, location:str) -> str:

        location_based_index = {entry.location:ID for ID, entry in self.indexdata.items()}

        return location_based_index.get(location, None)

    def createIndexEntryID(self, IDprefix:str):

        #last_entry_ID = list(self.indexdata.keys())[-1]

        try:
            entry_ID_numbers = [int(entryID.split(".")[-1]) for entryID in self.indexdata.keys()]

            #last_ID_num = int(last_entry_ID.split(".")[-1])
        except ValueError as ex:
            logger.error(f"Could not convert last part of an ID to an int")
            raise ManageError("internal-error", {})

        if len(entry_ID_numbers) > 0:
            last_ID_num = sorted(entry_ID_numbers)[-1]
        else:
            last_ID_num = 0

        if not IDprefix.endswith("."):
            IDprefix = IDprefix + "."

        return IDprefix + str(last_ID_num + 1)


    def setIndexEntry(self, ID:str, entry:MetadataIndexEntry):
        self.indexdata[ID] = entry

    def __enter__(self):

        self.storage.__enter__()

        self._load_index()

        return self

    def _write_index(self):
        
        # We never want to serialise Keys in any format other than without tag/properties
        current_key_serialise = Key.serialise_type
        Key.serialise_type = KeySerialiseType.NO_TAGS_PROPERTIES

        load_yaml.class_to_yaml_file(self, Path(self.storage.repodir).joinpath(self.index_filename))

        Key.serialise_type = current_key_serialise

    def persist(self):
        """ Writes any changes to the underlying storage layer """

        self._write_index()

    def __exit__(self, exc_type, exc_value, traceback):

        if exc_type is None:
            self._write_index()

        # This is going to commit any changes
        self.storage.__exit__(exc_type, exc_value, traceback)

    def _get_state(self):

        output = {}
        output["threatmodels"] = [value for value in self.indexdata.values()]

        return output

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_dict(node._get_state())

class ThreatModelMetaData:
    """
    Stores all ThreatModelVersionMetaData for all versions of a threat model

    Can retrieve entries, update new entries and persist all entries.  It also sets a version as the approved version.
    """

    def __init__(self, config:dict, storage:ThreatModelStorage, schemeID:str = None, location:str = None) -> None:
        yaml_register_class(ThreatModelMetaData)

        self.index = IndexMetaData(config, storage)

        self.metadata_filename = config.get("metadata-filename", "metadata.yaml")
        self.storage = storage
        self.approvedStatus = config.get("approved-status", "Approved")
        self.write_plain_model = config.get("write-plain-model", True)

        self.index._load_index()

        self.ID = self.index.getIDByLocation(location)
        if self.ID is None:
            logger.error(f"No ID was found in the metadata for a threat model with location '{location}'")
            raise ManageError("no-ID-in-metadata", {"location":location})

        self._set_empty()

        self._load_metadata() 

    def _set_empty(self):
        self.IDmetadata = {}
        self.IDmetadata["ID"] = self.ID
        self.IDmetadata["versions"] = {}

    def setModel(self, version:str, model:dict):
        self.model_version = version
        self.model = model

    def _load_metadata(self):

        # If the directory or file don't exist, that's fine as they'll be created when we write out changes.

        if (contents_dict := self.storage.load_yaml([], Path(self.ID).joinpath(self.metadata_filename))) is not None:

            if (tm_metadata := contents_dict.get("threatmodel-metadata", None)) is None:
                logger.error("Could not find key 'threatmodel-metadata'")
                return

            if not match.equals(self.ID, tm_metadata.get("ID", None)):
                logger.error("The 'ID' in the threatmodel metadata file did not match the ID of the threat model")
                return

            for version_key, version_value in tm_metadata.get("versions", {}).items():
                tmvm = ThreatModelVersionMetaData()
                tmvm.fromDict(version_key, version_value)
                self.IDmetadata["versions"][version_key] = tmvm

    def _write_metadata(self):
        
        # We never want to serialise Keys in any format other than without tag/properties
        current_key_serialise = Key.serialise_type
        Key.serialise_type = KeySerialiseType.NO_TAGS_PROPERTIES

        self.storage.write_yaml(Path(self.ID).joinpath(self.metadata_filename), self)

        Key.serialise_type = current_key_serialise
        

    def _write_model(self):
        """ Optionally, writes 2 versions of the model file, one that can be deserialised, and one that is human readable (plain) """
        Key.serialise_type = KeySerialiseType.TAGS_PROPERTIES
        #self.storage.write_yaml([Key], Path(self.ID).joinpath(self.model_version + ".yaml"), self.model)
        self.storage.write_yaml(Path(self.ID).joinpath(self.model_version + ".yaml"), self.model)

        if self.write_plain_model:
            Key.serialise_type = KeySerialiseType.NO_TAGS_PROPERTIES
            #self.storage.write_yaml([Key], Path(self.ID).joinpath(self.model_version + ".plain.yaml"), self.model)
            self.storage.write_yaml(Path(self.ID).joinpath(self.model_version + ".plain.yaml"), self.model)

    def load_model(self, version:str):

        Key.serialise_type = KeySerialiseType.TAGS_PROPERTIES
        self.model = self.storage.load_yaml([Key], Path(self.ID).joinpath(version + ".yaml"))
        if self.model is None:
            logger.error(f"Unable to load model for version '{version}'")
        else:
            self.model_version = version

        return self.model
            

    def setApprovedVersion(self, ID:str, current_version:str, currentModelIndexEntry:MetadataIndexEntry, approved_version:str, approvedModelIndexEntry:MetadataIndexEntry, approved_version_metadata:ThreatModelVersionMetaData):

        currentMetadataIndexEntry = self.index.getIndexEntry(ID)

        if currentMetadataIndexEntry is None:
            # The TM has either not been 'create'd, or the output of the 'create' action has not been merged to the default branch
            raise ManageError("cant-submit-not-in-metadata-index", {"ID":ID})

        # Several scenarios to consider
        # Common legitimate update scenario by author
        # model cur ver = 1.1 (not approved in model)
        # model app ver = 1.0 (approved in model)
        # index app ver = 1.0

        # Common legitimate update scenario by approver
        # model cur ver = 1.1 (approved in model)
        # model app ver = 1.1 (approved in model)
        # index app ver = 1.0

        # Common mistake update scenario by approver - forgot to update approved version in model
        # model cur ver = 1.1 (approved in model)
        # model app ver = 1.0 (approved in model)
        # index app ver = 1.0
    
        # Common mistake update scenario by author/approver - tried to update existing approved version
        # model cur ver = 1.1 (approved in model)
        # model app ver = 1.1 (approved in model)
        # index app ver = 1.1

        if currentModelIndexEntry.isApproved() and approvedModelIndexEntry.isApproved():
            if not match.equals(currentModelIndexEntry.approved_version, approvedModelIndexEntry.approved_version):
                # In the model, the current version is approved, and is different to the approved version from the model
                logger.error(f"Submitted Threat Model has different current and approved versions, but both are approved.  If the current version is approved it must match the approved version.")
                raise ManageError("current-approved-mismatched-version", {"ID":ID, "current_version":currentModelIndexEntry.approved_version, "approved_version":approvedModelIndexEntry.approved_version})
            elif match.equals(approvedModelIndexEntry.approved_version, currentMetadataIndexEntry.approved_version):
                # The model is correct, but we the index says the version is already approved
                logger.error(f"Submitted Threat Model approved version in the document is the same as the officially recorded approved version.  Submitting new versions requires a version increase.")
                raise ManageError("cant-update-approved-version", {"ID":ID, "approved_version":currentMetadataIndexEntry.approved_version})
        elif match.equals(current_version, approved_version) and not approvedModelIndexEntry.isApproved():
            # Often the only reason the TM is not considered approved is someone forgot to change the status
            if approvedModelIndexEntry.hasApproval() and not match.equals(self.approvedStatus, approvedModelIndexEntry.versionStatus()):
                logger.error(f"Submitted Threat Model has been approved, but status is not set to '{self.approvedStatus}'.")
                raise ManageError("status-not-approved", {"ID":ID, "approved_version":approved_version, "approved_status":self.approvedStatus})

            # The current version = approved version, but it's not approved.  Probably forgot to approve the version in the version history table
            logger.error(f"Submitted Threat Model approved version in the document is not marked as approved in the Version History table.")
            raise ManageError("approved-version-not-approved", {"ID":ID, "approved_version":approved_version})

        elif not match.equals(current_version, approved_version) and currentModelIndexEntry.isApproved():
            # The current version != approved version, but current version approved.  Probably forgot to increase the approved version the version in the version history table
            logger.error(f"Submitted Threat Model current version is approved, but differs from the approved version.")
            raise ManageError("approved-version-not-updated", {"ID":ID, "current_version":current_version, "approved_version":approved_version})


        self.index.setIndexEntry(ID, currentModelIndexEntry)

        self.IDmetadata["versions"][approved_version] = approved_version_metadata

    def persist(self):
        """ Writes any changes to the underlying storage layer """

        self.index._write_index()
        self._write_metadata()
        self._write_model()


    def getVersion(self, versionID:str) -> ThreatModelVersionMetaData:
        
        return self.IDmetadata.get(versionID, None)

    def _get_state(self):

        output = {}
        output["threatmodel-metadata"] = self.IDmetadata

        return output

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_dict(node._get_state())