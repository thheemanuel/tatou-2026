# Tatou — Security Monitoring and Incident Response Runbook

## 1. Purpose

This runbook describes how to monitor the Tatou deployment, investigate suspicious security events, verify service health, and respond to operational problems.

Tatou uses structured JSON security events emitted by the Flask application and accessible through Docker Compose logs.

## 2. Monitoring the Application

### View recent server logs

```bash
docker compose logs --tail=100 server
```

### Follow server logs in real time

```bash
docker compose logs -f server
```

### Find authentication failures

```bash
docker compose logs --no-color server | grep '"event":"authentication.failure"'
```

### Find rate-limit violations

```bash
docker compose logs --no-color server | grep '"event":"rate_limit.exceeded"'
```

### Check container status

```bash
docker compose ps
```

### Check application and database health

```bash
curl -i http://localhost:5000/healthz
```

A healthy response should return HTTP 200 and report `"db_connected":true`.

## 3. Security Events to Investigate

| Event                    | Possible concern                                                |
| ------------------------ | --------------------------------------------------------------- |
| `authentication.failure` | Invalid credentials, expired tokens, or repeated login attempts |
| `rate_limit.exceeded`    | Excessive request activity                                      |
| `authorization.denied`   | Attempts to access unauthorized resources                       |
| `document.upload`        | Unexpected or unusually frequent uploads                        |
| `plugin.load`            | Unexpected plugin-loading activity                              |
| `rmap.authentication`    | Failed or suspicious RMAP authentication                        |
| `secret_link.access`     | Invalid or repeated secret-link access                          |

Other authentication-success events can help establish context during an investigation.

An individual event is not automatically an attack. Operators should evaluate frequency, source, timing, outcome, and surrounding activity.

## 4. Incident Investigation Procedure

When suspicious events are found:

1. Record the event type and timestamps, including the timezone.
2. Identify the recorded source IP and relevant request IDs.
3. Determine the number of events and their time range.
4. Examine event outcomes and reasons.
5. Compare the events with expected application behavior and known testing activity.
6. Preserve relevant evidence while avoiding unnecessary collection of sensitive information.
7. Verify whether the application and database remain operational.
8. Document findings, actions, and unresolved questions in an incident report.

Do not assume that an IP address identifies a particular attacker or that suspicious activity proves a successful compromise.

## 5. Response and Containment

For repeated authentication failures:

- Investigate the frequency and affected accounts, if that information is available.
- Check for subsequent successful authentication events.
- Determine whether authorized testing could explain the activity.
- Consider temporary restrictions only when justified and authorized.

For excessive request activity:

- Confirm whether `rate_limit.exceeded` events report denied requests.
- Check service health and signs of performance degradation.
- Preserve relevant logs.
- Consider additional traffic restrictions if the existing rate limiter is insufficient, following team authorization.

For unexpected authorization or plugin activity:

- Investigate the affected functionality and available context.
- Preserve logs and assess whether further access should be restricted.
- Escalate suspected compromise to the project team.

## 6. Recovery and Verification

First determine whether the service has actually failed. Do not restart a healthy service unnecessarily.

Check:

```bash
docker compose ps
curl -i http://localhost:5000/healthz
```

If a service has failed and the project team approves restarting it, an operator may use:

```bash
docker compose restart server
```

After restarting, verify:

```bash
docker compose ps
curl -i http://localhost:5000/healthz
docker compose logs --tail=50 server
```

Confirm that the application responds, the database connection is healthy, and no relevant startup errors are present.

If a restart does not resolve the problem, investigate the logs and underlying cause rather than repeatedly restarting the service. Database or document restoration should only be performed using an approved backup and recovery procedure.

## 7. Evidence from 12 October 2026

The deployment recorded 600 `rate_limit.exceeded` events associated with one source IP between 16:53:23 and 17:15:58 UTC.

All 600 recorded outcomes were `denied`.

Later checks showed that the application server was running, MariaDB reported healthy status, and `/healthz` returned HTTP 200 with `"db_connected":true`.

No incident-related outage was established, and no recovery restart was performed.

Supporting material:

- `incident-report.md`
- `evidence/rate-limit-excerpt.jsonl`

## 8. Limitations and Improvements

Current monitoring relies on an operator reviewing Docker logs. Automatic alerting and long-term centralized log retention have not been demonstrated.

Future improvements could include:

- Alerts for repeated authentication failures and rate-limit violations.
- Centralized log retention and rotation policies.
- Availability and resource-usage metrics.
- A documented, tested backup-restoration procedure.
- Correlation of security events with application and infrastructure performance.

These are proposed improvements, not capabilities claimed to be implemented.
