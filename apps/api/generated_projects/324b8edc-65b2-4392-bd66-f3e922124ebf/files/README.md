# Mira News Infrastructure

This repository contains the infrastructure setup, CI/CD pipelines, and deployment strategies for Mira News, an AI-powered, space-themed news platform.

## Overview
- **CI/CD Pipeline**: Automated testing, building, and deployment using GitHub Actions.
- **Infrastructure as Code**: AWS EKS cluster provisioned with Terraform.
- **Containerization**: Docker for local development and production images.
- **Orchestration**: Kubernetes for managing containerized workloads with auto-scaling and health checks.
- **Deployment Strategy**: Blue-green deployment for zero-downtime updates.

## Setup
1. **Local Development**:
   - Install Docker and Docker Compose.
   - Run `docker-compose up` to start backend, frontend, and database services.
2. **CI/CD**:
   - Configure secrets in GitHub (DOCKER_USERNAME, DOCKER_PASSWORD, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY).
   - Push to `main` or `develop` branches to trigger the pipeline.
3. **Infrastructure**:
   - Install Terraform.
   - Run `terraform init` and `terraform apply` in the `terraform` directory to provision the EKS cluster.

## Deployment
- Deployments are automated via GitHub Actions to AWS EKS.
- Kubernetes manifests are in the `k8s` directory for backend and frontend services.

## Monitoring
- TODO: Add Prometheus and Grafana setup for monitoring.

## Security
- Secrets are managed via Kubernetes Secrets and AWS Secrets Manager (for production).
- TODO: Implement container scanning in CI pipeline.
