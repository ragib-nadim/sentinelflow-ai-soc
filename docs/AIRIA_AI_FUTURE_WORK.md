# Future Work: Airia AI Autonomous SOC Integration (Phase 3)

## 1. Motivation & Problem Statement
While Wazuh and NetAlertX provide rich endpoint and network telemetry, raw SIEM logs still require manual analyst triage to distinguish benign administrative file changes from ransomware staging, unauthorized lateral movement, or rogue device connections. **Phase 3** integrates **Airia AI** as an autonomous Tier-1/Tier-2 SOC analyst directly into the SentinelFlow pipeline.

## 2. Planned End-to-End Airia AI Workflow
1. **Alert Interception (`wazuh-integratord`):**
   - Wazuh Manager monitors `alerts.json` and triggers `custom-airia` (`airia_integration/wazuh_airia_webhook.py`) whenever an alert meets severity thresholds (`rule.level >= 7`, e.g., FIM checksum modification or deletion, brute-force attempts, or new unknown MAC alerts).
2. **Context Enrichment (Cross-Source Correlation):**
   - Before invoking Airia AI, the integration bridge queries NetAlertX (`http://192.168.0.50:20212/devices`) using the offending agent's IP/MAC (`192.168.0.102`) to attach network posture (known vs. rogue device, last seen timestamp, vendor OUI) to the Wazuh alert payload.
3. **Airia AI Agentic Reasoning Pipeline:**
   - **Agent 1 — Threat Classifier & MITRE Mapper:** Maps the event to MITRE ATT&CK techniques (e.g., `T1486` Data Encrypted for Impact, `T1070.004` File Deletion, `T1200` Hardware Additions).
   - **Agent 2 — Risk Scoring Engine:** Computes a normalized `0–100` risk score (`airia_risk_score`) and severity label (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) with confidence justification.
   - **Agent 3 — Remediation & SOAR Advisor:** Generates executable containment steps (e.g., PowerShell process quarantine, Wazuh Active Response `firewall-drop`, or NetAlertX VLAN isolation).
4. **Closed-Loop Grafana Visualization:**
   - Airia AI posts the structured JSON verdict (`airia_integration/airia_response_schema.json`) back to OpenSearch (`airia-triage-alerts-*`) or a lightweight FastAPI webhook cache on `192.168.0.50:8085`.
   - This immediately populates the two pre-built panels on `SentinelFlow_AI_SOC`:
     - **Latest Airia risk** (Stat panel displaying `0–100` dynamic threat score with color thresholds)
     - **Latest alert name** (Stat/Text panel displaying the AI-summarized incident title and MITRE technique ID)

## 3. Additional Future Research Directions
- **Automated Wazuh Active Response:** Triggering automated host isolation or process termination when `airia_risk_score >= 85` with human-in-the-loop approval via Slack/Telegram.
- **Rogue Device + FIM Correlation:** Raising critical alerts automatically if a `New` unknown MAC appears in NetAlertX within 60 seconds of sensitive file modifications on `DESKTOP-HOQHBSK`.
- **Local Small Language Model (SLM) Fallback:** Deploying an on-premise quantized model (Llama-3 / Mistral via Ollama on Ubuntu) as an air-gapped fallback when cloud Airia API connectivity is unavailable.
