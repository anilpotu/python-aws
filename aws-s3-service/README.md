# AWS S3 Service

REST API for S3 file operations, user data management (personal, financial, health), PostgreSQL persistence, SNS notifications, and SQS message processing, built with FastAPI and Python 3.12.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Local Development](#local-development)
- [Configuration](#configuration)
- [Infrastructure](#infrastructure)
  - [Prerequisites](#prerequisites)
  - [Terraform Modules](#terraform-modules)
  - [Provisioning Infrastructure](#provisioning-infrastructure)
- [Deployment](#deployment)
  - [ECS Fargate (Jenkins)](#ecs-fargate-jenkins)
  - [EKS Kubernetes (GitLab)](#eks-kubernetes-gitlab)
- [Istio Service Mesh](#istio-service-mesh)
- [Environment Configurations](#environment-configurations)
- [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
                    ┌──────────────┐
                    │   Clients    │
                    └──────┬───────┘
                           │
              ┌────────────┴────────────┐
              │                         │
     ┌────────▼────────┐     ┌──────────▼─────────┐
     │   ALB (ECS)     │     │ Istio Gateway (EKS) │
     └────────┬────────┘     └──────────┬──────────┘
              │                         │
     ┌────────▼────────┐     ┌──────────▼──────────┐
     │  ECS Fargate    │     │   EKS Pods          │
     │  ┌────────────┐ │     │  ┌────────────────┐ │
     │  │ FastAPI App │ │     │  │  FastAPI App   │ │
     │  │  Port 8000  │ │     │  │   Port 8000   │ │
     │  └─────┬──────┘ │     │  └──────┬─────────┘ │
     └────────┼────────┘     └─────────┼───────────┘
              │                        │
     ┌────────▼────────────────────────▼────────────────────┐
     │                    AWS Services                      │
     │  ┌─────────┐  ┌─────────┐  ┌──────────┐            │
     │  │   S3    │  │   SNS   │──│   SQS    │            │
     │  │ (JSON)  │  │ (Notify)│  │(Produce/ │            │
     │  │personal/│  └─────────┘  │Consume)  │            │
     │  │financial│               └──────────┘            │
     │  │health   │                                        │
     │  └─────────┘                                        │
     └──────────────────────────────────────────────────────┘
              │
     ┌────────▼──────────────┐
     │     PostgreSQL        │
     │  ┌──────────────────┐ │
     │  │ users_personal   │ │
     │  │ users_financial  │ │
     │  │ users_health     │ │
     │  └──────────────────┘ │
     └───────────────────────┘
```

The application supports two deployment targets:

- **ECS Fargate** — serverless containers behind an ALB, deployed via Jenkins and Terraform
- **EKS (Kubernetes)** — pods with Istio service mesh, deployed via GitLab CI/CD and Helm

Both share the same VPC, ECR, and AWS messaging resources (S3, SNS, SQS), and connect to a PostgreSQL database for persistent user data storage.

---

## API Endpoints

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check — returns `{"message": "ok"}` |

### S3 File Operations

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/s3/{key}` | Read any JSON file from S3 by key |
| `PUT` | `/s3/{key}` | Merge-update a JSON file in S3, then notify via SNS |
| `POST` | `/s3/upload` | Upload a new JSON file to S3, then notify via SNS |

### SNS

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/sns/publish` | Publish a custom message to the SNS topic |

### User Data — S3 Reads

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/users/{user_id}/s3/personal` | Read `users/personal/{user_id}.json` from S3 |
| `GET` | `/users/{user_id}/s3/financial` | Read `users/financial/{user_id}.json` from S3 |
| `GET` | `/users/{user_id}/s3/health` | Read `users/health/{user_id}.json` from S3 |
| `GET` | `/users/{user_id}/s3/all` | Read and merge all three S3 files for a user |

### User Data — PostgreSQL (Personal Information)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/users/personal` | Insert personal info (name, email, phone, address, date of birth) |
| `GET` | `/users/{user_id}/personal` | Fetch personal info from the database |
| `PATCH` | `/users/{user_id}/personal` | Partial update of personal info |
| `DELETE` | `/users/{user_id}/personal` | Delete personal info |

### User Data — PostgreSQL (Financial Information)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/users/financial` | Insert financial info (account number, credit score, income, debt) |
| `GET` | `/users/{user_id}/financial` | Fetch financial info from the database |
| `PATCH` | `/users/{user_id}/financial` | Partial update of financial info |
| `DELETE` | `/users/{user_id}/financial` | Delete financial info |

### User Data — PostgreSQL (Health Information)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/users/health` | Insert health info (blood type, conditions, medications, allergies) |
| `GET` | `/users/{user_id}/health` | Fetch health info from the database |
| `PATCH` | `/users/{user_id}/health` | Partial update of health info |
| `DELETE` | `/users/{user_id}/health` | Delete health info |

### User Data — Aggregated & SQS

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/users/{user_id}` | Fetch all stored records (personal + financial + health) for a user |
| `POST` | `/users/sqs/send` | Fetch DB records and publish them to SQS (`data_type`: `personal`, `financial`, `health`, or `all`) |

A background SQS consumer long-polls the configured queue and processes incoming messages automatically on startup.

---

## Database Schema

Tables are created automatically on application startup if they do not exist.

### `users_personal`

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | TEXT (PK) | Unique user identifier |
| `name` | TEXT | Full name |
| `email` | TEXT | Email address |
| `phone` | TEXT | Phone number |
| `address` | TEXT | Physical address |
| `date_of_birth` | DATE | Date of birth |
| `created_at` | TIMESTAMPTZ | Row creation timestamp |
| `updated_at` | TIMESTAMPTZ | Last update timestamp |

### `users_financial`

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | TEXT (PK) | Unique user identifier |
| `account_number` | TEXT | Bank account number |
| `credit_score` | INTEGER | Credit score |
| `annual_income` | NUMERIC(15,2) | Annual income |
| `total_debt` | NUMERIC(15,2) | Total outstanding debt |
| `created_at` | TIMESTAMPTZ | Row creation timestamp |
| `updated_at` | TIMESTAMPTZ | Last update timestamp |

### `users_health`

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | TEXT (PK) | Unique user identifier |
| `blood_type` | TEXT | Blood type (e.g. `O+`) |
| `conditions` | TEXT[] | List of medical conditions |
| `medications` | TEXT[] | List of current medications |
| `allergies` | TEXT[] | List of known allergies |
| `created_at` | TIMESTAMPTZ | Row creation timestamp |
| `updated_at` | TIMESTAMPTZ | Last update timestamp |

---

## Project Structure

```
aws-s3-service/
├── app/                          # Application source code
│   ├── main.py                   # FastAPI app entry point + DB pool + SQS lifespan
│   ├── config.py                 # Settings via pydantic-settings
│   ├── routers/
│   │   ├── health.py             # GET /health
│   │   ├── s3.py                 # Generic S3 CRUD endpoints
│   │   ├── sns.py                # SNS publish endpoint
│   │   └── users.py              # User data endpoints (S3 reads, DB CRUD, SQS send)
│   ├── schemas/
│   │   └── models.py             # Pydantic request/response models
│   └── services/
│       ├── s3_service.py         # S3 read/update/upload + typed readers per data domain
│       ├── sns_service.py        # SNS publish logic
│       ├── sqs_service.py        # SQS consumer (poll) + producer (send_message)
│       └── db_service.py         # PostgreSQL CRUD via asyncpg (personal/financial/health)
│
├── terraform/                    # Infrastructure as Code
│   ├── modules/
│   │   ├── vpc/                  # VPC, subnets, NAT, IGW
│   │   ├── ecr/                  # Container registry
│   │   ├── messaging/            # S3 bucket, SNS topic, SQS queue
│   │   ├── iam/                  # ECS IAM roles
│   │   ├── alb/                  # Application Load Balancer
│   │   ├── ecs/                  # ECS Fargate cluster + service
│   │   ├── eks/                  # EKS cluster + node group
│   │   └── irsa/                 # IAM Roles for Service Accounts
│   └── environments/
│       ├── dev/                  # Dev environment config
│       └── prod/                 # Prod environment config
│
├── helm/aws-s3-service/          # Helm chart for Kubernetes
│   ├── Chart.yaml
│   ├── values.yaml               # Default values
│   ├── values-dev.yaml           # Dev overrides
│   ├── values-prod.yaml          # Prod overrides
│   └── templates/                # K8s + Istio manifests
│
├── Dockerfile                    # Container image
├── docker-compose.yml            # Local dev with LocalStack
├── Jenkinsfile                   # Jenkins CI/CD (ECS deployment)
├── .gitlab-ci.yml                # GitLab CI/CD (EKS deployment)
├── requirements.txt              # Python dependencies
└── .env.example                  # Environment variable template
```

---

## Local Development

### Prerequisites

- Docker and Docker Compose
- Python 3.12+ (for running outside Docker)
- PostgreSQL 14+ (or use a Docker container)

### Running with Docker Compose

Docker Compose starts the app alongside [LocalStack](https://localstack.cloud/), which emulates S3, SNS, and SQS locally.

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Set the required values in `.env`:
   ```env
   S3_BUCKET_NAME=my-bucket
   SNS_TOPIC_ARN=arn:aws:sns:us-east-1:000000000000:my-topic
   SQS_QUEUE_URL=http://localstack:4566/000000000000/my-queue
   DATABASE_URL=postgresql://postgres:password@postgres:5432/userdata
   ```

3. Start the services:
   ```bash
   docker-compose up --build
   ```

4. The API is available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

5. Create the required LocalStack resources:
   ```bash
   # Create S3 bucket
   aws --endpoint-url=http://localhost:4566 s3 mb s3://my-bucket

   # Create SNS topic
   aws --endpoint-url=http://localhost:4566 sns create-topic --name my-topic

   # Create SQS queue
   aws --endpoint-url=http://localhost:4566 sqs create-queue --queue-name my-queue
   ```

6. The PostgreSQL tables (`users_personal`, `users_financial`, `users_health`) are created automatically when the application starts.

### Running without Docker

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration, including DATABASE_URL
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Configuration

All configuration is loaded from environment variables (or a `.env` file) via `pydantic-settings`.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AWS_REGION` | No | `us-east-1` | AWS region |
| `AWS_ACCESS_KEY_ID` | No | — | Static AWS credentials (not needed on ECS/EKS) |
| `AWS_SECRET_ACCESS_KEY` | No | — | Static AWS credentials (not needed on ECS/EKS) |
| `AWS_ENDPOINT_URL` | No | — | Custom endpoint for LocalStack (`http://localstack:4566`) |
| `S3_BUCKET_NAME` | **Yes** | — | Target S3 bucket name |
| `SNS_TOPIC_ARN` | **Yes** | — | Full SNS topic ARN |
| `SQS_QUEUE_URL` | **Yes** | — | Full SQS queue URL |
| `DATABASE_URL` | **Yes** | — | PostgreSQL DSN, e.g. `postgresql://user:pass@host:5432/db` |

**Credential handling in production:**

- **ECS Fargate** — credentials are provided by the ECS task role. No static keys needed.
- **EKS** — credentials are provided via IRSA (IAM Roles for Service Accounts). The Kubernetes `ServiceAccount` is annotated with the IAM role ARN, and pods inherit it automatically.

---

## Infrastructure

### Prerequisites

Before deploying, ensure you have:

1. **AWS CLI** configured with appropriate permissions
2. **Terraform** >= 1.5 installed
3. **kubectl** installed (for EKS deployments)
4. **Helm** >= 3.x installed (for EKS deployments)
5. **Istio** CLI (`istioctl`) installed (if using Istio)

### Create the Terraform State Bucket

The Terraform backend requires an S3 bucket for state storage. Create it once, manually:

```bash
aws s3api create-bucket \
  --bucket aws-s3-service-terraform-state \
  --region us-east-1

aws s3api put-bucket-versioning \
  --bucket aws-s3-service-terraform-state \
  --versioning-configuration Status=Enabled
```

### Terraform Modules

| Module | Resources | Purpose |
|--------|-----------|---------|
| **vpc** | VPC, 2 public + 2 private subnets, IGW, NAT gateway, route tables | Network foundation |
| **ecr** | ECR repository, lifecycle policy | Container image registry |
| **messaging** | S3 bucket (versioned, encrypted), SNS topic, SQS queue + DLQ, SNS→SQS subscription | AWS service resources |
| **iam** | ECS execution role, ECS task role with S3/SNS/SQS permissions | ECS IAM |
| **alb** | ALB, target group (health check on `/health`), HTTP listener, security group | ECS load balancing |
| **ecs** | ECS Fargate cluster, task definition, service, CloudWatch log group | ECS compute |
| **eks** | EKS cluster, managed node group, OIDC provider | Kubernetes compute |
| **irsa** | IAM role for K8s service account with S3/SNS/SQS permissions | EKS IAM (IRSA) |

### Provisioning Infrastructure

#### Step 1: Initialize and Apply (Dev)

```bash
cd terraform/environments/dev
terraform init
terraform plan
terraform apply
```

#### Step 2: Initialize and Apply (Prod)

```bash
cd terraform/environments/prod
terraform init
terraform plan
terraform apply
```

#### Step 3: Note the Outputs

After `terraform apply`, note these outputs — they are needed for deployment:

```bash
terraform output alb_url              # ALB DNS for ECS
terraform output ecr_repository_url   # ECR URL for Docker push
terraform output s3_bucket_name       # S3 bucket name
terraform output eks_cluster_name     # EKS cluster name
terraform output eks_cluster_endpoint # EKS API endpoint
terraform output irsa_role_arn        # IRSA role ARN for Helm
```

#### Step 4: Configure kubectl for EKS

```bash
aws eks update-kubeconfig \
  --name aws-s3-service-dev \
  --region us-east-1
```

#### Step 5: Install Istio on the EKS Cluster

```bash
istioctl install --set profile=demo -y
kubectl label namespace default istio-injection=enabled
```

---

## Deployment

### ECS Fargate (Jenkins)

The Jenkinsfile provides a full CI/CD pipeline for ECS Fargate deployments.

#### Jenkins Setup

1. **Install plugins**: AWS Credentials, Pipeline, Docker Pipeline
2. **Add credentials**: Create an `aws-credentials` entry in Jenkins (type: AWS Credentials) with an IAM user that has permissions for ECR, ECS, and Terraform state
3. **Create pipeline job**: Point it at the repository's `Jenkinsfile`

#### Pipeline Stages

| Stage | Description |
|-------|-------------|
| Checkout | Pulls source code |
| Lint | Runs `ruff check app/` |
| Test | Runs `pytest tests/ -v` |
| Build & Push | Builds Docker image, pushes to ECR with `BUILD_NUMBER` + `latest` tags |
| Terraform Init & Plan | Initializes Terraform, creates execution plan |
| Approval | Manual gate (**prod only**) |
| Terraform Apply | Applies the plan, deploying the new image to ECS |
| Smoke Test | Polls `GET /health` on the ALB for up to 5 minutes |

#### Running the Pipeline

1. Trigger the pipeline in Jenkins
2. Select the target environment (`dev` or `prod`)
3. For prod deployments, approve the manual gate when prompted
4. Monitor the smoke test stage for successful health check

#### First-Time Bootstrap (ECS)

On the first run, the ECR repository must exist before Docker can push images:

```bash
cd terraform/environments/dev
terraform apply -target=module.ecr
```

Then run the Jenkins pipeline normally.

---

### EKS Kubernetes (GitLab)

The `.gitlab-ci.yml` provides CI/CD for EKS deployments using Helm.

#### GitLab Setup

1. **Configure CI/CD variables** in GitLab (Settings → CI/CD → Variables):

   | Variable | Value | Masked |
   |----------|-------|--------|
   | `AWS_ACCESS_KEY_ID` | IAM access key | Yes |
   | `AWS_SECRET_ACCESS_KEY` | IAM secret key | Yes |
   | `AWS_REGION` | `us-east-1` | No |
   | `ECR_REGISTRY` | `<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com` | No |

2. **Branch strategy**:
   - Push to `develop` → auto-deploys to **dev**
   - Push to `main` → requires **manual approval** for prod deployment

#### Pipeline Stages

| Stage | Job(s) | Description |
|-------|--------|-------------|
| lint | `lint` | Runs `ruff check app/` |
| test | `test` | Runs `pytest tests/ -v` |
| build | `build-dev` / `build-prod` | Builds and pushes Docker image to ECR |
| deploy | `deploy-dev` / `deploy-prod` | `helm upgrade --install` to EKS + smoke test |

#### Manual Deployment with Helm

You can also deploy directly with Helm without the GitLab pipeline:

```bash
# Configure kubectl
aws eks update-kubeconfig --name aws-s3-service-dev --region us-east-1

# Deploy to dev
helm upgrade --install aws-s3-service helm/aws-s3-service/ \
  -f helm/aws-s3-service/values.yaml \
  -f helm/aws-s3-service/values-dev.yaml \
  --set image.tag=<YOUR_IMAGE_TAG> \
  --wait --timeout 5m

# Deploy to prod
helm upgrade --install aws-s3-service helm/aws-s3-service/ \
  -f helm/aws-s3-service/values.yaml \
  -f helm/aws-s3-service/values-prod.yaml \
  --set image.tag=<YOUR_IMAGE_TAG> \
  --wait --timeout 5m
```

#### Updating Helm Values

Before deploying, replace the placeholder `<AWS_ACCOUNT_ID>` in the Helm values files with your actual AWS account ID:

- `helm/aws-s3-service/values-dev.yaml`
- `helm/aws-s3-service/values-prod.yaml`

These files reference ECR repository URLs, IRSA role ARNs, and SQS/SNS resource names that include the account ID.

#### Verifying the Deployment

```bash
# Check pod status
kubectl get pods -l app.kubernetes.io/name=aws-s3-service

# Check service
kubectl get svc -l app.kubernetes.io/name=aws-s3-service

# View logs
kubectl logs -l app.kubernetes.io/name=aws-s3-service -f

# Test health endpoint via port-forward
kubectl port-forward svc/aws-s3-service-aws-s3-service 8000:80
curl http://localhost:8000/health
```

---

## Istio Service Mesh

Istio is configured as part of the Helm chart and enabled by default (`istio.enabled: true`).

### Resources Deployed

| Resource | Purpose |
|----------|---------|
| **Gateway** | Exposes the service via the Istio ingress gateway on port 80 |
| **VirtualService** | Routes traffic with 10s timeout and 3 retries on 5xx/reset/connect-failure |
| **DestinationRule** | Connection pool: 100 TCP connections, 100 pending HTTP/1 requests, 1000 HTTP/2 requests |

### Accessing via Istio Ingress

```bash
# Get the Istio ingress gateway external IP
kubectl get svc istio-ingressgateway -n istio-system

# Test the endpoint
curl -H "Host: dev.aws-s3-service.example.com" http://<INGRESS_EXTERNAL_IP>/health
```

### Customizing Istio

Override Istio settings per environment in the values files:

```yaml
istio:
  enabled: true
  gateway:
    hosts:
      - "your-domain.example.com"
  virtualService:
    timeout: 15s
    retries:
      attempts: 5
      perTryTimeout: 5s
      retryOn: "5xx,reset,connect-failure,retriable-4xx"
  destinationRule:
    connectionPool:
      tcp:
        maxConnections: 200
      http:
        http1MaxPendingRequests: 200
        http2MaxRequests: 2000
```

### Disabling Istio

Set `istio.enabled: false` in your values file or override at deploy time:

```bash
helm upgrade --install aws-s3-service helm/aws-s3-service/ \
  -f helm/aws-s3-service/values.yaml \
  --set istio.enabled=false
```

---

## Environment Configurations

### ECS Fargate

| Setting | Dev | Prod |
|---------|-----|------|
| CPU (units) | 256 | 512 |
| Memory (MiB) | 512 | 1024 |
| Desired tasks | 1 | 2 |
| Log retention | 14 days | 30 days |

### EKS

| Setting | Dev | Prod |
|---------|-----|------|
| Kubernetes version | 1.29 | 1.29 |
| Node instance type | t3.medium | t3.large |
| Node count (desired) | 2 | 3 |
| Node count (min/max) | 1 / 3 | 2 / 6 |

### Helm / Kubernetes

| Setting | Dev | Prod |
|---------|-----|------|
| Replicas | 1 | 2 |
| CPU request / limit | 128m / 256m | 256m / 1000m |
| Memory request / limit | 256Mi / 512Mi | 512Mi / 1024Mi |
| HPA min / max | 1 / 3 | 2 / 10 |

---

## Troubleshooting

### ECS Tasks Fail to Start

```bash
# Check ECS service events
aws ecs describe-services \
  --cluster aws-s3-service-dev \
  --services aws-s3-service-dev \
  --query 'services[0].events[:5]'

# Check CloudWatch logs
aws logs tail /ecs/aws-s3-service-dev --follow
```

Common causes:
- Missing environment variables (`S3_BUCKET_NAME`, `SNS_TOPIC_ARN`, `SQS_QUEUE_URL`, `DATABASE_URL`)
- IAM permissions insufficient for S3/SNS/SQS access
- ECR image not found (check the image tag)
- PostgreSQL unreachable — verify `DATABASE_URL` and security group rules

### EKS Pods CrashLoopBackOff

```bash
kubectl describe pod -l app.kubernetes.io/name=aws-s3-service
kubectl logs -l app.kubernetes.io/name=aws-s3-service --previous
```

Common causes:
- IRSA role not correctly annotated on the ServiceAccount
- Helm values missing required `env.*` values (including `DATABASE_URL`)
- Istio sidecar injection issues (check `istio-injection` label on namespace)
- PostgreSQL connection refused — check host, port, credentials, and network policy

### Database Connection Issues

```bash
# Test connectivity from inside a pod
kubectl exec -it <pod-name> -- python -c \
  "import asyncio, asyncpg; asyncio.run(asyncpg.connect('$DATABASE_URL'))"
```

Common causes:
- Incorrect `DATABASE_URL` format (must be `postgresql://user:pass@host:5432/db`)
- PostgreSQL not accepting connections from the app's IP/subnet
- Wrong database name or user credentials

### Terraform State Lock

If Terraform hangs due to a stale state lock:

```bash
terraform force-unlock <LOCK_ID>
```

### Health Check Failures

The `/health` endpoint returns `{"message": "ok"}` with HTTP 200. If ALB or Kubernetes probes fail:

- Verify the container is listening on port 8000
- Check security group rules allow traffic from the ALB (ECS) or within the cluster (EKS)
- For Istio, ensure the sidecar is injected and the `VirtualService` routes correctly

### Connecting to LocalStack Resources

```bash
# List S3 buckets
aws --endpoint-url=http://localhost:4566 s3 ls

# List SNS topics
aws --endpoint-url=http://localhost:4566 sns list-topics

# List SQS queues
aws --endpoint-url=http://localhost:4566 sqs list-queues
```
