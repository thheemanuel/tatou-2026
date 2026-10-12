# Specialization D — Operational Security

## 1. Objective

The goal of this specialization was to improve the operational security of Tatou, a PDF watermarking application, by identifying relevant threats, implementing security observation points, monitoring the deployed service, and investigating suspicious activity.

Our approach focused on producing actionable security evidence rather than introducing a complex monitoring platform.

## 2. Threat Modeling

We created a threat model describing Tatou's assets, trust boundaries, entry points, potential attackers, and relevant threats.

The analysis considered risks involving authentication, authorization, document handling, secret links, plugin functionality, and service availability.

The threat model helped us identify where additional security visibility would be useful and informed our selection of logging events.

The full analysis is documented in `threat-model.md`.

## 3. Security Logging Implementation

We implemented structured JSON security logging in the Flask application.

The logging implementation records eight security event types:

- `authentication.success`
- `authentication.failure`
- `rate_limit.exceeded`
- `authorization.denied`
- `document.upload`
- `plugin.load`
- `rmap.authentication`
- `secret_link.access`

Events include a UTC timestamp, event name, request identifier, and recorded source IP, together with additional fields relevant to the event.

Structured JSON was selected because it supports consistent searching, filtering, grouping, and analysis.

The logging design aims to avoid recording passwords, authentication tokens, document contents, or secret-link values.

## 4. Validation and Testing

We added automated tests to verify the security logging behavior across relevant application functionality.

The selected test suite completed successfully with **26 passing tests**.

We also verified that the deployed Docker application emitted structured security events visible through `docker compose logs`.

This established that the monitoring data was available in the running deployment, not only in unit tests.

## 5. Monitoring and Incident Detection

We used Docker Compose logs to investigate security events from the deployed Tatou service.

On 12 October 2026, we collected 600 `rate_limit.exceeded` events associated with source IP `10.100.11.15`.

The first recorded event occurred at 16:53:23 UTC and the last at 17:15:58 UTC, spanning approximately 22 minutes and 35 seconds.

All 600 recorded outcomes were `denied`.

This evidence shows that the application's rate-limiting mechanism was triggered and recorded its defensive decisions. It does not establish the total number of incoming requests or the identity and intent of the source.

Previously captured screenshots also showed repeated `authentication.failure` events, including several invalid-credential attempts from one recorded source over a short interval.

These observations were treated as suspicious activity rather than proof of successful compromise.

## 6. Incident Response and Recovery

We investigated the security events by grouping them by event type and source IP, examining their timestamps and outcomes, and preserving representative evidence.

We then checked the deployed environment.

Docker Compose showed the application and database containers running, and MariaDB reported healthy status.

On 12 October 2026, the application's `/healthz` endpoint returned HTTP 200 and confirmed that the database connection was working.

We also verified that a request for a nonexistent document link produced the expected HTTP 404 response.

No incident-related outage was established during the investigation, so we did not restart the application unnecessarily.

We documented a response and recovery runbook covering log inspection, containment decisions, health verification, and the steps to take if a service fails.

## 7. Findings and Lessons Learned

The work demonstrated that structured security logging can provide useful operational evidence without requiring a dedicated monitoring platform.

The collected logs made it possible to identify repeated rate-limit violations, determine their time range, and confirm the recorded defensive outcome.

The investigation also highlighted limitations:

- Suspicious events do not necessarily prove malicious intent.
- Recorded source IP addresses do not identify attackers.
- Health checks performed after an incident cannot prove uninterrupted availability during the incident.
- Docker log retention may limit historical investigation.
- Manual monitoring does not provide automatic alerts.

Future improvements could include centralized log storage, automatic detection thresholds, resource-usage monitoring, and a tested backup-restoration process.

## 8. Deliverables

The specialization produced:

- `threat-model.md` — threat model and security analysis.
- Security logging changes in the Flask application.
- Automated tests for security event generation.
- `monitoring.md` — monitoring design and event definitions.
- `specialization-d/incident-report.md` — analysis of observed security incidents.
- `specialization-d/monitoring-runbook.md` — monitoring, response, and recovery procedures.
- `specialization-d/evidence/rate-limit-excerpt.jsonl` — representative sanitized evidence.

Together, these artifacts document the design, implementation, validation, monitoring, investigation, and operational response work completed for Specialization D.
