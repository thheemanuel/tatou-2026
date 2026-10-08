# Tatou Security Monitoring

## 1. Purpose

The purpose of the monitoring system is to provide sufficient evidence to detect and investigate the security threats identified in "threat-model.md".

The system prioritizes security-relevant events rather than recording complete HTTP requests.

Sensitive information such as passwords, bearer tokens, secret document links, watermark secrets, private keys, and document contents must not be logged.

## 2. Application security events

### authentication.success IMPLEMENTED

Generated when a user successfully authenticates.

Fields:

- timestamp
- request_id
- user_id
- source_ip

### authentication.failure IMPLEMENTED

Generated when authentication fails.

Fields:

- timestamp
- request_id
- source_ip
- account identifier where appropriate
- failure category

### authorization.denied IMPLEMENTED (for /api/get-document)

Generated when an authenticated user attempts an operation on a resource they do not own.

Fields:

- timestamp
- request_id
- user_id
- source_ip
- action
- resource_type
- resource_id

### document.upload PLANNED

Generated after a document upload attempt.

Fields:

- timestamp
- request_id
- user_id
- source_ip
- document_id
- result
- safe file metadata

### plugin.load PLANNED

Generated when plugin loading is attempted.

Fields:

- timestamp
- request_id
- user_id
- source_ip
- result
- failure category

### rmap.authentication PLANNED

Generated during RMAP authentication.

Fields:

- timestamp
- request_id
- source_ip
- identity where safely available
- result
- failure category

### secret_link.access PLANNED

Generated when public version retrieval is attempted.

Fields:

- timestamp
- request_id
- source_ip
- result

The complete secret link must not be logged.

## 3. System telemetry

In addition to application events, monitoring should provide visibility into:

- container availability
- container restarts
- CPU usage
- memory usage
- disk usage
- application errors
- availability of the log collection system

## 4. Initial detection goals

The first detection rules will target:

- repeated failed authentication;
- repeated authorization failures;
- suspicious plugin loading/deserialization;
- repeated invalid secret-link access;
- repeated RMAP authentication/protocol failures;
- application/container instability.

## 5. Validation

Each observation point will be tested using controlled requests against our own deployment.

Testing must verify both that the expected event is produced and that sensitive information is absent from the resulting logs.
