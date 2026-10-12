# Specialization D — Security Incident Report

**Project:** Tatou — PDF Watermarking Service  
**Date of investigation:** 12 October 2026  
**Environment:** University VM, Docker Compose deployment  
**Evidence:** Application security logs, Docker container status, HTTP health checks, and previously captured screenshots

## 1. Purpose

This report documents suspicious security events observed on the deployed Tatou application, the defensive behavior recorded by the application, and the investigation performed afterward.

The goal is to demonstrate how security logging and operational monitoring can support detection, analysis, and response to attempted attacks.

The recorded activity is considered suspicious. Its malicious intent and the identity of the sources have not been established.

## 2. Incident 1 — Excessive Request Activity

### Description

On 12 October 2026, the Tatou server recorded repeated `rate_limit.exceeded` events associated with source IP address `10.100.11.15`.

The available Docker logs contain **600 rate-limit violation events** from this source.

### Timeline

| Observation              | Time (UTC)                              |
| ------------------------ | --------------------------------------- |
| First recorded violation | 12 October 2026, 16:53:23               |
| Last recorded violation  | 12 October 2026, 17:15:58               |
| Observed duration        | Approximately 22 minutes and 35 seconds |

### Evidence

The recorded events contain the following fields:

- `event`: `rate_limit.exceeded`
- `source_ip`: `10.100.11.15`
- `outcome`: `denied`
- `request_count`: `500`
- `window_seconds`: `60`
- `timestamp` and `request_id` for individual events

All 600 events in the collected evidence were associated with this source IP, and all had the recorded outcome `denied`.

The event count represents logged rate-limit violations, not the total number of HTTP requests sent.

### Detection and Analysis

The structured security logs made it possible to identify the event type, source IP, recorded outcome, and time range.

The repeated violations are consistent with excessive or automated request activity. Such activity may indicate attempted resource exhaustion, aggressive scanning, or testing of the rate-limiting mechanism.

The available evidence does not establish the source's intent or prove that a successful attack occurred.

### Defensive Response

Tatou's existing rate-limiting mechanism recorded the requests as denied.

This provides evidence that the rate limiter responded to excessive request activity. The investigation did not establish whether the service experienced performance degradation during the event.

## 3. Incident 2 — Repeated Authentication Failures

### Description

Previously captured screenshots show multiple `authentication.failure` events.

In particular, source IP `10.100.11.11` generated several events with reason `invalid_credentials` on 10 October 2026, approximately between 10:02:32 and 10:02:49 UTC.

Other screenshots also show authentication failures associated with `10.100.11.15`, including `invalid_credentials` and `expired_token` events.

### Detection and Analysis

The authentication security events identify failed authentication attempts and their recorded reasons.

Repeated invalid credentials from one source over a short period may be consistent with password guessing or automated authentication testing. However, legitimate user errors and authorized security testing are also possible explanations.

The available screenshots do not prove malicious intent, successful account compromise, or the identity of the source.

### Evidence Limitations

The currently collected Docker log file contains 600 rate-limit violations but no authentication-failure events.

Therefore, this incident is supported by previously captured screenshots rather than by the current exported log file.

## 4. Investigation and Service Health Verification

Following the observed security events, the deployment was inspected using Docker Compose and HTTP requests.

### Container Status

The following containers were running during verification:

- Tatou application server
- MariaDB database, reporting healthy status
- phpMyAdmin
- Test container

### Application Health

On 12 October 2026 at 20:40:46 GMT, the application's `/healthz` endpoint returned HTTP 200 with:

```json
{ "db_connected": true, "message": "The server is up and running." }
```

A request to `/api/get-version/monitoring-test-invalid-link` also returned HTTP 404, the expected result for a nonexistent document link.

These observations confirm that the application responded and reported a working database connection at the time of verification.

They do not prove uninterrupted availability during the earlier suspicious activity.

## 5. Response and Recovery

### Actions Performed

1. Collected relevant security events from Docker logs.
2. Counted and grouped the recorded events by event type and source IP.
3. Established the first and last recorded timestamps.
4. Reviewed the recorded rate-limiting outcomes.
5. Inspected Docker container status.
6. Verified the application's health endpoint and database connectivity.
7. Verified that the application handled an invalid document link as expected.

### Containment

The existing rate limiter recorded the excessive requests as denied. No additional IP block or firewall rule was applied during this investigation.

### Recovery

No service failure requiring recovery was established during the investigation, so no restart or restoration was performed.

If a future incident causes service degradation, the operator should inspect container logs and health status, determine the affected component, and perform an appropriate recovery action, such as restarting a failed service. Recovery should then be verified through `/healthz`, database connectivity, and relevant application functionality.

A restart should not be used automatically when the service is functioning normally, because unnecessary restarts can interrupt legitimate users and remove useful runtime context.

## 6. Lessons Learned and Limitations

The structured logging implementation provided useful evidence for identifying suspicious request patterns and investigating their outcomes.

The incident also demonstrated several limitations:

- Source IP addresses do not establish attacker identity.
- Rate-limit events do not reveal the total number of requests or their intent.
- Current Docker log retention may not preserve all historical authentication events.
- A successful health check after an incident does not establish availability throughout the incident.
- Manual log inspection requires an operator to review events; automated alerting has not been demonstrated.

Potential future improvements include centralized log retention, automated alerts for repeated authentication failures and rate-limit violations, and additional service-availability telemetry.

## 7. Conclusion

Tatou's deployed security logging captured 600 rate-limit violations from a single recorded source IP over approximately 22 minutes and 35 seconds. The recorded outcomes were all `denied`.

Previously captured authentication-failure events provided additional evidence of suspicious activity.

The investigation demonstrated that the logs could be used to identify, group, and analyze security events. Subsequent health checks confirmed that the application and database were functioning at the time of verification.

No successful compromise or incident-related outage was established by the available evidence.
