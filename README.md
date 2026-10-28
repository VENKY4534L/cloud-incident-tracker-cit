# Cloud Incident Tracker (CIT)

Serverless IT incident-management API starter project using Python, Flask, Firestore, Cloud Run, Pub/Sub, Cloud Functions, IAM, and Cloud Logging.

**Status:** This repository contains runnable application code and deployment guidance. It does not create GCP resources automatically. Deploy and test in your own Google Cloud project before claiming it is deployed or production-ready.

## Architecture
Client → REST API on Cloud Run → Firestore  
Incident lifecycle event → Pub/Sub → Cloud Function consumer  
Runtime service account → least-privilege IAM  
Application logs → Cloud Logging

## Local run (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:USE_FIRESTORE = "false"
python main.py
```
Open http://127.0.0.1:8080. In-memory mode loses data on restart.

## API endpoints
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/incidents` | Create incident |
| GET | `/incidents` | List incidents |
| GET | `/incidents/<incident_id>` | Retrieve incident |
| PATCH | `/incidents/<incident_id>` | Update incident |
| DELETE | `/incidents/<incident_id>` | Delete incident |

Example JSON: `{"title":"VPN issue","description":"Cannot connect","severity":"high","status":"open","reported_by":"demo-user"}`

## Enable Firestore
1. Create a GCP project and enable Firestore in Native mode.
2. For local development run `gcloud auth application-default login`.
3. Set `USE_FIRESTORE=true` and `GOOGLE_CLOUD_PROJECT=your-project-id`.
4. Run `python main.py`.

## Deploy to Cloud Run
Enable APIs:
```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com firestore.googleapis.com pubsub.googleapis.com
```
Create Firestore in Native mode, then deploy:
```bash
gcloud run deploy cit-api --source . --region asia-south1
```
Prefer authenticated access for real use. Configure `USE_FIRESTORE=true`, `GOOGLE_CLOUD_PROJECT`, and a dedicated runtime service account with least-privilege access in Cloud Run settings.

## Pub/Sub and Cloud Functions
Create a topic such as `cit-incident-events`, set `PUBSUB_TOPIC` and `GOOGLE_CLOUD_PROJECT`, and grant the Cloud Run service account permission to publish. The `cloud_function/` directory contains a Pub/Sub event handler example; deploy it with the current supported Cloud Functions Gen2 CLI syntax for your environment.

## Security and limitations
- This sample API does not implement caller authentication/authorization. Do not expose it publicly with real incident data.
- Do not commit credentials, service-account keys, tokens, or real incident records.
- Add pagination, rate limiting, schema validation, integration tests, and alerting before production.
- Pub/Sub publishing is optional; a publish failure is logged but does not roll back the incident write.
- Use Cloud Logging to inspect runtime logs and troubleshooting details.

## Tests
```powershell
python -m unittest discover -s tests -v
```
