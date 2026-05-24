# Deployment Guide

This guide covers deploying the AI-Powered Geospatial Anomaly Detection system to production using Docker and Docker Compose.

## Prerequisites

- Docker (>= 20.10)
- Docker Compose (>= 2.0)
- At least 8GB RAM
- 20GB disk space
- GPU (optional, for faster ML inference)

## Quick Start (Docker Compose)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd windsurf-project
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your configuration
nano .env
```

**Important:** Change the following values in `.env`:
- `SECRET_KEY` - Generate a secure random key
- `POSTGRES_PASSWORD` - Set a strong database password
- `GEE_PROJECT_ID` - Your Google Earth Engine project ID (if using GEE)

### 3. Build and Start Services

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f
```

### 4. Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Flower (Celery Monitor):** http://localhost:5555

## Deployment Options

### Option 1: Local/On-Premises Deployment

#### Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

#### Without Docker

**Backend:**
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/anomaly_detection"
export REDIS_URL="redis://localhost:6379/0"

# Start backend
cd backend
uvicorn api_advanced:app --host 0.0.0.0 --port 8000 --workers 4
```

**Frontend:**
```bash
# Serve with any HTTP server
cd frontend
python -m http.server 3000
# Or use nginx
```

### Option 2: Cloud Deployment

#### AWS Deployment

**Using ECS (Elastic Container Service):**

1. Push Docker images to ECR:
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag anomaly-detection-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/anomaly-detection-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/anomaly-detection-backend:latest
```

2. Create ECS task definition using the provided Docker image
3. Configure load balancer (ALB) for frontend and backend
4. Set up RDS for PostgreSQL and ElastiCache for Redis

**Using EC2:**

```bash
# Launch EC2 instance with Docker installed
# SSH into instance
git clone <repository-url>
cd windsurf-project
docker-compose up -d
```

#### Google Cloud Platform (GCP)

**Using Cloud Run:**

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/<project-id>/anomaly-detection-backend

# Deploy to Cloud Run
gcloud run deploy anomaly-detection-backend \
  --image gcr.io/<project-id>/anomaly-detection-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**Using GKE (Google Kubernetes Engine):**

```bash
# Create cluster
gcloud container clusters create anomaly-detection --num-nodes=3

# Deploy using kubectl
kubectl apply -f k8s/
```

#### Azure Deployment

**Using Azure Container Instances (ACI):**

```bash
# Create resource group
az group create --name anomaly-detection --location eastus

# Deploy container
az container create \
  --resource-group anomaly-detection \
  --name anomaly-detection-backend \
  --image <registry>/anomaly-detection-backend:latest \
  --ports 8000
```

**Using Azure Kubernetes Service (AKS):**

```bash
# Create cluster
az aks create --resource-group anomaly-detection --name anomaly-detection-cluster --node-count 3

# Deploy using kubectl
kubectl apply -f k8s/
```

### Option 3: Kubernetes Deployment

Create Kubernetes manifests in `k8s/` directory:

**k8s/deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: anomaly-detection-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: anomaly-detection-backend
  template:
    metadata:
      labels:
        app: anomaly-detection-backend
    spec:
      containers:
      - name: backend
        image: anomaly-detection-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
```

**Deploy:**
```bash
kubectl apply -f k8s/
kubectl get pods
```

## Production Configuration

### Security

1. **Change Default Passwords:**
   - Update `POSTGRES_PASSWORD` in `.env`
   - Generate strong `SECRET_KEY`

2. **Enable HTTPS:**
   - Use reverse proxy (nginx) with SSL certificates
   - Let's Encrypt for free SSL:
   ```bash
   certbot --nginx -d your-domain.com
   ```

3. **Firewall Rules:**
   - Only expose ports 80 (HTTP) and 443 (HTTPS)
   - Restrict database access to internal network

4. **Environment Variables:**
   - Never commit `.env` file
   - Use secrets management (AWS Secrets Manager, Azure Key Vault)

### Performance Optimization

1. **Database:**
   - Enable connection pooling
   - Add indexes for frequently queried fields
   - Configure read replicas for scaling

2. **Caching:**
   - Redis for API response caching
   - CDN for static assets (frontend)

3. **Backend:**
   - Increase worker count based on CPU cores
   - Enable GPU acceleration if available
   - Use load balancer for multiple instances

4. **Frontend:**
   - Enable gzip compression
   - Minify CSS/JS
   - Use CDN for static assets

### Monitoring

1. **Application Monitoring:**
   - Prometheus + Grafana for metrics
   - ELK Stack (Elasticsearch, Logstash, Kibana) for logs
   - Sentry for error tracking

2. **Health Checks:**
   - `/health` endpoint for backend
   - Database connection checks
   - Redis connection checks

3. **Alerts:**
   - Set up alerts for high error rates
   - Monitor disk space and memory usage
   - Alert on failed deployments

## Scaling

### Horizontal Scaling

```bash
# Scale backend to 4 instances
docker-compose up -d --scale backend=4

# Or in Kubernetes
kubectl scale deployment anomaly-detection-backend --replicas=4
```

### Vertical Scaling

- Increase CPU/RAM limits in Docker Compose or Kubernetes
- Use GPU instances for ML inference

### Database Scaling

- Read replicas for read-heavy workloads
- Database sharding for large datasets
- Connection pooling (PgBouncer)

## Backup and Recovery

### Database Backup

```bash
# Backup PostgreSQL
docker exec anomaly-detection-postgres pg_dump -U postgres anomaly_detection > backup.sql

# Restore
docker exec -i anomaly-detection-postgres psql -U postgres anomaly_detection < backup.sql
```

### Automated Backups

```bash
# Add to crontab
0 2 * * * docker exec anomaly-detection-postgres pg_dump -U postgres anomaly_detection > /backups/backup_$(date +\%Y\%m\%d).sql
```

### Volume Backups

```bash
# Backup Docker volumes
docker run --rm -v anomaly-detection_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

## Troubleshooting

### Common Issues

1. **Backend fails to start:**
   ```bash
   # Check logs
   docker-compose logs backend
   
   # Check if port is in use
   netstat -tulpn | grep 8000
   ```

2. **Database connection failed:**
   ```bash
   # Check if PostgreSQL is running
   docker-compose ps postgres
   
   # Test connection
   docker exec -it anomaly-detection-postgres psql -U postgres -d anomaly_detection
   ```

3. **Out of memory:**
   - Increase memory limits in docker-compose.yml
   - Reduce batch size in ML models
   - Use gradient checkpointing for large models

4. **Slow detection:**
   - Enable GPU acceleration
   - Reduce image resolution
   - Use simpler models (skip ViT)

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# View last 100 lines
docker-compose logs --tail=100 backend
```

## Maintenance

### Updates

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build

# Clean up old images
docker image prune -a
```

### Health Checks

```bash
# Check service health
curl http://localhost:8000/health
curl http://localhost:3000
```

### Performance Tuning

- Monitor resource usage with `docker stats`
- Adjust worker counts based on load
- Optimize database queries
- Cache frequently accessed data

## Cost Optimization

1. **Use spot instances** for non-critical workloads
2. **Auto-scale** based on traffic patterns
3. **Compress** stored data
4. **Clean up** unused resources regularly
5. **Use reserved instances** for steady workloads

## Support

For issues or questions:
- Check logs: `docker-compose logs`
- Review documentation: `README.md`
- Open an issue on GitHub
