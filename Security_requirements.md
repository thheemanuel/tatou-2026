# Security Requirements

This document records security requirements used by Group 21 and
connects them to threats and verification evidence.

## SR-01: Document ownership

### Requirement

Documents and document-related operations must only be accessible to the authenticated owner of the document.

Source:

- Platform_specifications.md
- server/API.md

### Threat

An authenticated user attempts to access or perform operations on a document belonging to another authenticated user.

For the assurance assignment this is described as T.CROSS_USER.

### Relevant operations

- get-document
- delete-document
- create-watermark
- list-versions
- read-watermark

### Verification evidence

- server/test/test_get_document_idor.py
- server/test/test_delete_document_idor.py
- server/test/test_create_watermark_idor.py

### Current limitations

Not every document-related endpoint has an automated cross-user test.
The pytest environment also differs from the deployed environment.
