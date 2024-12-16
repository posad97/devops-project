pipeline {
    agent any
    environment {
        DOCKER_IMAGE = 'posad97/trading-app:latest'
        APP_CONTAINER_NAME = 'trading-app'
        DOCKER_CREDENTIALS_ID = 'dockerhub-credentials'
        DB_CREDENTIALS_ID = 'db-credentials'
        DOCKER_NETWORK = 'backend'
        APP_PORT = '5000'
    }
    stages {
        stage('Build Docker Image') {
            steps {
                // Build the Docker image
                sh 'docker build -t ${DOCKER_IMAGE} .'
            }
        }
        stage('Push to Docker Hub') {
            steps {
                script {
                    // Login to Docker Hub using credentials from Jenkins
                    withCredentials([usernamePassword(credentialsId: DOCKER_CREDENTIALS_ID, passwordVariable: 'DOCKER_PASSWORD', usernameVariable: 'DOCKER_USERNAME')]) {
                        sh 'docker login -u ${DOCKER_USERNAME} -p ${DOCKER_PASSWORD}'
                    }
                }

                sh 'docker push ${DOCKER_IMAGE}'
            }
        }
        stage('Run Container from Docker Hub') {
            steps {
                script {
                    // Stop and remove any existing container with the same name
                    sh 'docker rm -f ${APP_CONTAINER_NAME} || true'
                    
                    // Pull the image from Docker Hub and run the new container
                    withCredentials([usernamePassword(credentialsId: DB_CREDENTIALS_ID, passwordVariable: 'DB_PASSWORD', usernameVariable: 'DB_USER'),
                    string(credentialsId: 'api-key', variable: 'API_KEY'),
                    string(credentialsId: 'db-name', variable: 'DB_NAME'),
                    string(credentialsId: 'db-hostname', variable: 'DB_HOSTNAME')]) {

                        sh """
                        docker run -d \
                        --name ${APP_CONTAINER_NAME} \
                        --network ${DOCKER_NETWORK} \
                        -p ${APP_PORT}:${APP_PORT} \
                        -e DB_HOSTNAME=${DB_HOSTNAME} \
                        -e DB_USER=${DB_USER} \
                        -e DB_PASSWORD=${DB_PASSWORD} \
                        -e DB_NAME=${DB_NAME} \
                        -e API_KEY=${API_KEY} \
                        ${DOCKER_IMAGE}
                    """

                    }
                    
                }
            }
        }

        stage('Clean up old images') {
            steps {
                script {
                    sh '''
                    chmod +x remove_old_images.sh
                    ./remove_old_images.sh
                    '''
                }
            }
        }
    }
}