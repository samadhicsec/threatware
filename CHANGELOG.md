# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
### Changed
### Removed

## [Unreleased]

### Added

- New output format `html` can be used with the `format` parameter, but only for the `verify` action.  This returns the web page representation of the threat model, and findings are displayed via tooltips at the locations in the document where the issue exists.
- A new `response/response_config.yaml` file has been added to the configuration files to allow for the complete customisation of the HTML/JavaScript/CSS that is added to the HTML version of the threat model i.e. when `format='html'`.  A new `response/response_texts.yaml` has also been added for associated texts to be localised.
- scheme query types `html-element-text` (to replace `html-text`) and `html-element-attribute`.  This means all the `html-*` query types now are consistent and all expect to be passed elements (rather than before when some expected text).

### Changed

- The format of all `*_text.yaml` configuration files can now include (in addition to language) a version of the output string specific to the output format e.g. specific texts have been added when the output is `html` in order to appropriately format the content.
- Schemes have been updated to grab all text in the list items under the References heading.  A new verification check was added when the text does not contain a hyperlink.
- ** BREAKING CHANGE ** The texts under `grouped-by` in `verifiers/verifiers_texts.yaml` have been moved to the same lcoation as all the other texts and the `grouped-by` section removed.  If you have edited these then they'll need to be moved.
- scheme query `html-text-section` now outputs a markdown representation of the nodes passed to it ()

### Fixed

- Updated the preprocessor for `schemes/googledoc-scheme-1.0.yaml` to also strip `sup` elements from headings.  If the googledoc had a comment on certain headings this was causing issues.
- Fixed how request parameters were being passed to the template engine, making them work again
- Fixed manage.indexdata action so it passes through the correct ID
- Fixed AWS lambda git setup to allow git config to be called successfully
- Updated scheme query `html-text-section` from just converting `p` nodes to text, to now outputting a markdown representation of all the nodes passed to it

### Removed

## [0.9.4] - 2024-08-28

### Added

- threatware can now run as an API.  Install requirements from `api_requirements.txt`.  It uses the [FastAPI framework](https://fastapi.tiangolo.com/) e.g. `fastapi run actions/api_main.py --port 8080`.  Once running you can see API docs at either `/docs` or `/redoc` URL paths.  A containerised version of threatware running as an API is available at https://hub.docker.com/r/threatwaretryit/api_threatware.

### Fixed

- the `manage.indexdata` action no longer returns internal information and just returns the information stored in threatmodels.yaml.
- the `validate-as-status` validation is now configured correctly and reports when the `Verision History` `Status` entry is invalid.

## [0.9.3] - 2024-03-26

### Added

- Added new `cov` tag validation to ensure 1-to-1 coverage between tables.  Example, authn/z table must include every in-scope component.

### Changed

- **BREAKING CHANGE** When extracting an HTML table in 0.9.2 there was code to remove certain HTML elements e.g. &lt;span>, &lt;a> etc.  This was too restrictive as different document formats needed different processing.  The definition of this processing has now been moved to the scheme file for the document format.  This has also allowed the XPath queries to be made simpler.  Older scheme files won't have these pre-processing commands, and since the 0.9.3 code was updated to not hardcode the removal of specific HTML elements, these older scheme files won't convert correctly (i.e. no HTML elements will be removed).  Instructions have been added to the latest scheme files on what pre-processing commands to add to older scheme files to make them covert the same way as version 0.9.2 would convert them.

### Fixed 

- Expressions in backets "()" after tagged `storage-location` values, are now ignored for the purpose of validation
- '&' are now handled correctly when extracting HTML tables
- 'U+00A0' are now replaced with 'U+0020' and no longer break matching validators
- Fixed bug when no Asset value was present in the Threats & Control table
- Hyperlinks in tables no longer break parsing a table

## [0.9.2] - 2022-07-22

### Added

- Everything, initial release