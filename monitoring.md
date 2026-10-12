# Tatou Security Monitoring

## 1. Purpose

The purpose of the monitoring system is to provide sufficient evidence to detect and investigate the security threats identified in `threat-model.md`.

The system prioritizes security-relevant events rather than recording complete HTTP requests.

Security events are written as structured JSON using the `tatou.security` Python logger.

Every security event contains:

- `timestamp` — UTC timestamp of the event
- `event` — type of security event
- `request_id` — unique identifier used to correlate events from the same HTTP request
- `source_ip` — IP address of the requesting client

Sensitive information such as passwords, bearer tokens, secret document links, watermark secrets, private keys, and document contents must not be logged.

## 2. Application security events

### authentication.success — IMPLEMENTED

Generated when a user successfully authenticates through `/api/login`.

Additional fields:

- `user_id`
- `outcome` — `success`

### authentication.failure — IMPLEMENTED

Generated when authentication fails because of invalid credentials, missing or invalid authorization headers, expired tokens, or invalid tokens.

Additional fields:

- `reason` — failure category
- `outcome` — `failure`

The submitted password and bearer token are not included in the event.

### rate_limit.exceeded — IMPLEMENTED

Generated when a client exceeds the application's request limit.

Additional fields:

- `outcome` — `denied`
- `request_count` — number of recent requests
- `window_seconds` — configured rate-limiting window

This event helps identify excessive request activity and possible automated scanning.

### authorization.denied — IMPLEMENTED (for `/api/get-document`)

Generated when an authenticated user attempts to read a document belonging to another user.

Additional fields:

- `user_id`
- `resource_type` — `document`
- `resource_id` — document identifier
- `action` — `read`
- `reason` — `ownership_mismatch`
- `outcome` — `failure`

The current implementation covers denied document retrieval through `/api/get-document`. It does not yet cover every authorization failure throughout the application.

### document.upload — IMPLEMENTED

Generated during document upload attempts.

Additional fields:

- `user_id`
- `document_id` — included after a successful upload
- `result` — `success` or `failure`
- `reason` — included for failed uploads
- `file_size` — included when available

The document contents and authentication token are not logged.

### plugin.load — IMPLEMENTED

Generated when an authenticated user attempts to load a plugin.

Additional fields:

- `user_id`
- `result` — `success` or `failure`
- `reason` — included for failed attempts

Failure categories include invalid filenames, invalid paths, unsupported extensions, missing files, rejected serialized classes, and invalid plugin interfaces.

This event supports investigation of suspicious plugin-loading activity.

### rmap.authentication — IMPLEMENTED

Generated during the two stages of the RMAP authentication protocol:

- `initiate` — first RMAP message
- `get_link` — second RMAP message and subsequent document processing

Additional fields:

- `stage` — `initiate` or `get_link`
- `result` — `success`, `failure`, or `processing_failure`
- `reason` — included for failed operations

Failure categories include invalid message formats, protocol rejection, unexpected errors, duplicate links, and watermark or storage failures.

A successful RMAP authentication event does not necessarily mean that the watermarked document was successfully created. Subsequent processing failures are recorded separately.

The structured security event does not contain the RMAP message payload, secret link, or watermark secret.

### secret_link.access — IMPLEMENTED

Generated when a client attempts to retrieve a watermarked PDF using `/api/get-version/<link>`.

Additional fields:

- `result` — `success` or `failure`
- `reason` — included when access fails

Failure categories:

- `invalid_link` — the requested link does not match a database record
- `database_error` — the database lookup failed
- `invalid_file_path` — the stored file path is outside the permitted storage directory
- `file_missing` — the database record exists, but the PDF is missing from disk

Successful retrieval is recorded with `result="success"`.

The complete secret link, document contents, and watermark secret are not included in the structured security event.

## 3. System telemetry

In addition to application security events, monitoring should provide visibility into:

- Container availability
- Container restarts
- CPU usage
- Memory usage
- Disk usage
- Application errors
- Availability of the log collection system

These are monitoring goals and are separate from the application security events already implemented.

## 4. Initial detection goals

The initial detection goals are:

- **Repeated authentication failures:** Identify repeated failed login attempts or invalid authentication tokens from the same source IP.
- **Rate-limit violations:** Identify clients generating excessive request volumes.
- **Repeated authorization failures:** Identify repeated attempts to access documents owned by other users.
- **Suspicious plugin loading:** Identify repeated invalid plugin-loading attempts or rejected serialized classes.
- **Repeated invalid secret-link access:** Identify clients repeatedly requesting unknown or inaccessible document links.
- **RMAP authentication failures:** Identify repeated invalid RMAP messages, rejected protocol messages, or unsuccessful document processing.
- **Application and container instability:** Identify repeated application errors, unexpected container restarts, or resource exhaustion.

These are proposed detection rules. The application currently produces the relevant security events, but automated alerting and thresholds are not yet implemented.

## 5. Validation

Application security logging has been tested using automated pytest tests and controlled requests.

The tests verify:

- The expected security event is generated.
- The event contains the appropriate result and failure category.
- Standard fields such as timestamp, request ID, and source IP are present.
- Sensitive values, particularly secret document links, are excluded from structured security events.
- Existing HTTP response behavior is preserved for tested success and failure cases.

The test files are:

- `test_security_logging.py`
- `test_authorization_logging.py`
- `test_upload_logging.py`
- `test_plugin_logging.py`
- `test_rmap_logging.py`
- `test_secret_link_logging.py`

The secret-link logging tests cover successful retrieval, invalid links, database failures, invalid file paths, and missing files.

Additional validation will be needed if centralized log collection, alerting, or infrastructure monitoring is introduced.

The application security logging implementation was validated using six pytest test files. All 26 tests passed, covering authentication, authorization, document uploads, plugin loading, RMAP authentication, and secret-link access.

The tests verify that security events are generated for the tested success and failure scenarios, contain the expected structured fields, and do not expose the sensitive values checked by the tests.

**Validation result:** 26 passed, 0 failed.
