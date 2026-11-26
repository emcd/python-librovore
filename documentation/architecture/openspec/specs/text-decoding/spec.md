# Text Decoding

## Purpose
The Text Decoding capability converts retrieved documentation bytes to text
through Detextive-based charset detection and textual validation, for both
file-scheme and HTTP sources, with consistent error mapping.

## Requirements

### Requirement: File-Scheme Text Retrieval
The system SHALL decode file-scheme content to text using charset detection,
defaulting through Detextive trial codecs.

Priority: High

#### Scenario: UTF-8 File Decodes
- **WHEN** a file URL points to UTF-8 encoded text
- **THEN** the system returns the decoded text content

#### Scenario: Non-UTF-8 File Decodes
- **WHEN** a file URL points to text in another charset
- **THEN** the system detects the charset and returns decoded text

#### Scenario: UTF-8 Last Resort
- **WHEN** detection does not yield a usable charset for a file
- **THEN** the system retries decoding as UTF-8 before failing

### Requirement: HTTP Text Retrieval
The system SHALL decode HTTP content to text, guided by the response
Content-Type header and falling back to charset detection.

Priority: High

#### Scenario: Header Charset Honored
- **WHEN** the Content-Type header specifies a charset
- **THEN** the system decodes with that charset

#### Scenario: Detection Fallback
- **WHEN** the Content-Type header carries no charset
- **THEN** the system detects the charset from content and decodes

#### Scenario: Default Charset Fallback
- **WHEN** neither headers nor detection yield a charset
- **THEN** the system decodes with the configured default charset

### Requirement: Non-Textual Rejection
The system SHALL reject non-textual content on both schemes with a mapped
domain error instead of returning decoded garbage.

Priority: High

#### Scenario: Binary File Rejected
- **WHEN** file-scheme content fails textual validation
- **THEN** the system raises `DocumentationInaccessibility`

#### Scenario: Unknown Header Charset Stripped With MIME Retained
- **WHEN** the Content-Type header names a charset no codec registry knows
- **THEN** the system strips the charset but retains the MIME for the gate
- **AND** falls back to detection and the default charset instead of raising `LookupError`

#### Scenario: Known Non-Text Codec Header Stripped With MIME Retained
- **WHEN** the Content-Type header names a registry-known non-text codec
  (for example `base64_codec`, `rot_13`, or `hex_codec`)
- **THEN** the system strips the charset but retains the MIME for the gate
- **AND** falls back to detection and the default charset instead of raising `LookupError`

#### Scenario: Unusable Header Charset Stripped With MIME Retained
- **WHEN** the Content-Type header names a charset the registry marks as
  text but that cannot decode content (for example `undefined`), or a
  malformed charset name (for example one containing a NUL byte)
- **THEN** the system strips the charset but retains the MIME for the gate
- **AND** falls back to detection and the default charset instead of raising `UnicodeError` or `ValueError`

#### Scenario: Non-Textual MIME Header Rejected Without Decoding
- **WHEN** HTTP content has a non-textual MIME type or fails content analysis
- **THEN** the system raises `HttpContentTypeInvalidity`

#### Scenario: Empty Non-Textual HTTP Body Rejected
- **WHEN** the HTTP body is empty but the Content-Type declares a
  non-textual MIME type, on either the cache-hit or the cache-miss path
- **THEN** the system raises `HttpContentTypeInvalidity`

#### Scenario: Empty Textual Body Valid
- **WHEN** the body is empty and the Content-Type is textual or absent
- **THEN** the system returns empty text

### Requirement: Detector Independence
The system SHALL route all character detection through Detextive with no
direct dependency on detector packages and no detector-aware tests.
Disabling detection in the pyfakefs harness is explicitly permitted.

Priority: Medium

#### Scenario: No Direct Detector Dependencies
- **WHEN** the project dependency manifest is inspected
- **THEN** `chardet`, `charset-normalizer`, `python-magic`, and `puremagic`
  appear neither as direct dependencies nor as test imports
- **AND** detector backends arrive only transitively through Detextive

#### Scenario: No Detector-Aware Tests
- **WHEN** the test suite runs
- **THEN** no test maps detector data files, asserts detector-specific
  labels, imports detector packages, or selects detector backends to
  reach a decoding result
- **AND** pyfakefs tests run with detection disabled
- **AND** all charset tests assert decode-to-expected-text

#### Scenario: Production-Default Coverage
- **WHEN** the suite runs
- **THEN** a real-filesystem smoke subset exercises production-default
  detector order alongside the detection-disabled pyfakefs tests
