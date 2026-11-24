#!/usr/bin/env python3
"""
SentinelFlow AI SOC (Phase 3 Future Work): Wazuh -> Airia AI Triage Bridge
Deployed on Wazuh Manager (/var/ossec/integrations/custom-airia) to forward
high-severity alerts to Airia AI and index enriched triage results back into OpenSearch.
"""
import json
import os
import sys
from datetime import datetime, timezone
import requests

AIRIA_API_URL = os.getenv("AIRIA_API_URL", "https://api.airia.ai/v1/pipelines/sentinelflow-triage/execute")
AIRIA_API_KEY = os.getenv("AIRIA_API_KEY", "YOUR_AIRIA_API_KEY")
NETALERTX_API = os.getenv("NETALERTX_API", "http://192.168.0.50:20212/devices")
OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "https://192.168.0.50:9200/airia-triage-alerts/_doc")
OPENSEARCH_AUTH = (os.getenv("OS_USER", "admin"), os.getenv("OS_PASS", "CHANGE_ME"))


def enrich_with_netalertx(agent_ip: str) -> dict:
    """Cross-correlate offending endpoint IP with NetAlertX LAN inventory."""
    try:
        r = requests.get(NETALERTX_API, timeout=5)
        devices = r.json().get("devices", [])
        for dev in devices:
            if dev.get("devLastIP") == agent_ip:
                return {
                    "mac": dev.get("devMac"),
                    "device_name": dev.get("devName"),
                    "device_type": dev.get("devType"),
                    "known_asset": True
                }
    except Exception as exc:
        return {"known_asset": False, "lookup_error": str(exc)}
    return {"known_asset": False}


def run_airia_triage(alert: dict) -> dict:
    agent_ip = alert.get("agent", {}).get("ip", "unknown")
    asset_context = enrich_with_netalertx(agent_ip)

    prompt_payload = {
        "alert_id": alert.get("id"),
        "rule": alert.get("rule", {}),
        "agent": alert.get("agent", {}),
        "syscheck": alert.get("syscheck", {}),
        "network_context": asset_context
    }

    headers = {
        "Authorization": f"Bearer {AIRIA_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(AIRIA_API_URL, headers=headers, json={"input": json.dumps(prompt_payload)}, timeout=30)
    response.raise_for_status()
    ai_result = response.json()

    return {
        "@timestamp": datetime.now(timezone.utc).isoformat(),
        "source_alert_id": alert.get("id"),
        "agent_name": alert.get("agent", {}).get("name"),
        "agent_ip": agent_ip,
        "airia_risk_score": ai_result.get("risk_score", 75),
        "airia_alert_title": ai_result.get("alert_title", alert.get("rule", {}).get("description")),
        "mitre_techniques": ai_result.get("mitre_techniques", ["T1070.004"]),
        "remediation_steps": ai_result.get("remediation_steps", []),
        "network_context": asset_context
    }


def main():
    if len(sys.argv) < 2:
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        alert = json.load(f)

    triage_doc = run_airia_triage(alert)
    requests.post(OPENSEARCH_URL, auth=OPENSEARCH_AUTH, json=triage_doc, verify=False, timeout=10)


if __name__ == "__main__":
    main()
