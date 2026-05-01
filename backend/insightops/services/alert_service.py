from collections import Counter


def generate_alerts(incidents):

    if not incidents:
        return {
            "alerts": []
        }

    severities = [i.severity for i in incidents]

    counts = Counter(severities)

    alerts = []

    # Critical threshold
    if counts.get("CRITICAL", 0) >= 3:
        alerts.append(
            "CRITICAL ALERT: Multiple critical incidents detected"
        )

    # High threshold
    if counts.get("HIGH", 0) >= 5:
        alerts.append(
            "WARNING: High number of HIGH severity incidents"
        )

    # Outage pattern
    outage_count = 0

    for incident in incidents:

        if incident.category == "Outage":
            outage_count += 1

    if outage_count >= 3:
        alerts.append(
            "OUTAGE ALERT: Recurring outage incidents detected"
        )

    return {
        "alerts": alerts
    }