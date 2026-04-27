# Privacy Policy

Effective date: 2026-03-12

Valkyrie Ballistics is designed to work offline by default. This policy
explains what data is stored, when data may be transmitted, and how you
can control it.

## 1. Data stored locally
The software stores the following locally:
- Project data in the selected project folder (including reloading.db).
- Configuration files in the app config directory.
- Diagnostic logs in the logs folder.
- Export Pack archives that you create.

## 2. Optional research data sharing
If research opt-in is enabled, the software may create sanitized research
payloads and queue them locally. These payloads are sent only to a
user-configured endpoint. If no endpoint is configured, payloads are
saved to a local research_payloads.jsonl file.

## 3. Network features
Some features call third-party services when used, such as:
- Terrain map and elevation lookups.
- Weather data providers (for example, OpenWeather or met.no).

These requests may expose your IP address to those providers. Use these
features only if you are comfortable with third-party network calls.

## 4. Data sharing and disclosure
The publisher does not collect your data by default. Data is shared only
when you:
- Enable research opt-in and configure a remote endpoint.
- Export and manually share files.

## 5. Data retention and deletion
- To delete project data, remove the project folder.
- To delete logs, clear the logs folder.
- To delete queued research payloads, delete research_payloads.jsonl.
- Remote endpoints are controlled by the user; delete data at the
  destination using its own tools.

## 6. Security
The software stores data locally. You are responsible for backups,
device security, and access control to the project folders.

## 7. Changes to this policy
This policy may be updated for future releases. Check the effective date
above for the current version.
