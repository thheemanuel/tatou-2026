# Tatou Threat Model

Verison: 0.2
Status: Initial threat model informed by implementation ewview and observed project events
Method/Framework: STRIDE

## 1. Purpose and scope

This document describes the threat model for our deployment of the Tatou PDF watermarking platform.

The purpose of the threat model is to identify security threats that are relevant to tatou's actual functionality and deployment. The results will be used to decide which security events should be observable, logged, and monitored as part of the Operational Security specialization.

STRIDE is used as a structured method for identifying threats. The goal is not to produce one threat for every STRIDE category, but to use the method to identify threats that are meaningful for the service (tatou).

The following components are in scope:

- tatou flask backend and http api
- html/javascript web client
- authentication and authorization
- mariadb database
- pdf file storage
- pdf upload and processing
- watermark creation and extraction
- secret document links
- rmap endpoints and rmap v1.0.2
- rmap/openpgp key material
- docker deployment
- host vm where relevant to the security of the service (tatou)
- security logging and monitoring

Third-party components such as flask, mariadb, docker and pdf processing libraries are not threat modeled internally. However, their configuration and the way Tatou interacts with them are within scope.

## 2. System overview

# AI generated diagram over the system

                    Course network
                         |
          +--------------+--------------+
          |                             |
       Web/API                       RMAP client
       clients                      (other groups)
          |                             |
          +--------------+--------------+
                         |
                  +------v------+
                  | Tatou/Flask |
                  +------+------+
                         |
             +-----------+-----------+
             |                       |
             v                       v
          MariaDB                PDF storage
                                     |
                                     v
                               Watermarking

                  RMAP ---- OpenPGP keys

               ===== Docker boundary =====

                       Host VM

## 3. Assets

Important assets include:

- original confidential pdf documents
- individually watermarked pdf documents
- watermark secrets and attribution information
- user accounts
- authentication credentials and bearer tokens
- secret document download links
- user and document metadata stored in database
- rmap server private-key material
- trusted rmap client public keys
- the three flags
- security logs used for monitoring and incident investigation
- availability of the service

Confidentiality is especially important for documents, credentials, secret links, private keys and flags, for example.

Integrity is important for document ownership, watermark attribution, database info, rmap identities and security logs.

Availability is important because tatou must remain operational during the project.

## 4. Threats (threat actors)

# 4.1 Unathuenticated network user

- An unauthenticated network user can interact with publicly accessible tatou endpoints but does not possess legit tatou credentials.

# 4.2 Malicious authenticated user

- A malicious authenticated user has a legit tatou account and authentication token.

# 4.3 Other course groups

- Other course groups are legitimate participants in the project and may possess rmap identities that are trusted by our deployment.

# 4.4 Attacker with compromised credentials

- An attacker may obtain a password, bearer token, secret document link, or other credentials belonging to a legitimate user.

## 5. Attack surface

The main trust boundary exists between the course network and the tatou application.

Data received through http requests must be considered to be untrusted. This includes authentication information, json data, document identifiers, uploaded pdfs, watermark parameters, secret links, and rmap messages.

More trust boundaries exist between:

- tatou and mariadb
- tatou and the document filesystem
- tatou and the watermarking subsystem
- tatou and the rmap/openpgpg key material
- the tatou container and the host vm.

Important attack surfaces include:

- account creation
- login
- bearer token authentication
- authenticated document endpoints
- document identifiers
- pdf upload and processing
- watermark creation and extraction
- public secret-link retrieval
- rmap authentication
- filesystem operations
- database operations
- watermarking and plugin related functionality
- application and deployment configuration (docker etc.)

These areas either accept untrusted input or provide access to security sensitive areas or resources.

## 6. Identified threats

The following threats were identified by applying STRIDE to tatous main components, assets, trust boundaries, and data flows.

The threat model also incorporates evidence collected during development and operation of our tatou instance (deployement). Where a vulnerability has previously been confirmed, this is stated. Other entries represent credible threats that still require further verification or monitoring.

### T1. Cross-user document access

STRIDE: Information Disclosure / Elevation of Privilege
Priority: High
Status: Previously vulnerable; mitigation implemented and tested

Tatou contains documents belonging to different authenticated users. A malicious authenticated user may attempt to access or operate on another users document by supplying its document identifier.

SUccessful authentication does not impy authorixation to every document. Every operation involving a document must also verify that the resource belong to the authenticated user.

This threat was previously confirmed in our implementation.

delete-document, create-watermark and read-watermark originally looked up documents by their documet id without verifying that the document belonged to the requesting user.

The affected operations were changed to include the authenticated users id when looking up documents.

Altough the known vulnerabilities have been mitigated, authorization remains an important observation point.

Failed ownership checks should be observable.

### T2. Unsafe plugin loading and deserialization

STRIDE: Tampering / Elevation of Privilege
Priority: Critical
Status: Attack activity observed; mitigations implemented

Tatou supports dynamically loaded watermarking functionality. Loading serialized Python obejcts from attacker controlled input creates a particularly dangerous trust boundary because unsafe deserialization can cause behavior beyond the intended watermarking functionality.

Following a flag getting stolen by another group, automated activity was observed that repeatedly created an account and uploaded a file named "x.pkl". The behaviour appeared to target the unsafe pickle plugin functionality.

Also, an unsafe watermarking method that was exposed to users was removed from the available method registry. Additional defenses were later introduced around plugin loading, including path validation and restricted deserialization.

The fact that this attack class has already been observed makes plugin activity a high-value monitoring target.

Relevant events include:

- attempts to load a plugin
- rejected plugin filenames or paths
- deserialization failures
- rejected serialized objects
- successful plugin registration
- repeated suspicious file uploads

These events should include authenticated identity, source, opeartion, and outcome where available. (Except for the situation where sentitive or personal information is included).

### T3. SQL injection through API parameters

STRIDE: Information Disclosure / Tampering / Elevation of Privilege
Priority: High
Status: Confirmed vulnerability; known instance mitigated

Tatou interacts with MariaDB using values originating from http requests.

A previous implementation of "delete-document" constructed a database query using string concatenation with the supplied document identifier. This allowed attacker controlled input to influence the SQL statement instead of being treated exclusively as data.

The vulnerable query was changed to use a parameterized query.

SQL injection can have consequences beyond the endpoint containing the vulnerability. Depending on the query and database permissions, it may allow an attacker to disclose databse information, modify application state, bypass application assumptions, or obtain information useful for another stage of an attack.

All databse operations involving attacker controlled input should therefore user parameterized queries.

Monitoring is a secondary control for this threat. Preventing injection through safe query construction remains the primary defense.

### T4. Path traversal and unintended filesystem access

STRIDE: Information disclosure / Tampering / Elevation of Privilege
Priority: High
Status: Known attack path; mitigation implemented for plugin loading

Tatou stores and processes uploaded documents and plugins using the filesystem.

If attacker controlled filenames or paths are resolved without ensuring that they remain within the intended directory, path components such as "../" may cause the application to access files outside the directory.

This becomes particularly dangerous when combined with plugin loading. A file uploaded thorugh one part of the application must not become loadable as executable plugin functionality merely by referencing its location using path traversal.

A path traversal guard has been introduced around plugin loading. However, other filesystem operations should still be reviewed to ensure the equivalent assumptions are enforced consistently.

Security relevant events include rejected traversal attempts and references to files outside an expected directory.

### T5. Account compromise thorugh authentication attacks

STRIDE: Spoofing
Priority: High
Status: Ongoing threat

An unauthenticated attacker may repeatedly attempt to log in using
different credentials in order to gain access to an existing tatou
account.

If an account is compromised, the attacker may gain access to the
victim's authenticated functionality and documents.

Authentication activity should therefore be observable. Both failed and
successful authentication attempts may be useful during an investigation.

Repeated authentication failures from one source, or repeated failures
against one account, may indicate credential guessing.

Passwords and bearer tokens must never be written to security logs.

### T6. Unauthorized access through secret document links

STRIDE: Information Disclosure
Priority: High
Status: Requires continued review

Tatou allows generated document versions to be retrieved using secret links.

Possession of such a link acts as a capability to retrieve the corresponding document. Anyone who obtains a valid link may therefore be able to access the document without following the normal authenticated document workflow.

An attacker may attempt to obtain such a link though disclosure, prediction, enumeration, or resuse.

The predictability of identifiers or filenames is relevant here. Rate limiting may make large scale guessing more difficult, but does not correct an underlying predictability problem if the value itself remains guessable. Unpredictable random values are preferable where secrecy of the identifier is part of the access control mechanism.

Successful and unsuccessful access to secret document links should provide sufficient evidence for investigation. (The complete secret link must not be stored in the log).

### T7. Unauthorized or invalid rmap authentication

STRIDE: Spoofing / Information Disclosure
Priority: High
Status: Requires continued verification and monitoring

RMAP is used to authenticate other course groups before providing access to an individually watermarked version of the assigned confidential document.

An unauthorized client may attempt to impersonate an accepted identity, send malformed protocol messages, replay protocol information, or otherwise complete the exchange without satisfying the intended authentication requirements.

Only identities whose public keys are configured as trusted should be accepted.

Failed RMAP authentication, unknowning identities, and protocol errors are therefore important observation points.

Successful RMAP authentication should also be recorded so that document distribution can later be associated with an authenticated rmap identity.

Monitoring must, of course, not expose sensitive information.

### T8. Exposure of the rmap private key

STRIDE: Information Disclosure / Spoofing
Priority: High
Status: Preventinve control required

The rmap server private key represents the cryptographic identity of our tatou rmap server.

Disclosure of this key could undermine the authentication properties of rmap and may allow another party to impersonate the server.

The private key must therefore be protected from accidental inclusion in source control and other inappropriate or unncessary exposure.

### T9. Malicious or malformed pdf processing

STRIDE: Tampering / Denial of Service
Priority: Medium
Status: Ongoing threat

Uploaded pdfs across an important trust boundary. Their contents are controlled by users but are subsequently processed by tatou and its pdf and watermarking functionality.

Malformed or deliberately unusual pdfs may trigger errors or expensive processing. Depending on the implementation, this could result in failed watermark operations, application exceptions, exessive resource consumption, or service instability.

File type and document validation are therefore importatnt preventive controls.

Rejected uploads and unexpected pdf-processing failures should also be observable.

### T10. Application or container compromise

STRIDE: Elevation of Privilege / Information Disclosure
Priority: Critical
Status: Previously relevant to an actual flag compromise

A vulnerability that gives an attacker broad file access or code execution inside the tatou application/container could expose several assets simultaneously.

These assets may include:

- confidential pdfs
- application configuration
- database credentials
- rmap key material
- course flags

This is particularly relevant because the project has already experienced flag compromise. It must therefore be treated as an operational scenario, not merely as a theoretical worst case.

Application logs alone may become unreliable after a sufficiently serious compromose. An attacker with enough access may be able to modify or delete local evidence. Important security telemetry should therefore be persisted or collected outside the tatou application container where practical.

### T11. Destruction or modification of security evidence

STRIDE: Tampering / Repudiation
Priority: Medium
Status: Mnitoring design requirement

An attacker who compromises tatou may attempt to remove or modify logs that describe the attack.

Important information regarding the security events within the service should therefore be persisted outside the application container.

The monitoring system should also make it possible to identify when info unexpectedly stops arriving.

### T12. Sensitive information leaked through security logging

STRIDE: Information Disclosure
Priority: High
Status: Monitoring design requirement

Introducing additional security logging creates a new security risk.

Careless logging of complete http requests, headers, urls, exception information, database queries, or rmap messages could expose sensitive information.

Security logging should therefore use explicitly selected fields rather than storing complete requests.

The following information must not intentionally be written to security logs:

- passwords
- bearer tokens
- rmap private key material
- watermark secrets
- complete secret document links
- document contents

Should be tested to confirm above.

### T13. Resource exhaustion and loss of availability

STRIDE: Denial of Service
Priority: Medium
Status: Ongoing operational threat

Tatou performs operations that may consume significant resources,
including PDF parsing, watermark generation, filesystem storage, plugin
processing, and database access.

The course rules prohibit intentional destructive or disruptive attacks
such as denial-of-service attacks. Resource exhaustion is nevertheless
relevant operationally because it may result from malformed input,
implementation defects, unexpected workloads, or non-destructive attack
activity.

Rate limiting may reduce some forms of repeated request activity, but it
should not be treated as a substitute for fixing the underlying
vulnerability.

Relevant observation points include:

- application error rate
- processing time
- container restarts
- disk usage
- cpu usage
- memory usage
- unusual request volume

## 7. Implications for monitoring

The threat analysis provides the basic for deciding what tatou should log and monitor.

The journal of project event demonstrates why this is necessary. During previous incidents, the group was able to identify suspicious behavior through application and database state, but the events were not necessarily represented as dedicated security information/telemetry.

The goal of the monitoring operations is therefore not simply to produce more logs. It is to make security relevant behavior visible enough that an attack can be detected and reconstructed.

The initial application level observation points should include:

- successful authentication
- failed authentication
- failed authorization and ownership checks
- document upload failures
- pdf processing failures
- plugin loading attempts
- rejected plugin paths
- deserialization failures
- successful plugin registration
- secret-link access
- invalid secret-link access
- RMAP authentication success and failure
- RMAP protocol failures
- important document/database state changes
- unexpected application exceptions
- unexpected filesystem failures

Useful event field may therefore include for example:

- timestamp
- event type
- request identifier
- source address
- authenticated user identifier
- operation
- resource type
- resource identifier
- outcome
- safe failure category

Application logs alone are not sufficient for all identified threats.

Important security information should be stored outside the tatou application container so that evidence is more likely to survive an application or container compromise.

## 8. Detection priorities

The first monitoring implementation should focus on a small number of
high-value detections rather than attempting to detect every possible
attack immediately:

- Repeated authorization failures
- Suspicious plugin activity
- Authentication failures
- SQL/database errors caused by request input
- Secret-link proving
- rmap authentication failures
- Application or container instability

## 9. Recovery considerations

Detection alone is not sufficient. The operational security process must also support recovery after an incident.

Recovery procedures should be prepared for at least:

- flag compromise
- account or bearer-token compromise
- confidential document disclosure
- application/container compromise
- RMAP private-key compromise
- database or persistent-data corruption
- service failure

Detect -> investigate -> determine impact -> contain -> fix / remove cause -> rotate affected secrets if necessary -> redeploy / restore -> verify -> document lessons learned.

## 10. Limitations

This threat model does not prove that tatou is secure.

STRIDE provides a structured method for reasoning about threats, but is does not guarantee that every vulnerability will be discovered.

The model is also influenced by incidents already experienced by the group. This is useful because it grounds the analysis in real evidence, but it creates a risk of focusing too heavily on attacks that have already occurred while overlooking new attack paths.

Monitoring itself has limitations.

An attacker using a valid stolen bearer token may appear to the application as the legitimate user.

Changes made to a watermarked pdf after it has been downloaded occur outside the tatou server and cannot normally be observed through monitoring the server.

A sufficiently serious application or container compromise may allow an attacker to interfere with local application logging.

RMAPs cryptography intentionally protects/limits what can be observed.

Monitoring can provide evidence of attempted exploitation, but it should
not replace preventive controls. For example, rate limiting may reduce
the speed of enumeration but does not make a predictable secret
unpredictable, and logging SQL errors does not replace parameterized
queries.

For these reasons, the threat model should remain a living document and
be updated as implementation review, testing, monitoring, and future
attack attempts provide new evidence.

Finally, future attacks or suspicious activity observed during operation
should be compared with this threat model. New attack paths should result
in updates to the model, monitoring implementation, and recovery
procedures where appropriate.
