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
