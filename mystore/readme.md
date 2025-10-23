# Django DevOps Deployment Guide (Offline)

This guide will walk you through deploying your Django project `mystore` on **AWS EC2** with **Docker, Jenkins, Nginx, Gunicorn, and DockerHub**, including persistent static/media files and HTTPS using Certbot. All steps are designed to avoid paid AWS services except EC2.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [AWS EC2 Setup](#aws-ec2-setup)
3. [Local Jenkins Setup](#local-jenkins-setup)
4. [Dockerizing Django Project](#dockerizing-django-project)
5. [Jenkins Pipeline Configuration](#jenkins-pipeline-configuration)
6. [EC2 Deployment](#ec2-deployment)
7. [Persistent Static & Media Files](#persistent-static--media-files)
8. [Nginx Setup](#nginx-setup)
9. [HTTPS with Certbot](#https-with-certbot)
10. [Testing & Verification](#testing--verification)

---

## Prerequisites

- AWS EC2 Ubuntu instance (t2.micro is fine)
- Elastic IP attached
- Local machine with Jenkins installed
- DockerHub account with a free private repository
- GitHub account with your Django project repo
- Python 3.10+, Docker, Nginx installed on EC2

---

## AWS EC2 Setup

1. Launch Ubuntu EC2 instance.
2. Attach Elastic IP.
3. SSH into instance:
```bash
ssh -i mystore.pem ubuntu@13.204.111.62
```
4. Install Docker & Nginx:
```bash
sudo apt update
sudo apt install -y docker.io nginx
sudo systemctl enable docker
sudo systemctl enable nginx
```

---

## Local Jenkins Setup

1. Install Jenkins locally.
2. Open Jenkins URL: `http://localhost:8080`.
3. Install plugins:
   - Docker Pipeline
   - SSH Agent Plugin
   - GitHub Integration Plugin
   - Pipeline Plugin
4. Add credentials:
   - DockerHub (username + token)
   - EC2 SSH key (`mystore.pem`)
   - GitHub token (if repo is private)

---

## Dockerizing Django Project

### Dockerfile
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["gunicorn", "mystore.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Django Settings (`settings.py`)
```python
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'mediafiles'
```

---

## Jenkins Pipeline Configuration

### Jenkinsfile
```groovy
pipeline {
    agent any
    environment {
        DOCKERHUB_REPO = "renjithmr/mystore"
        EC2_HOST = "ubuntu@13.204.111.62"
        IMAGE_TAG = "latest"
    }
    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'main', credentialsId: 'github_creds', url: 'https://github.com/renjumr87/mystore.git'
            }
        }
        stage('Build Docker Image') {
            steps {
                sh 'docker build -t $DOCKERHUB_REPO:$IMAGE_TAG .'
            }
        }
        stage('Push to DockerHub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub_creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                    echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                    docker push $DOCKERHUB_REPO:$IMAGE_TAG
                    docker logout
                    '''
                }
            }
        }
        stage('Deploy to EC2') {
            steps {
                sshagent(credentials: ['ec2_ssh']) {
                    sh '''
                    ssh -o StrictHostKeyChecking=no $EC2_HOST << EOF
                    docker pull $DOCKERHUB_REPO:$IMAGE_TAG
                    mkdir -p ~/mystore_data/static
                    mkdir -p ~/mystore_data/media
                    docker stop mystore || true
                    docker rm mystore || true
                    docker run -d --name mystore -p 8000:8000 \
                        -v ~/mystore_data/static:/app/staticfiles \
                        -v ~/mystore_data/media:/app/mediafiles \
                        -e DJANGO_SETTINGS_MODULE=mystore.settings \
                        $DOCKERHUB_REPO:$IMAGE_TAG
                    sudo systemctl restart nginx || true
                    EOF
                    '''
                }
            }
        }
    }
    post {
        success {
            echo '✅ Deployment completed successfully!'
        }
        failure {
            echo '❌ Deployment failed.'
        }
    }
}
```

---

## EC2 Deployment

1. Ensure Docker & Nginx installed.
2. Give Jenkins machine SSH access:
```bash
# On EC2
mkdir -p ~/.ssh
nano ~/.ssh/authorized_keys # add Jenkins public key
chmod 600 ~/.ssh/authorized_keys
```
3. Test connection from local Jenkins machine:
```bash
ssh -i jenkins_ec2 ubuntu@13.204.111.62
```
4. Deploy via Jenkins build → container runs on port 8000.

---

## Persistent Static & Media Files

- Map `/home/ubuntu/mystore_data/static` → `/app/staticfiles`
- Map `/home/ubuntu/mystore_data/media` → `/app/mediafiles`
- Update Nginx config:
```nginx
location /static/ { alias /home/ubuntu/mystore_data/static/; }
location /media/ { alias /home/ubuntu/mystore_data/media/; }
```

---

## Nginx Setup

1. Edit `/etc/nginx/sites-available/mystore`:

```nginx
server {
    listen 80;
    server_name mystore.in www.mystore.in;

    location /static/ {
        alias /home/ubuntu/mystore_data/static/;
    }

    location /media/ {
        alias /home/ubuntu/mystore_data/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

2. Enable & reload Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/mystore /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## HTTPS with Certbot

1. Install Certbot:
```bash
sudo apt install -y certbot python3-certbot-nginx
```

2. Run Certbot:
```bash
sudo certbot --nginx -d mystore.in -d www.mystore.in
```

3. Verify HTTPS at `https://mystore.in`

4. Auto-renew:
```bash
sudo certbot renew --dry-run
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## Testing & Verification

1. Push new code → Jenkins automatically builds → DockerHub push → EC2 deployment
2. Visit your domain/IP → should load Django app via HTTPS
3. Upload media/static → stop container → redeploy → files persist
4. Gunicorn + Nginx serve the app in production

---

## Notes

- Keep EC2 running continuously for Elastic IP persistence
- All static/media files persist via Docker volumes
- Jenkins triggers builds manually or via GitHub Actions → SSH trigger
- Ready to extend to Load Balancer or multiple EC2 instances later

---

*End of `django-devops.md` offline guide*

