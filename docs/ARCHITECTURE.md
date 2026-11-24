# SentinelFlow AI SOC — Technical Architecture & Engineering Log

## 1. Hybrid Lab Infrastructure
SentinelFlow operates across a bridged Layer-2 LAN (`192.168.0.0/24`) connecting a Windows 11 host (`DESKTOP-HOQHBSK`, `192.168.0.102`) and an Ubuntu Server virtual machine (`node01`, `192.168.0.50`). Using a bridged network adapter allows NetAlertX's ARP scanner to observe real physical and virtual MAC addresses across the subnet without NAT translation masking host identities.

## 2. Telemetry Ingestion Pipelines

### A. Endpoint File Integrity Monitoring (Wazuh v4.14.10)
- **Agent Configuration (`ossec.conf`):** Configured `<syscheck>` with `realtime="yes"`, `check_all="yes"`, and `report_changes="yes"` targeting `E:\Personal Projects\sentinelflow-ai-soc\monitored_directory`.
- **Database Synchronization:** Enabled `<synchronization>` every `5m` (`max_eps=10`) to ensure state consistency between the Windows agent and Ubuntu Wazuh Manager.
- **Triggered Rules:**
  - `Rule 554` (Level 5): File added to the system.
  - `Rule 550` (Level 7): Integrity checksum changed (SHA-256 before/after diff recorded).
  - `Rule 553` (Level 7): File deleted from monitored path.
- **Indexer Storage:** Alerts are indexed in OpenSearch under `wazuh-alerts-4.x-*` with `@timestamp` as the primary time-series field.

### B. Network Asset Discovery (NetAlertX)
- **Scanner Engine:** `ARPSCAN` scheduled via cron (`*/5 * * * *`) with `ARPSCAN_SET_ALWAYS` locked to `devMac` and `devLastIP`.
- **REST API Exposure:** Exposes device inventory JSON at `http://192.168.0.50:20212/devices`, tracking 9 active devices (`Ubuntu`, `_gateway`, and local subnet hosts) alongside `Full MAC`, `Last IP`, `Status`, and `Source Plugin`.

### C. Unified Visualization Layer (Grafana OSS)
- **OpenSearch Datasource (`SentinelFlow-Wazuh-Indexer-2`):** Connects to `https://192.168.0.50:9200` using Basic Auth (`admin`), querying `wazuh-alerts-*` for real-time FIM event counts (`793–796` events) and detailed SHA-256 audit tables.
- **Infinity Datasource (`NetAlertX Infinity`, UID `cg5b0m1omr6kgb`):** Queries `http://192.168.0.50:20212/devices` via HTTP GET (`JSON` / `JSONata`).
- **Troubleshooting & Query Engineering:**
  - Initially, filtering `devices[$lowercase($string(devStatus)) in ["online", "on-line"]]` returned empty frames (`[[null]]`) because NetAlertX's `/devices` schema stores status indicators differently or leaves `devStatus` null when queried directly via JSONata root predicates.
  - Resolved the **Online devices** panel (`9`) by mapping `devName` / `devices` rows cleanly and applying Grafana's native `Reduce / Calculation -> Count` reducer on the Stat panel.
  - Resolved **Device inventory** and **Device status** panels by aligning Infinity column selectors (`status as Status`, `count as Count`) and Pie Chart label/value mappings.
