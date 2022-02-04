#!/usr/bin/env python3
"""
Classes to manipulate for threat model metadata
"""
import logging
import os
from pathlib import Path
from ruamel.yaml import YAML
from utils import match
from utils import load_yaml
from data import find
from utils.error import ManageError
from manage.storage.gitrepo import IndexStorage
from manage.storage.gitrepo import ThreatModelStorage

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

class MetadataIndexEntry:

    def __init__(self, entry:dict):

        self.ID = entry.get("ID", "")
        self.scheme = entry.get("scheme", "")
        self.location = entry.get("location", "")
        self.approved_version = entry.get("approved-version", "")
        self.approved_date = entry.get("approved-date", "")     

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

        self.doc_title = None
        self.doc_location = None
        self.doc_current_version = None
        self.version_row = None
        self.version_author = None
        self.version_author_role = None
        self.version_date = None
        self.version_changelog = None
        self.version_status = None
        self.version_approver = None
        self.version_approved_date = None

    def fromModel(self, location, model):

        ddd_key, ddd_value = find.key_with_tag(model, "document-details-data")
        _, id_value = find.key_with_tag(ddd_value, "document-id")
        title_key, title_value = find.key_with_tag(ddd_value, "document-title")
        current_version_key, current_version_value = find.key_with_tag(ddd_value, "current-version")

        self.doc_title = title_value
        self.doc_location = location
        self.version = current_version_value

        vhd_key, vhd_value = find.key_with_tag(model, "version-history-data")
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

        return id_value

    def fromDict(self, version:str, meta_dict:dict) -> None:

        self.version = version
        self.doc_title = meta_dict.get("title", None)
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
        
        self.index_filename = config.get("index-filename", "threatmodels.yaml")
        self.storage = storage

    def _load_index(self):

        threatmodels = load_yaml.yaml_file_to_dict(Path(self.storage.repodir).joinpath(self.index_filename))

        self.indexdata = {}
        for TMindex_list_entry in threatmodels["threatmodels"]:
            mdie = MetadataIndexEntry(TMindex_list_entry)
            self.indexdata[mdie.ID] = mdie

    def getIndexEntry(self, ID:str):
        return self.indexdata.get(ID, None)

    def setIndexEntry(self, ID:str, entry:MetadataIndexEntry):
        self.indexdata[ID] = entry

    def __enter__(self):

        self.storage.__enter__()

        self._load_index()

        return self

    def _write_index(self):
        load_yaml.class_to_yaml_file([IndexMetaData, MetadataIndexEntry], self, Path(self.storage.repodir).joinpath(self.index_filename))

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
        
        self.index = IndexMetaData(config, storage)

        self.metadata_filename = config.get("metadata-filename", "metadata.yaml")
        self.storage = storage
        self.ID = ID
        self._set_empty()

    def _set_empty(self):
        self.IDmetadata = {}
        self.IDmetadata["ID"] = self.ID
        self.IDmetadata["versions"] = {}

    def _load_metadata(self):

        # If the directory or file don't exist, that's fine as they'll be created when we write out changes.

        # Does the dir exist?
        if Path(self.storage.repodir).joinpath(self.ID).is_dir():
            metadata_file = Path(self.storage.repodir).joinpath(self.ID, self.metadata_filename)
            # and the file?
            if metadata_file.exists():
                # then load
                contents_dict = load_yaml.yaml_file_to_dict(metadata_file)

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

        if not Path(self.storage.repodir).joinpath(self.ID).is_dir():
            os.mkdir(Path(self.storage.repodir).joinpath(self.ID))

        load_yaml.class_to_yaml_file([ThreatModelMetaData, ThreatModelVersionMetaData], self, Path(self.storage.repodir).joinpath(self.ID, self.metadata_filename))

    def __enter__(self):

        # This is going to checkout the relevant parts of the repo
        self.storage.__enter__()

        self.index._load_index()

        self._load_metadata()      

        return self

    def __exit__(self, exc_type, exc_value, traceback):

        if exc_type is None:
            self.index._write_index()
            self._write_metadata()

        # This is going to commit any changes
        self.storage.__exit__(exc_type, exc_value, traceback)

    def setApprovedVersion(self, ID:str, version:ThreatModelVersionMetaData):

        indexEntry = self.index.getIndexEntry(ID)

        if match.equals(indexEntry.approved_version, version.version):
            logger.error(f"Submitted Threat Model version is the same as current approved version.  Cannot overwrite current approved version.")
            return

        indexEntry.location = version.doc_location
        indexEntry.approved_version = version.version
        indexEntry.approved_version_date = version.version_approved_date
        self.index.setIndexEntry(ID, indexEntry)

        self.IDmetadata["versions"][version.version] = version


    def getVersion(self, versionID:str) -> ThreatModelVersionMetaData:
        
        return self.IDmetadata.get(versionID, None)

    def _get_state(self):

        output = {}
        output["threatmodel-metadata"] = self.IDmetadata

        return output

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_dict(node._get_state())