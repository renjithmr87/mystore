pipeline {
    agent { label "dev" }

    environment {
        DOCKERHUB_REPO = "renjithmr/mystore"
        DOCKER_USER = "renjithmr"
        DOCKER_IMAGE = "mystore"
        APP_EC2_USER = "ubuntu"
        APP_EC2_HOST = "13.204.111.62"
        APP_EC2_PATH = "/home/ubuntu/projects/mystore" // Correct path on app EC2
    }

    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'master', credentialsId: 'github_creds', url: 'https://github.com/renjumr87/mystore.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh "docker compose -f docker-compose.prod.yml build"
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
                sshagent(['mystore_ec2_key']) { // Jenkins credential for SSH private key
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
        success {
            echo '✅ Deployment completed successfully!'
        }
        failure {
            echo '❌ Deployment failed.'
        }
    }
}
