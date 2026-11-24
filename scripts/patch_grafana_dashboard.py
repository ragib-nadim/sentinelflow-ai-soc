#!/usr/bin/env python3
"""
SentinelFlow AI SOC: Grafana Dashboard API Patcher & Verifier
Programmatically updates and verifies the SentinelFlow_AI_SOC dashboard (UID: adktrrf).
"""
import json
import os
import requests

GRAFANA_URL = os.getenv("GRAFANA_URL", "http://192.168.0.50:3000")
GRAFANA_USER = os.getenv("GRAFANA_USER", "admin")
GRAFANA_PASS = os.getenv("GRAFANA_PASS", "admin")
DASHBOARD_UID = "adktrrf"


def push_dashboard(dashboard_path: str):
    with open(dashboard_path, "r", encoding="utf-8") as f:
        dash = json.load(f)

    dash.pop("id", None)
    payload = {
        "dashboard": dash,
        "folderId": 0,
        "overwrite": True,
        "message": "Automated sync from sentinelflow-ai-soc repository"
    }

    resp = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        auth=(GRAFANA_USER, GRAFANA_PASS),
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=15
    )
    resp.raise_for_status()
    print("Dashboard synced successfully:", resp.json())


if __name__ == "__main__":
    push_dashboard("grafana/dashboards/SentinelFlow_AI_SOC.json")
