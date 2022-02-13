#!/usr/bin/env python3

from atlassian import Confluence
from requests import HTTPError
import unicodedata

def connect(url, username, api_token):
    confluence = Confluence(
        url=url,
        username=username,
        password=api_token,
        cloud=True)

    return confluence

def exists(confluence, space, title):
    return confluence.page_exists(space, title)

def exists(confluence, page_id):
    url = "rest/api/content/{}/property".format(page_id)
    try:
        confluence.get(url)
    except HTTPError as e:
        return False
    return True

def history(confluence, page_id):
    url = "rest/api/content/{}/version?expand=content".format(page_id)
    return confluence.get(url)

def read(confluence, page_id, version=''):
    page = confluence.get_page_by_id(page_id, expand='body.view', status=None, version=version)
    return unicodedata.normalize("NFKD", page['body']['view']['value'])