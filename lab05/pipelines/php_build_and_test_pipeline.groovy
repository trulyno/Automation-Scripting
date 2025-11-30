pipeline {
    agent any
    
    stages {
        stage('Clone Repository') {
            steps {
                script {
                    sshagent(credentials: ['ssh-agent-key']) {
                        sh '''
                            ssh -o StrictHostKeyChecking=no jenkins@ssh-agent '
                                rm -rf /home/jenkins/phpproject &&
                                git clone https://github.com/trulyno/php-site-with-unit-tests /home/jenkins/phpproject
                            '
                        '''
                    }
                }
            }
        }
        
        stage('Install Dependencies') {
            steps {
                script {
                    sshagent(credentials: ['ssh-agent-key']) {
                        sh '''
                            ssh jenkins@ssh-agent '
                                cd /home/jenkins/phpproject &&
                                composer install --no-interaction --prefer-dist
                            '
                        '''
                    }
                }
            }
        }
        
        stage('Run Unit Tests') {
            steps {
                script {
                    sshagent(credentials: ['ssh-agent-key']) {
                        sh '''
                            ssh jenkins@ssh-agent '
                                cd /home/jenkins/phpproject &&
                                ./vendor/bin/phpunit --log-junit test-results.xml
                            '
                        '''
                    }
                }
            }
        }
        
        stage('Report Results') {
            steps {
                script {
                    sshagent(credentials: ['ssh-agent-key']) {
                        sh '''
                            scp jenkins@ssh-agent:/home/jenkins/phpproject/test-results.xml .
                        '''
                    }
                    junit 'test-results.xml'
                }
            }
        }
    }
}