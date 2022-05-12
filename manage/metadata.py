#!/usr/bin/env python3
"""
Classes to manipulate for threat model metadata
"""
import logging
from pathlib import Path
from data.key import KeySerialiseType, key as Key
from utils import match
from utils import load_yaml
from utils.load_yaml import yaml_register_class
from data import find
from utils.error import ManageError
from manage.manage_storage import IndexStorage
from manage.manage_storage import ThreatModelStorage

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

class MetadataIndexEntry:

    def __init__(self, entry:dict):
        yaml_register_class(MetadataIndexEntry)

        self.ID = entry.get("ID", "")
        self.scheme = entry.get("scheme", "")
        self.location = entry.get("location", "")
        self.approved_version = entry.get("approved-version", "")
        self.approved_date = entry.get("approved-date", "")     

    def _populate(self, scheme, location, model, version_tag):
        """ 
        This populates using the current version data from the model 
        
        """

        _, ddd_value = find.key_with_tag(model, "document-details-data")
        _, id_value = find.key_with_tag(ddd_value, "document-id")
        _, version_tag_value = find.key_with_tag(ddd_value, version_tag)

        if match.is_empty(id_value):
            raise ManageError("empty-id", {})

        self.ID = id_value
        self.scheme = scheme
        self.location = location
        #self.approved_version = current_version_value

        version_approver = None
        version_approved_date = None

        _, vhd_value = find.key_with_tag(model, "version-history-data")
        versions = find.keys_with_tag(vhd_value, "row-identifier")
        
        # If the version value is empty then there will be no match in the version history table
        if not match.is_empty(version_tag_value):
            for version_key, version_value in versions:
                if match.equals(version_tag_value, version_value):
                    version_row = version_key.getProperty("row")
                    version_approver = find.key_with_tag(version_row, "version-approver")[1]
                    version_approved_date = find.key_with_tag(version_row, "version-approved-date")[1]
                    break

            if version_approver is not None and version_approved_date is not None:
                self.approved_version = version_tag_value
                self.approved_date = version_approved_date

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
        """ An entry is considered approved if both the Approved Version and Approved Date fields are set """
        if not match.is_empty(self.approved_version) and not match.is_empty(self.approved_date):
            return True

        return False

    # def fromModel(self, scheme, location, model):
    #     """ 
    #     This extracts approval data dependant on whether approval has been given 
        
    #     approved_version and approved_date are only set if version-approver and version-approved-date have been set
    #     for the document-details-data approved-version value
    #     """

    #     _, ddd_value = find.key_with_tag(model, "document-details-data")
    #     _, id_value = find.key_with_tag(ddd_value, "document-id")
    #     _, current_version_value = find.key_with_tag(ddd_value, "current-version")
    #     _, approved_version_value = find.key_with_tag(ddd_value, "approved-version")

    #     self.ID = id_value
    #     self.scheme = scheme
    #     self.location = location
    #     #self.approved_version = current_version_value

    #     version_approver = None
    #     version_approved_date = None

    #     _, vhd_value = find.key_with_tag(model, "version-history-data")
    #     versions = find.keys_with_tag(vhd_value, "row-identifier")
    #     #match_found = False
    #     for version_key, version_value in versions:
    #         if match.equals(approved_version_value, version_value):
    #             version_row = version_key.getProperty("row")
    #             version_approver = find.key_with_tag(version_row, "version-approver")[1]
    #             version_approved_date = find.key_with_tag(version_row, "version-approved-date")[1]
    #             #match_found = True
    #             break

    #     if version_approver is not None and version_approved_date is not None:
    #         self.approved_version = approved_version_value
    #         self.approved_date = version_approved_date

    #     #if not match_found:
    #     #    logger.error(f"Could not find entry in version history table for threat model approved version '{current_version_value}'")
    #     #    raise ManageError("no-version-history", {"current_version":current_version_value})

    #     return current_version_value, approved_version_value

    def _get_state(self):
        output = {}
        output["ID"] = self.ID
        output["scheme"] = self.scheme
        output["location"] = self.location
        output["approved-version"] = self.approved_version
        output["approved-date"] = self.approved_date

        return output

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_dict(node._get_state())   


class ThreatModelVersionMetaData:
    """ Holds data about a specific version of a threat model """
    def __init__(self) -> None:
        yaml_register_class(ThreatModelVersionMetaData)

        self.doc_title = None
        self.doc_scheme = None
        self.doc_location = None
        self.version = None
        self.version_row = None
        self.version_author = None
        self.version_author_role = None
        self.version_date = None
        self.version_changelog = None
        self.version_status = None
        self.version_approver = None
        self.version_approved_date = None

    def fromModel(self, scheme, location, model):

        _, ddd_value = find.key_with_tag(model, "document-details-data")
        _, id_value = find.key_with_tag(ddd_value, "document-id")
        _, title_value = find.key_with_tag(ddd_value, "document-title")
        _, current_version_value = find.key_with_tag(ddd_value, "current-version")
        _, approved_version_value = find.key_with_tag(ddd_value, "approved-version")

        self.doc_title = title_value
        self.doc_scheme = scheme
        self.doc_location = location
        self.version = current_version_value
        self.approved_version = approved_version_value

        _, vhd_value = find.key_with_tag(model, "version-history-data")
        versions = find.keys_with_tag(vhd_value, "row-identifier")
        match_found = False
        for version_key, version_value in versions:
            if match.equals(current_version_value, version_value):
                self.version_row = version_key.getProperty("row")
                self.version_author = find.key_with_tag(self.version_row, "version-author")[1]
                self.version_author_role = find.key_with_tag(self.version_row, "version-author-role")[1]
                self.version_date = find.key_with_tag(self.version_row, "version-date")[1]
                self.version_changelog = find.key_with_tag(self.version_row, "version-changelog")[1]
                self.version_status = find.key_with_tag(self.version_row, "version-status")[1]
                self.version_approver = find.key_with_tag(self.version_row, "version-approver")[1]
                self.version_approved_date = find.key_with_tag(self.version_row, "version-approved-date")[1]
                match_found = True
                break

        if not match_found:
            logger.error(f"Could not find entry in version history table for threat model current version '{current_version_value}'")
            raise ManageError("no-version-history", {"current_version":current_version_value})

        return id_value, current_version_value, approved_version_value

    def fromDict(self, version:str, meta_dict:dict) -> None:

        self.version = version
        self.doc_title = meta_dict.get("title", None)
        self.doc_scheme = meta_dict.get("scheme", None)
        self.doc_location = meta_dict.get("location", None)
        
        self.version_author = meta_dict.get("author", None)
        self.version_author_role = meta_dict.get("author-role", None)
        self.version_date = meta_dict.get("date", None)
        self.version_changelog = meta_dict.get("change-log", None)
        self.version_status = meta_dict.get("status", None)
        self.version_approver = meta_dict.get("approver", None)
        self.version_approved_date = meta_dict.get("approved-date", None)

    def _get_state(self):
        output = {}
        output["title"] = self.doc_title
        output["scheme"] = self.doc_scheme
        output["location"] = self.doc_location
        output["author"] = self.version_author
        output["author-role"] = self.version_author_role
        output["date"] = self.version_date
        output["change-log"] = self.version_changelog
        output["status"] = self.version_status
        output["approver"] = self.version_approver
        output["approved-date"] = self.version_approved_date

        return output

    def __getstate__(self):
        """ Used by jsonpickle to state of class to output """
        return self._get_state()

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_dict(node._get_state())


class IndexMetaData:

    def __init__(self, config:dict, storage) -> None:
        yaml_register_class(IndexMetaData)

        self.index_filename = config.get("index-filename", "threatmodels.yaml")
        self.storage = storage

        self._load_index()

    def _load_index(self):

        self.indexdata = {}

        #threatmodels = load_yaml.yaml_file_to_dict(Path(self.storage.repodir).joinpath(self.index_filename))
        if (threatmodels := self.storage.load_yaml([], Path(self.storage.repodir).joinpath(self.index_filename))) is not None:
            for TMindex_list_entry in threatmodels.get("threatmodels", []):
                mdie = MetadataIndexEntry(TMindex_list_entry)
                self.indexdata[mdie.ID] = mdie
        else:
            logger.warning(f"No {self.index_filename} was loaded.  This should only happen when the metadata repo is first created and is empty.")

    def getIndexEntry(self, ID:str) -> MetadataIndexEntry:
        return self.indexdata.get(ID, None)

    def getIndexEntryByLocation(self, scheme:str, location:str) -> MetadataIndexEntry:

        location_based_index = {(entry.scheme, entry.location):entry for entry in self.indexdata.values()}

        return location_based_index.get((scheme, location), None)

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
        #load_yaml.class_to_yaml_file2([IndexMetaData, MetadataIndexEntry], self, Path(self.storage.repodir).joinpath(self.index_filename))
        load_yaml.class_to_yaml_file(self, Path(self.storage.repodir).joinpath(self.index_filename))

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

    def __init__(self, config:dict, storage:ThreatModelStorage, ID:str) -> None:
        yaml_register_class(ThreatModelMetaData)

        self.index = IndexMetaData(config, storage)

        self.metadata_filename = config.get("metadata-filename", "metadata.yaml")
        self.storage = storage
        self.approvedStatus = config.get("approved-status", "Approved")
        self.write_plain_model = config.get("write-plain-model", True)
        self.ID = ID
        self._set_empty()

        self.index._load_index()

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

        #self.storage.write_yaml([ThreatModelMetaData, ThreatModelVersionMetaData], Path(self.ID).joinpath(self.metadata_filename), self)
        self.storage.write_yaml(Path(self.ID).joinpath(self.metadata_filename), self)

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
            

    def setApprovedVersion(self, ID:str, currentModelIndexEntry:MetadataIndexEntry, approvedModelIndexEntry:MetadataIndexEntry, version:ThreatModelVersionMetaData):

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
        elif match.equals(version.version, version.approved_version) and not approvedModelIndexEntry.isApproved():
            # The current version = approved version, but it's not approved.  Probably forgot to approve the version in the version history table
            logger.error(f"Submitted Threat Model approved version in the document is not marked as approved in the Version History table.")
            raise ManageError("approved-version-not-approved", {"ID":ID, "approved_version":version.approved_version})
        elif not match.equals(version.version, version.approved_version) and currentModelIndexEntry.isApproved():
            # The current version != approved version, but current version approved.  Probably forgot to increase the approved version the version in the version history table
            logger.error(f"Submitted Threat Model current version is approved, but differs from the approved version.")
            raise ManageError("approved-version-not-updated", {"ID":ID, "current_version":currentModelIndexEntry.approved_version, "approved_version":version.approved_version})

        # TODO make sure the status is APPROVED
        if approvedModelIndexEntry.isApproved() and not match.equals(self.approvedStatus, version.version_status):
            logger.error(f"Submitted Threat Model approved version is approved, but status is not set to '{self.approvedStatus}'.")
            raise ManageError("status-not-approved", {"ID":ID, "approved_version":version.approved_version, "approved_status":self.approvedStatus})

        # if match.equals(currentMetadataIndexEntry.approved_version, version.version):
        #     logger.error(f"Submitted Threat Model version is the same as current approved version.  Cannot overwrite current approved version.")
        #     raise ManageError("cant-update-approved-version", {"ID":ID, "approved-version":currentMetadataIndexEntry.approved_version})

        # if not match.is_empty(approvedModelIndexEntry.approved_version) and not match.is_empty(currentModelIndexEntry.approved_version):
        #     if not match.equals(approvedModelIndexEntry.approved_version, currentModelIndexEntry.approved_version):
        #         logger.error(f"Submitted Threat Model version has different current version and approved version numbers")
        #         raise ManageError("current-and-approved-not-equal", {"current-version":version.version, "approved-version":approvedModelIndexEntry.approved_version})    
        # if not match.is_empty(indexEntry.approved_version) and not match.equals(indexEntry.approved_version, version.version):
        #     logger.error(f"Submitted Threat Model version has different current version and approved version numbers")
        #     raise ManageError("current-and-approved-not-equal", {"current-version":version.version, "approved-version":indexEntry.approved_version})

        self.index.setIndexEntry(ID, currentModelIndexEntry)

        self.IDmetadata["versions"][version.version] = version

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