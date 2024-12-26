pipeline {
    agent any
    
    stages {
        stage('Test') {
            steps {
                sh 'git rev-parse --short HEAD'
            }
        }
    }
}