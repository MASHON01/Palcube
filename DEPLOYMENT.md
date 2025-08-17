# Deployment Guide

This guide covers deploying the Slack-Jira-GitHub automation system in various environments.

## 🏗️ Architecture Overview

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Slack     │    │   Jira      │    │   GitHub    │
│  (Events)   │    │ (Tickets)   │    │(Repos)      │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
              ┌─────────────────────┐
              │  Automation App     │
              │  (Docker Container) │
              └─────────────────────┘
```

## 🚀 Quick Start

### 1. Prerequisites Check

```bash
# Check Docker
docker --version
docker-compose --version

# Check Python (for local development)
python --version  # Should be 3.11+

# Check Git
git --version
```

### 2. Environment Setup

```bash
# Clone repository
git clone <your-repo-url>
cd slack-jira-github-automation

# Copy environment template
cp env.example .env

# Edit environment variables
nano .env  # or use your preferred editor
```

### 3. Docker Deployment

```bash
# Build and start
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## 🔧 Environment Configuration

### Production Environment Variables

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-production-bot-token
SLACK_APP_TOKEN=xapp-your-production-app-token

# Jira Configuration
JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=automation@yourcompany.com
JIRA_API_TOKEN=your-production-jira-token

# GitHub Configuration
GITHUB_TOKEN=ghp_your-production-github-token
GITHUB_USERNAME=your-github-username

# Application Configuration
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### Staging Environment Variables

```bash
# Use staging-specific tokens and URLs
SLACK_BOT_TOKEN=xoxb-your-staging-bot-token
JIRA_URL=https://your-staging.atlassian.net
GITHUB_TOKEN=ghp_your-staging-github-token
ENVIRONMENT=staging
```

## 🐳 Docker Deployment

### Development

```bash
# Start with development config
docker-compose up -d

# Rebuild after changes
docker-compose up -d --build

# Stop services
docker-compose down
```

### Production

```bash
# Create production compose file
cp docker-compose.yml docker-compose.prod.yml

# Edit production config (add resource limits, etc.)
nano docker-compose.prod.yml

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d

# Monitor production
docker-compose -f docker-compose.prod.yml logs -f
```

### Production Docker Compose Example

```yaml
version: '3.8'

services:
  slack-jira-github-automation:
    build: .
    container_name: slack-jira-github-automation-prod
    restart: unless-stopped
    environment:
      - SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}
      - SLACK_APP_TOKEN=${SLACK_APP_TOKEN}
      - JIRA_URL=${JIRA_URL}
      - JIRA_USERNAME=${JIRA_USERNAME}
      - JIRA_API_TOKEN=${JIRA_API_TOKEN}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - GITHUB_USERNAME=${GITHUB_USERNAME}
      - ENVIRONMENT=production
    volumes:
      - ./logs:/app/logs
      - ./backups:/app/backups
    networks:
      - automation-network
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  automation-network:
    driver: bridge

volumes:
  logs:
  backups:
```

## ☁️ Cloud Deployment

### AWS ECS

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name automation-cluster

# Create task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service --cluster automation-cluster --service-name automation-service --task-definition automation-task
```

### Google Cloud Run

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/slack-jira-github-automation

# Deploy to Cloud Run
gcloud run deploy slack-jira-github-automation \
  --image gcr.io/PROJECT_ID/slack-jira-github-automation \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Azure Container Instances

```bash
# Deploy to Azure Container Instances
az container create \
  --resource-group myResourceGroup \
  --name automation-container \
  --image your-registry.azurecr.io/slack-jira-github-automation:latest \
  --dns-name-label automation-app \
  --ports 8080
```

## 🔒 Security Best Practices

### 1. Secrets Management

```bash
# Use Docker secrets (for Swarm)
echo "your-secret-token" | docker secret create slack_bot_token -

# Use Kubernetes secrets
kubectl create secret generic automation-secrets \
  --from-literal=slack-bot-token=xoxb-your-token \
  --from-literal=jira-api-token=your-jira-token
```

### 2. Network Security

```bash
# Create isolated network
docker network create --driver bridge automation-network

# Use internal networks for inter-service communication
docker-compose up -d --network automation-network
```

### 3. Access Control

```bash
# Run container as non-root user (already in Dockerfile)
# Use read-only filesystem where possible
docker run --read-only --tmpfs /tmp your-image
```

## 📊 Monitoring and Logging

### Health Checks

```bash
# Check application health
curl http://localhost:8080/health

# Monitor with Docker
docker-compose ps
docker-compose logs --tail=100 -f
```

### Log Management

```bash
# Configure log rotation
docker run --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  your-image

# Send logs to external service
docker run --log-driver fluentd \
  --log-opt fluentd-address=localhost:24224 \
  your-image
```

### Metrics Collection

```bash
# Use Prometheus for metrics
docker run -p 9090:9090 prom/prometheus

# Use Grafana for visualization
docker run -p 3000:3000 grafana/grafana
```

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
name: Deploy Automation

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker image
        run: docker build -t automation-app .
      
      - name: Deploy to production
        run: |
          docker-compose -f docker-compose.prod.yml up -d
```

## 🚨 Troubleshooting

### Common Issues

1. **Container won't start**
   ```bash
   # Check logs
   docker-compose logs
   
   # Check environment variables
   docker-compose config
   ```

2. **Slack connection issues**
   ```bash
   # Verify tokens
   curl -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
     https://slack.com/api/auth.test
   ```

3. **Jira API errors**
   ```bash
   # Test Jira connection
   curl -u "$JIRA_USERNAME:$JIRA_API_TOKEN" \
     "$JIRA_URL/rest/api/2/myself"
   ```

### Debug Mode

```bash
# Run with debug logging
ENVIRONMENT=development LOG_LEVEL=DEBUG docker-compose up

# Access container shell
docker-compose exec slack-jira-github-automation /bin/bash
```

## 📈 Scaling

### Horizontal Scaling

```bash
# Scale to multiple instances
docker-compose up -d --scale slack-jira-github-automation=3

# Use load balancer
docker run -d --name nginx \
  -p 80:80 \
  nginx:alpine
```

### Resource Optimization

```bash
# Monitor resource usage
docker stats

# Set resource limits
docker run --memory=512m --cpus=0.5 your-image
```

## 🔄 Backup and Recovery

### Data Backup

```bash
# Backup logs
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/

# Backup configuration
cp .env .env.backup-$(date +%Y%m%d)
```

### Disaster Recovery

```bash
# Restore from backup
tar -xzf logs-backup-20240101.tar.gz
cp .env.backup-20240101 .env

# Restart services
docker-compose down
docker-compose up -d
```

## 📞 Support

For deployment issues:
1. Check the logs: `docker-compose logs -f`
2. Verify environment variables: `docker-compose config`
3. Test connectivity to external services
4. Review the troubleshooting section above
5. Create an issue in the repository with logs and error details
