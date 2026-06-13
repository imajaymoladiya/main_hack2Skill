# Google Cloud Platform (GCP) Deployment Guide 🚀

This guide details how to deploy **ZenExam AI** on Google Cloud Platform using Google App Engine (GAE) or Google Cloud Run, alongside security practices using Google Secret Manager.

---

## 1. Deploying to Google App Engine (GAE)
Google App Engine is a managed Platform-as-a-Service (PaaS) that automatically scales based on traffic.

### Prerequisites
- Install the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install).
- Initialize your CLI session:
  ```bash
  gcloud init
  ```

### Deployment Commands
1. Open PowerShell/Terminal at the root directory of the project.
2. Initialize App Engine in your target GCP project:
   ```bash
   gcloud app create --region=us-central
   ```
3. Deploy the application:
   ```bash
   gcloud app deploy
   ```
4. Access the live App Engine URL:
   ```bash
   gcloud app browse
   ```

---

## 2. Deploying to Google Cloud Run (Serverless Container)
Google Cloud Run runs stateless Docker containers on demand, offering high scalability and CPU/Memory efficiency.

### Deployment Commands
1. Navigate to the project root directory.
2. Build, containerize, and deploy the application in a single step using Google Cloud Build:
   ```bash
   gcloud run deploy zenexam-ai --source . --region=us-central1 --allow-unauthenticated
   ```
3. Confirm prompts to create an Artifact Registry repository by typing **Y**.
4. Once complete, the CLI will output the live Cloud Run URL (e.g. `https://zenexam-ai-xxxx-uc.a.run.app`).

---

## 3. Configuring Secrets in GCP Secret Manager (Safe Practices)
Never commit sensitive keys like `GROQ_API_KEY` to public repositories. Secure them using GCP Secret Manager:

1. Go to the **GCP Console** > **Secret Manager**.
2. Click **Create Secret**:
   - Secret Name: `GROQ_API_KEY`
   - Value: *[Insert your Groq API Key]*
3. Open **Cloud Run** > Select **zenexam-ai** service > Click **Edit & Deploy New Revision**.
4. Navigate to **Variables & Secrets** > **Reference a Secret**:
   - Select `GROQ_API_KEY`.
   - Map it as an Environment Variable named `GROQ_API_KEY`.
5. Click **Deploy**. Your keys are now stored securely in KMS and dynamically injected into the container at runtime.
