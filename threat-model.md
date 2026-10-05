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
