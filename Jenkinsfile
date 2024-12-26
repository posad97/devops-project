pipeline {
    agent any
    environment {
      IMAGE_NAME = 'posad97/trading-app'
      DOCKER_CREDENTIALS_ID = 'dockerhub-credentials'
      DB_CREDENTIALS_ID = 'db-credentials'
      CLUSTER_NAME = 'zonal-cluster'
      ZONE = 'us-central1-c'
    }

    stages {
        stage('Set App Version') {
            steps {
                script {
                    env.APP_VERSION = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    def imageTag = "${env.APP_VERSION}"
                    env.DOCKER_IMAGE = "${IMAGE_NAME}:${imageTag}"
                    sh 'docker build -t ${env.DOCKER_IMAGE} .'
                }
            }
        }

        stage('Push Image to Docker Hub') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: DOCKER_CREDENTIALS_ID, passwordVariable: 'DOCKER_PASSWORD', usernameVariable: 'DOCKER_USERNAME')]) {
                        sh 'docker login -u ${DOCKER_USERNAME} -p ${DOCKER_PASSWORD}'
                        sh 'docker push ${env.DOCKER_IMAGE}'
                    }
                }
            }
        }

        stage('Login to GCP and Get Kubeconfig for GKE') {
            steps {
                script {
                    withCredentials([file(credentialsId: 'gcloud-sa-key-file', variable: 'GCLOUD_KEY'),
                    string(credentialsId: 'gcp-project-id', variable: 'GCP_PROJECT_ID')]) {
                        sh """
                        gcloud auth activate-service-account --key-file=${GCLOUD_KEY}
                        gcloud config set project ${GCP_PROJECT_ID}
                        gcloud container clusters get-credentials ${CLUSTER_NAME} --zone ${ZONE} --project ${PROJECT_ID}
                        """
                    }
                }
            }
        }

        stage('Deploy to GKE') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: DB_CREDENTIALS_ID, passwordVariable: 'MYSQL_ROOT_PASSWORD', usernameVariable: 'MYSQL_USER'),
                    string(credentialsId: 'tiingo-api-key', variable: 'API_KEY'),
                    string(credentialsId: 'db-name', variable: 'MYSQL_DATABASE')]) {
                        sh """
                        helm upgrade \
                        --install trading-app ./trading-app-chart \
                        --set secret.trading.data.API_KEY=${API_KEY},\
                        secret.trading.data.MYSQL_USER=${MYSQL_USER},\
                        secret.mysql.data.MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD},\
                        secret.mysql.data.MYSQL_DATABASE=${MYSQL_DATABASE},\
                        deployment.trading.containers.image=${env.DOCKER_IMAGE}
                        """
                    }
                }
            }
        }
    }
}