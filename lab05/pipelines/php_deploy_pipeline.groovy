pipeline {
    agent any
    
    stages {
        stage('Clone Repository') {
            steps {
                script {
                    sshagent(credentials: ['ansible-agent-key']) {
                        sh '''
                            ssh -o StrictHostKeyChecking=no jenkins@ansible-agent '
                                rm -rf /home/jenkins/ansible &&
                                git clone https://github.com/trulyno/php-site-with-unit-tests /home/jenkins/ansible
                            '
                        '''
                    }
                }
            }
        }
        
        stage('Deploy to Test Server') {
            steps {
                script {
                    sshagent(credentials: ['ansible-agent-key']) {
                        sh '''
                            ssh jenkins@ansible-agent '
                                cd /home/jenkins/ansible/lab05/ansible &&
                                ansible-playbook -i hosts.ini deploy_php_project.yml
                            '
                        '''
                    }
                }
            }
        }
    }
}