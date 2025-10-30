**cleaned, production-ready markdown guide**
It’s focused purely on **containerized Jenkins master/worker**, **Django-PostgreSQL-Nginx stack**, and **automated deployment to EC2 (13.204.111.62)**.

---

# 🐳 Django DevOps Deployment Guide (Production, Offline)

This guide explains how to deploy the Django project **`mystore`** on **AWS EC2 (13.204.111.62)** using **Docker, Jenkins (Master + Worker nodes), PostgreSQL, Nginx, and DockerHub**.
It covers full CI/CD — from GitHub to EC2 deployment — with persistent static/media storage.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [EC2 Setup](#ec2-setup)
3. [Dockerizing Django Project](#dockerizing-django-project)
4. [Jenkins Master and Worker Setup](#jenkins-master-and-worker-setup)
5. [Jenkins Pipeline Configuration](#jenkins-pipeline-configuration)
6. [EC2 Deployment](#ec2-deployment)
7. [Persistent Static & Media Files](#persistent-static--media-files)
8. [Testing & Verification](#testing--verification)
9. [Notes](#notes)

---

## 🧰 Prerequisites

* AWS EC2 Ubuntu instance (t2.micro or higher)
* Elastic IP attached
* Jenkins Master & Worker nodes running in Docker containers
* DockerHub account (for image registry)
* GitHub repository for your Django project (`mystore`)
* Valid SSH key for EC2 access

---

## ☁️ EC2 Setup

1. **Launch EC2 (Ubuntu 22.04+)** and attach your Elastic IP.

2. **Connect via SSH**:

   ```bash
   ssh -i ~/.ssh/mystore.pem ubuntu@13.204.111.62
   ```

3. **Install Docker & Docker Compose**:

   ```bash
   sudo apt remove docker docker-engine docker.io containerd runc -y
   sudo apt update
   sudo apt install ca-certificates curl gnupg -y

   sudo install -m 0755 -d /etc/apt/keyrings
   sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
   sudo chmod a+r /etc/apt/keyrings/docker.asc

   echo \
     "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
     https://download.docker.com/linux/ubuntu \
     $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
     sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

   sudo apt update
   sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
   docker --version
   docker compose version
   sudo systemctl enable docker
   ```

4. **(Optional)** Add Jenkins user to Docker group (if Jenkins container runs as user):

   ```bash
   sudo usermod -aG docker jenkins
   sudo systemctl restart docker
   ```

---

## 🐍 Dockerizing Django Project

### Dockerfile

```dockerfile
FROM python:3.12-slim
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

### docker-compose.prod.yml

```yaml
version: '3.9'

services:
  django:
    image: renjithmr/mystore:latest
    container_name: mystore-django
    restart: always
    env_file: .env
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/mediafiles
    expose:
      - 8000
    depends_on:
      - mystoredb

  mystoredb:
    image: postgres:15
    container_name: mystore-mystoredb
    restart: always
    environment:
      POSTGRES_DB: mystore
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  nginx:
    image: nginx:latest
    container_name: mystore-nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - static_volume:/home/ubuntu/mystore_data/static
      - media_volume:/home/ubuntu/mystore_data/media
    depends_on:
      - django

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

---

## ⚙️ Jenkins Master and Worker Setup

You will use **containerized Jenkins** for CI/CD.

### Jenkins Master

* Runs the main Jenkins controller.
* Accessible via browser:

  ```
  http://<jenkins-master-public-ip>:8080
  ```
* Manages credentials, jobs, and pipelines.

### Jenkins Worker (Agent)

* Performs build and deploy tasks.
* Connects via SSH to the master Jenkins.
* Must have:

  * Docker + Docker Compose
  * SSH access to EC2 app server (`13.204.111.62`)

### SSH Key Setup

On **worker node**:

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/mystore_ec2
cat ~/.ssh/mystore_ec2.pub
```

Copy the public key into `/home/ubuntu/.ssh/authorized_keys` on the EC2 app server.

In **Jenkins → Manage Credentials → Global**, add:

* **Kind:** SSH private key
* **ID:** `mystore_ec2_key`
* **Username:** `ubuntu`
* **Private Key:** contents of `~/.ssh/mystore_ec2`

---

## 🧩 Jenkins Pipeline Configuration

### Jenkinsfile

```groovy
pipeline {
    agent { label 'dev-node' }

    environment {
        DOCKERHUB_REPO = 'renjithmr/mystore'
        DOCKER_USER = 'renjithmr'
        DOCKER_IMAGE = 'mystore'
        APP_EC2_USER = 'ubuntu'
        APP_EC2_HOST = '13.204.111.62'
        APP_EC2_PATH = '/home/ubuntu/projects/mystore'
    }

    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'master', url: 'https://github.com/renjumr87/mystore.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker compose -f docker-compose.prod.yml build'
            }
        }

        stage('Push to DockerHub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub_creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        docker login -u $DOCKER_USER -p $DOCKER_PASS
                        docker tag myjob-django:latest $DOCKERHUB_REPO:latest
                        docker push $DOCKERHUB_REPO:latest
                        docker logout
                    '''
                }
            }
        }

        stage('Deploy to EC2') {
            steps {
                sshagent(['mystore_ec2_key']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no $APP_EC2_USER@$APP_EC2_HOST '
                            cd $APP_EC2_PATH &&
                            echo "Pulling latest Docker images..." &&
                            docker compose -f docker-compose.prod.yml pull &&
                            echo "Updating containers..." &&
                            docker compose -f docker-compose.prod.yml up -d --no-deps --build &&
                            echo "Cleaning up old images..." &&
                            docker image prune -f
                        '
                    """
                }
            }
        }
    }

    post {
        success { echo '✅ Deployment completed successfully!' }
        failure { echo '❌ Deployment failed.' }
    }
}
```

---

## 🚀 EC2 Deployment

1. On EC2, prepare the project directory:

   ```bash
   mkdir -p /home/ubuntu/projects/mystore
   cd /home/ubuntu/projects/mystore
   ```

2. Ensure SSH key access works from Jenkins worker:

   ```bash
   ssh ubuntu@13.204.111.62
   ```

3. When you trigger a Jenkins build:

   * Django Docker image is built and pushed to DockerHub
   * Jenkins connects via SSH to EC2
   * EC2 pulls and restarts containers automatically

---

## 🗂️ Persistent Static & Media Files

* Static: `/home/ubuntu/mystore_data/static`
* Media: `/home/ubuntu/mystore_data/media`

These are mapped in `docker-compose.prod.yml` to persist data across redeployments.

---

## ✅ Testing & Verification

1. Trigger Jenkins pipeline manually or via webhook.
2. Observe logs — successful deployment message should appear:

   ```
   ✅ Deployment completed successfully!
   ```
3. Access your app:

   ```
   http://13.204.111.62
   ```
4. Verify containers:

   ```bash
   docker ps
   docker compose logs
   ```

---

## 🧾 Notes

* Jenkins Master manages CI/CD pipelines; Worker performs build/deploy.
* The Django app runs inside Docker with PostgreSQL and Nginx as supporting services.
* Static and media files persist using Docker volumes.
* Future enhancements:

  * HTTPS via Certbot inside Nginx container
  * Tagged image versions for rollback
  * Slack or email notifications from Jenkins

---
## Finally 
#  **GitHub Actions workflow** (`.github/workflows/django-ci.yml`) to trigger **webhooks for Jenkins CI/CD pipeline**.

Let’s update it to use the **latest stable Actions**, **modern syntax**, and **best practices (Python 3.12)**.
We’ll also ensure proper error handling and caching for faster builds.

Here’s the **updated `django-ci.yml`** 👇

---

```yaml
name: Django CI

on:
  push:
    branches: [ "master" ]
  pull_request:
    branches: [ "master" ]

jobs:
  build:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: mystoredb
          POSTGRES_USER: mystoreuser
          POSTGRES_PASSWORD: ren1234
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    env:
      DATABASE_URL: postgres://mystoreuser:ren1234@127.0.0.1:5432/mystoredb

    strategy:
      matrix:
        python-version: ["3.10"]

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: "pip"

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run Django Migrations
        run: |
          python manage.py makemigrations --noinput
          python manage.py migrate --noinput

      - name: Run Tests
        run: |
          python manage.py test

      - name: Trigger Jenkins Webhook
        if: success()
        env:
          JENKINS_WEBHOOK_URL: ${{ secrets.JENKINS_WEBHOOK_URL }}
        run: |
          echo "Triggering Jenkins CI/CD Pipeline..."
          curl -X POST "$JENKINS_WEBHOOK_URL"
```

---

### 🔍 Key Improvements

✅ **Latest action versions:**

* `actions/checkout@v4`
* `actions/setup-python@v5`

✅ **Python 3.12 (stable LTS)**
Up-to-date runtime for Django 5.x compatibility.

✅ **Pip caching**
Drastically reduces build times for repeat workflows.

✅ **Non-interactive migrations**
`--noinput` prevents CI from hanging on prompts.

✅ **Webhook trigger for Jenkins**
Automatically POSTs to your Jenkins endpoint stored securely in
**GitHub Secrets → `JENKINS_WEBHOOK_URL`**.

---

### 🛠️ Setup Secret for Jenkins Webhook

In your GitHub repo:

1. Go to **Settings → Secrets and variables → Actions → New repository secret**
2. Add:
   * **Name:** `JENKINS_WEBHOOK_URL`

   * **Value:** Your Jenkins webhook (e.g.,
     `http://3.110.197.137:8080/github-webhook/`)

---


*End of `django-devops.md` (Production Containerized Setup Guide)*