pipeline {
    agent { label "dev" }
    environment {
        DOCKERHUB_REPO = "renjithmr/mystore"
        EC2_HOST = "ubuntu@13.204.111.62"
        IMAGE_TAG = "latest"
    }
    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'master', credentialsId: 'github_creds', url: 'https://github.com/renjumr87/mystore.git'
            }
        }
        stage('Deploy') {
            steps {
                sh "docker-compose -f docker-compose.prod.yml up -d --build"
            }
        }
        stage('Push to DockerHub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub_creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                    docker login -u $DOCKER_USER -p $DOCKER_PASS
                    docker push $DOCKERHUB_REPO:$IMAGE_TAG
                    docker logout
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
