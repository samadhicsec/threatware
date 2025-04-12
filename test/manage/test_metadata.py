#!/usr/bin/env python3

import pytest
from threatware.manage.metadata import MetadataIndexEntry, IndexMetaData, ThreatModelMetaData

@pytest.mark.parametrize("details_current_version, ver_his_cur_version, ver_his_cur_status, ver_his_cur_approver, ver_his_cur_app_date, details_approved_version, ver_his_apprvd_version, ver_his_apprvd_status, ver_his_apprvd_approver, ver_his_apprvd_app_date", [
    ("", "", "", "", "", "", "", "", "", ""),
])
def test_load_scheme(monkeypatch, details_current_version, ver_his_cur_version, ver_his_cur_status, ver_his_cur_approver, ver_his_cur_app_date, details_approved_version, ver_his_apprvd_version, ver_his_apprvd_status, ver_his_apprvd_approver, ver_his_apprvd_app_date):
    
    def mock_init():
        return

    monkeypatch.setattr(IndexMetaData, "__init__", mock_init)

    current_in_version_history = MetadataIndexEntry({"approved-version":ver_his_cur_version, "status":ver_his_cur_status, "approver":ver_his_cur_approver, "approved_date":ver_his_cur_app_date})
    approved_in_version_history = MetadataIndexEntry({"approved-version":ver_his_apprvd_version, "status":ver_his_apprvd_status, "approver":ver_his_apprvd_approver, "approved_date":ver_his_apprvd_app_date})
        
    assert str(load_scheme(scheme)) == expected_result