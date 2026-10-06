# Tatou Threat Model

Verison: 0.1
Status: Initial threat model
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
