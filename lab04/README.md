# Jenkins CI/CD Pipeline Setup Report

## 1. Project Description

This project demonstrates the configuration and implementation of a Jenkins-based Continuous Integration/Continuous Deployment (CI/CD) pipeline for automating DevOps tasks. The setup includes a Jenkins Controller managing build processes and an SSH Agent for executing pipeline jobs in an isolated environment.

The project utilizes Docker and Docker Compose to create a containerized infrastructure consisting of two primary services: a Jenkins Controller service that provides the web interface and orchestrates builds, and an SSH Agent service configured with PHP-CLI for running PHP application tests. The pipeline is designed to automate the testing workflow for a PHP application with unit tests, demonstrating practical DevOps automation capabilities.

## 2. Steps for Setting Up Jenkins Controller

### Creating the Docker Compose Configuration

First, create a `docker-compose.yml` file with the Jenkins Controller service definition:

```yaml
services:
  jenkins-controller:
    image: jenkins/jenkins:lts
    container_name: jenkins-controller
    ports:
      - "8080:8080"
      - "50000:50000"
    volumes:
      - jenkins_home:/var/jenkins_home
    networks:
      - jenkins-network

volumes:
  jenkins_home:
  jenkins_agent_volume:

networks:
  jenkins-network:
    driver: bridge
```

This configuration defines the Jenkins Controller using the official Long-Term Support (LTS) image. Port 8080 is exposed for the web interface, while port 50000 is used for agent communication. The `jenkins_home` volume persists Jenkins configuration and job data across container restarts.

### Starting the Jenkins Controller

Launch the Jenkins Controller container by running the following command in the directory containing your `docker-compose.yml` file:

```bash
docker-compose up -d
```

### Initial Jenkins Configuration

After the container starts, retrieve the initial administrator password:

```bash
docker exec jenkins-controller cat /var/jenkins_home/secrets/initialAdminPassword
```

Access the Jenkins web interface by navigating to `http://localhost:8080` in your browser. Enter the initial administrator password when prompted.

Follow the setup wizard:
- Select "Install suggested plugins" to install commonly used plugins
- Create your first admin user account by providing username, password, full name, and email address
- Confirm the Jenkins URL (default is `http://localhost:8080`)
- Click "Start using Jenkins" to complete the initial setup

The Jenkins Controller is now ready to manage build jobs and coordinate with agent nodes.

## 3. Steps for Setting Up SSH Agent

### Generating SSH Keys

Create a `secrets` directory in your project root and generate SSH key pairs for secure authentication:

```bash
mkdir secrets
cd secrets
ssh-keygen -t rsa -b 4096 -f jenkins_agent_ssh_key -N ""
cd ..
```

This creates two files: `jenkins_agent_ssh_key` (private key) and `jenkins_agent_ssh_key.pub` (public key). The private key will be registered in Jenkins, while the public key will be provided to the SSH agent container.

### Creating the SSH Agent Dockerfile

Create a `Dockerfile` in your project root with the following content:

```dockerfile
FROM jenkins/ssh-agent

# Install PHP-CLI for running PHP tests
RUN apt-get update && apt-get install -y php-cli && apt-get clean
```

This extends the base Jenkins SSH agent image with PHP-CLI, which is required for running PHP unit tests in the pipeline.

### Configuring the SSH Agent Service

Add the SSH Agent service to your `docker-compose.yml` file:

```yaml
  ssh-agent:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ssh-agent
    environment:
      - JENKINS_AGENT_SSH_PUBKEY=${JENKINS_AGENT_SSH_PUBKEY}
    volumes:
      - jenkins_agent_volume:/home/jenkins/agent
    depends_on:
      - jenkins-controller
    networks:
      - jenkins-network
```

### Setting Up Environment Variables

Create a `.env` file in your project root and add the public SSH key:

```bash
echo "JENKINS_AGENT_SSH_PUBKEY=$(cat secrets/jenkins_agent_ssh_key.pub)" > .env
```

This makes the public key available to the SSH agent container through the environment variable.

### Starting the SSH Agent

Restart the Docker Compose project to build and start the SSH agent:

```bash
docker-compose down
docker-compose up -d
```

### Registering SSH Credentials in Jenkins

Navigate to the Jenkins web interface and register the SSH private key:

1. Go to `Manage Jenkins` → `Manage Credentials`
2. Click on `(global)` domain
3. Click `Add Credentials`
4. Select `SSH Username with private key` as the kind
5. Set the following values:
   - **Scope**: Global
   - **ID**: `ssh-agent-key` (or any meaningful identifier)
   - **Description**: SSH key for Jenkins agent
   - **Username**: `jenkins`
   - **Private Key**: Select "Enter directly" and paste the contents of `secrets/jenkins_agent_ssh_key`
6. Click `Create`

### Adding the SSH Agent Node

Configure Jenkins to recognize and use the SSH agent:

1. Go to `Manage Jenkins` → `Manage Nodes and Clouds`
2. Click `New Node`
3. Enter node name: `ssh-agent1`
4. Select `Permanent Agent`
5. Click `Create`
6. Configure the node with these settings:
   - **Name**: `ssh-agent1`
   - **Description**: SSH agent for PHP builds
   - **Remote root directory**: `/home/jenkins/agent`
   - **Labels**: `php-agent`
   - **Usage**: Use this node as much as possible
   - **Launch method**: Launch agents via SSH
   - **Host**: `ssh-agent`
   - **Credentials**: Select the SSH credentials created earlier (`ssh-agent-key`)
   - **Host Key Verification Strategy**: Non verifying Verification Strategy
7. Click `Save`

The agent should connect automatically. Check the node status page to verify the connection is successful.

## 4. Steps for Creating and Configuring Jenkins Pipeline

### Selecting a PHP Project Repository

For this demonstration, the PHP project repository is located at:
```
https://github.com/trulyno/php-site-with-unit-tests
```

This repository contains a PHP application with PHPUnit tests and a Composer configuration for dependency management.

### Creating a New Pipeline Job

In the Jenkins web interface:

1. Click `New Item` from the dashboard
2. Enter a name for your pipeline (e.g., "PHP Pipeline")
3. Select `Pipeline` as the project type
4. Click `OK`

### Configuring Pipeline Settings

In the pipeline configuration page:

1. **General Section**:
   - Add a description: "Automated testing pipeline for PHP application"
   - Optionally check "GitHub project" and enter the repository URL

2. **Build Triggers** (optional):
   - Check "GitHub hook trigger for GITScm polling" if you want automatic builds on code push
   - Or check "Poll SCM" and set a schedule (e.g., `H/5 * * * *` for every 5 minutes)

3. **Pipeline Section**:
   - **Definition**: Select "Pipeline script from SCM"
   - **SCM**: Select "Git"
   - **Repository URL**: `https://github.com/trulyno/php-site-with-unit-tests`
   - **Credentials**: None (for public repositories)
   - **Branch Specifier**: `*/main` (or `*/master` depending on your default branch)
   - **Script Path**: `Jenkinsfile`

4. Click `Save`

### Creating the Jenkinsfile

Create a `Jenkinsfile` in the root of your PHP project repository with the following content:

```groovy
pipeline {
    agent {
        label 'php-agent'
    }
    
    stages {        
        stage('Install Dependencies') {
            steps {
                echo 'Preparing project...'
                sh '''
                    composer install --no-interaction --prefer-dist
                '''
            }
        }
        
        stage('Test') {
            steps {
                echo 'Running tests...'
                sh './vendor/bin/phpunit'
            }
        }
    }
    
    post {
        always {
            echo 'Pipeline completed.'
        }
        success {
            echo 'All stages completed successfully!'
        }
        failure {
            echo 'Errors detected in the pipeline.'
        }
    }
}
```

### Pipeline Explanation

The pipeline consists of the following components:

**Agent Configuration**: The `agent` block specifies that jobs should run on nodes with the label `php-agent`, ensuring they execute on the SSH agent container with PHP-CLI installed.

**Install Dependencies Stage**: Uses Composer to install project dependencies defined in `composer.json`. The `--no-interaction` flag prevents prompts, and `--prefer-dist` downloads distribution packages for faster installation.

**Test Stage**: Executes PHPUnit tests using the vendor binary installed by Composer. This runs all test cases defined in the project's test suite.

**Post Actions**: The `post` block defines actions that run after pipeline completion regardless of success or failure, providing feedback about the build status.

### Running the Pipeline

Execute the pipeline manually:

1. Navigate to your pipeline job in Jenkins
2. Click `Build Now`
3. Click on the build number in the Build History to view detailed output
4. Click `Console Output` to see real-time logs

The pipeline should complete successfully with all tests passing. The console output will show each stage execution, dependency installation progress, and test results.

### Verifying Pipeline Execution

A successful pipeline run should display:
- Green checkmarks for all stages
- Console output showing Composer dependency installation
- PHPUnit test results with all tests passing
- Success message: "All stages completed successfully!"

![Succesful execution of the pipeline](pipeline_success.png)

If the pipeline fails, the console output will indicate which stage failed and provide error messages for troubleshooting.

## 5. Questions and Answers

### What are the advantages of using Jenkins for DevOps task automation?

Jenkins offers numerous advantages that make it a preferred choice for DevOps automation:

**Open Source and Free**: Jenkins is completely free to use with no licensing costs, making it accessible to organizations of all sizes. The large open-source community continuously contributes plugins, improvements, and support.

**Extensive Plugin Ecosystem**: With over 1,800 plugins available, Jenkins can integrate with virtually any tool in the DevOps ecosystem, including version control systems (Git, SVN), build tools (Maven, Gradle), testing frameworks, deployment platforms, and monitoring solutions.

**Pipeline as Code**: Jenkins supports defining entire CI/CD pipelines as code using Jenkinsfile, which can be version-controlled alongside application code. This approach enables reproducibility, peer review, and easy pipeline modifications across projects.

**Distributed Builds**: Jenkins supports master-agent architecture, allowing workload distribution across multiple machines. This improves build performance, enables parallel execution, and provides isolation between different build environments.

**Flexibility and Customization**: Jenkins is highly configurable and adaptable to various workflows, programming languages, and deployment strategies. It supports declarative and scripted pipeline syntaxes to accommodate different complexity levels.

**Strong Community Support**: The active Jenkins community provides extensive documentation, tutorials, forums, and regular updates, making it easier to troubleshoot issues and implement best practices.

**Integration with Modern Technologies**: Jenkins seamlessly integrates with containerization technologies like Docker and Kubernetes, cloud platforms (AWS, Azure, GCP), and modern development practices including infrastructure as code and GitOps workflows.

**Automatic Testing and Continuous Feedback**: Jenkins automatically triggers builds and tests on code commits, providing rapid feedback to developers about code quality, test failures, and integration issues, which accelerates the development cycle.

### What other types of Jenkins agents exist?

Jenkins supports several types of agents beyond SSH agents, each suited for different use cases:

**JNLP Agents (Java Web Start)**: These agents connect to the Jenkins controller using the Java Network Launch Protocol. The agent initiates the connection, which is useful when the controller cannot directly access the agent machine due to network restrictions or firewalls.

**Docker Agents**: Jenkins can dynamically provision agents as Docker containers on-demand. This approach provides clean, isolated build environments for each job and automatically scales resources based on workload. The Docker plugin allows specifying different images for different job types.

**Kubernetes Agents**: When running Jenkins in Kubernetes, the Kubernetes plugin can dynamically create agent pods on-demand. Each build runs in a fresh pod with specified resource limits, and pods are automatically terminated after builds complete, optimizing resource utilization.

**Windows Service Agents**: For Windows environments, agents can be installed and run as Windows services, providing persistent agents on Windows machines for builds requiring Windows-specific tools or environments.

**Static Agents (Permanent Agents)**: These are long-running agents manually configured on specific machines. They remain connected to the controller and are suitable for environments requiring consistent build infrastructure with specific tools or configurations.

**Cloud-Based Agents**: Jenkins integrates with cloud providers (AWS EC2, Azure VMs, Google Compute Engine) to dynamically provision virtual machine agents on-demand. These agents are created when builds are queued and terminated when idle, optimizing cost.

**MacOS Agents**: For iOS and macOS application builds, Jenkins agents can be configured on Mac hardware, providing access to Xcode and other Apple development tools required for building and testing Apple platform applications.

Each agent type offers different advantages regarding scalability, resource management, security, and environment isolation, allowing teams to choose the most appropriate solution for their infrastructure and requirements.

### What problems did you encounter when setting up Jenkins and how did you solve them?

**Problem: SSH Agent Connection Failures**

An issue I ran into was the SSH agent failing to connect to the Jenkins controller with errors like "Connection refused" or "Host key verification failed."

*Solution*: The problem was solved by ensuring the SSH key was passed properly in the .env (public key in full format "ssh-ed25519 AAAA... yourkey") and in the credentials creation (private key including the "-----BEGIN OPENSSH PRIVATE KEY-----" and "-----END OPENSSH PRIVATE KEY-----").

**Problem: Composer Not Found in SSH Agent**

When running the pipeline, the "Install Dependencies" stage failed with "composer: command not found" because the base SSH agent image doesn't include PHP development tools.

*Solution*: The Dockerfile was extended to install not only `php-cli` but also Composer. The corrected Dockerfile includes:
```dockerfile
# Install PHP CLI and common extensions for PHPUnit
RUN apt-get update && \
    apt-get install -y \
        php-cli \
        php-xml \
        php-curl \
        php-mbstring \
        unzip \
        git \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Install Composer globally
RUN curl -sS https://getcomposer.org/installer | php && \
    mv composer.phar /usr/local/bin/composer
```