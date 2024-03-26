# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
### Changed
### Removed

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