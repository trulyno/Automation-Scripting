# Lab 05: Ansible Automation for Server Configuration

## Project Description

This project demonstrates the implementation of an automated CI/CD infrastructure using Jenkins, Docker, and Ansible for PHP application deployment. The system consists of four main components:

1. **Jenkins Controller** - Orchestrates all automation pipelines
2. **SSH Agent** - Executes PHP project builds and unit tests
3. **Ansible Agent** - Runs Ansible playbooks for server configuration
4. **Test Server** - Target environment for PHP application deployment

The infrastructure is containerized using Docker Compose, enabling isolated and reproducible environments. Jenkins pipelines automate the entire workflow from building and testing to server configuration and deployment.

## Prerequisites

- Docker and Docker Compose installed
- Git repository with PHP project containing unit tests
- GitHub account for version control
- Basic understanding of Jenkins, Ansible, and Docker

## Steps for Configuring Jenkins Controller

### 1. Start Jenkins Container

```bash
cd lab05
docker compose up -d jenkins-controller
```

### 2. Initial Jenkins Setup

1. Retrieve the initial admin password:
```bash
docker exec jenkins-controller cat /var/jenkins_home/secrets/initialAdminPassword
```

2. Open browser and navigate to `http://localhost:8080`
3. Enter the initial admin password
4. Select "Install suggested plugins"
5. Create first admin user account

### 3. Install Required Plugins

Navigate to **Manage Jenkins** → **Manage Plugins** → **Available** and install:

- **Docker Plugin** - For Docker integration
- **Docker Pipeline** - For Docker-based pipeline steps
- **SSH Agent Plugin** - For SSH credential management

### 4. Configure SSH Credentials

#### For SSH Agent:
1. Go to **Manage Jenkins** → **Manage Credentials** → **System** → **Global credentials**
2. Click **Add Credentials**
3. Select **SSH Username with private key**
4. ID: `ssh-agent-key`
5. Username: `jenkins`
6. Private Key: Enter directly (paste contents of `secrets/jenkins_ssh_agent_key`)

#### For Ansible Agent:
1. Repeat the process above
2. ID: `ansible-agent-key`
3. Username: `jenkins`
4. Private Key: Enter directly (paste contents of `secrets/jenkins_ansible_agent_key`)

## Steps for Setting Up SSH Agent

### 1. Create SSH Keys

```bash
cd lab05
mkdir -p secrets
ssh-keygen -t rsa -b 4096 -f secrets/jenkins_ssh_agent_key -N ""
```

### 2. Create Dockerfile.ssh_agent

The SSH agent Dockerfile includes:
- Base image: `jenkins/ssh-agent:latest-jdk17`
- PHP CLI and extensions (php-xml, php-mbstring, php-curl, php-zip)
- Composer for dependency management
- Git for repository operations
- Proper user permissions for Jenkins

Key components:
```dockerfile
FROM jenkins/ssh-agent:latest-jdk17
USER root
RUN apt-get update && apt-get install -y \
    php-cli php-xml php-mbstring php-curl php-zip \
    curl git unzip wget ca-certificates
RUN curl -sS https://getcomposer.org/installer | php -- \
    --install-dir=/usr/local/bin --filename=composer
```

### 3. Add SSH Agent to Docker Compose

The `compose.yml` includes the ssh-agent service with:
- Build context pointing to Dockerfile.ssh_agent
- Environment variable for Jenkins public key
- Network connectivity to jenkins-network

### 4. Build and Start SSH Agent

```bash
docker compose up -d --build ssh-agent
```

### 5. Verify SSH Agent

```bash
docker exec -it ssh-agent php --version
docker exec -it ssh-agent composer --version
```

## Steps for Creating and Configuring Ansible Agent

### 1. Create SSH Keys for Ansible Agent

```bash
# Key for Jenkins to connect to Ansible agent
ssh-keygen -t rsa -b 4096 -f secrets/jenkins_ansible_agent_key -N ""

# Key for Ansible agent to connect to test server
ssh-keygen -t rsa -b 4096 -f secrets/ansible_test_server_key -N ""
```

### 2. Create Dockerfile.ansible_agent

The Ansible agent Dockerfile includes:
- Base image: Ubuntu 22.04
- OpenSSH server for Jenkins connectivity
- Python 3 and pip for Ansible
- Ansible installation via pip
- Jenkins user with SSH access
- SSH keys for both Jenkins authentication and test server connection

Key features:
```dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y \
    openssh-server python3 python3-pip git sudo
RUN pip3 install ansible
COPY secrets/jenkins_ansible_agent_key.pub /home/jenkins/.ssh/authorized_keys
COPY secrets/ansible_test_server_key /home/jenkins/.ssh/id_rsa
```

### 3. Configure SSH Settings

The Dockerfile configures:
- SSH host key checking disabled for automated connections
- Proper file permissions (700 for .ssh, 600 for keys)
- SSH config file to trust all hosts automatically

### 4. Add Ansible Agent to Docker Compose

```bash
docker compose up -d --build ansible-agent
```

### 5. Verify Ansible Installation

```bash
docker exec -it ansible-agent ansible --version
docker exec -it ansible-agent ssh -V
```

## Steps for Creating the Test Server

### 1. Create SSH Keys for Test Server Access

These keys were created in the Ansible agent setup:
```bash
# Already created: secrets/ansible_test_server_key
```

### 2. Create Dockerfile.test_server

The test server Dockerfile includes:
- Base image: Ubuntu 22.04
- OpenSSH server for remote management
- Python 3 for Ansible compatibility
- Sudo for privilege escalation
- Ansible user with passwordless sudo access
- Public key authentication setup

Key configuration:
```dockerfile
FROM ubuntu:22.04
RUN useradd -m -s /bin/bash ansible && \
    echo "ansible ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
COPY secrets/ansible_test_server_key.pub /home/ansible/.ssh/authorized_keys
EXPOSE 22 80
```

### 3. Add Test Server to Docker Compose

The test server service includes:
- Port mapping: 8081:80 (Apache accessible on host port 8081)
- Network connectivity to jenkins-network
- SSH exposed on port 22 (internal to Docker network)

### 4. Start Test Server

```bash
docker compose up -d --build test-server
```

### 5. Verify Test Server Connectivity

```bash
# Test SSH connection from Ansible agent
docker exec -it ansible-agent ssh ansible@test-server "echo 'Connection successful'"
```

## Description of Ansible Playbook and Its Tasks

### Inventory File (hosts.ini)

Defines the test server connection parameters:
```ini
[test_servers]
test-server ansible_host=test-server ansible_user=ansible \
    ansible_ssh_private_key_file=/home/jenkins/.ssh/id_rsa \
    ansible_python_interpreter=/usr/bin/python3
```

### Setup Test Server Playbook (setup_test_server.yml)

This playbook configures the test server with all necessary components for hosting a PHP application.

**Tasks:**

1. **Update apt cache** - Ensures package lists are current
   ```yaml
   - name: Update apt cache
     apt:
       update_cache: yes
       cache_valid_time: 3600
   ```

2. **Install system packages** - Installs rsync and git for file operations
   ```yaml
   - name: Install system packages
     apt:
       name: [rsync, git]
       state: present
   ```

3. **Install Apache2** - Web server installation
   ```yaml
   - name: Install Apache2
     apt:
       name: apache2
       state: present
   ```

4. **Start Apache2 service** - Ensures Apache is running
   - Uses manual start with `apache2ctl` as fallback for containerized environments
   - Checks if Apache is already running before attempting start

5. **Install PHP and extensions** - Complete PHP stack for application
   ```yaml
   - name: Install PHP and extensions
     apt:
       name:
         - php
         - php-cli
         - php-common
         - php-curl
         - php-mbstring
         - php-xml
         - php-zip
         - libapache2-mod-php
       state: present
   ```

6. **Create project directory** - Sets up `/var/www/html/phpproject`
   - Owner: www-data (Apache user)
   - Permissions: 0755

7. **Configure Apache virtual host** - Creates custom virtual host configuration
   ```apache
   <VirtualHost *:80>
       ServerAdmin webmaster@localhost
       DocumentRoot /var/www/html/phpproject
       <Directory /var/www/html/phpproject>
           Options Indexes FollowSymLinks
           AllowOverride All
           Require all granted
       </Directory>
   </VirtualHost>
   ```

8. **Enable the virtual host** - Activates phpproject configuration
   ```yaml
   - name: Enable the virtual host
     command: a2ensite phpproject.conf
   ```

9. **Disable default site** - Removes default Apache welcome page
   ```yaml
   - name: Disable default site
     command: a2dissite 000-default.conf
   ```

10. **Enable Apache rewrite module** - Enables URL rewriting capabilities
    ```yaml
    - name: Enable Apache rewrite module
      apache2_module:
        name: rewrite
        state: present
    ```

11. **Restart Apache** - Applies all configuration changes
    ```yaml
    - name: Restart Apache
      shell: /usr/sbin/apache2ctl restart
    ```

### Deploy PHP Project Playbook (deploy_php_project.yml)

This playbook handles the complete deployment process of the PHP application.

**Tasks:**

1. **Install required packages** - Ensures deployment dependencies are available
2. **Check if Composer is installed** - Verifies Composer availability
3. **Download and install Composer** - Installs Composer if not present
4. **Clone PHP project** - Fetches latest code from GitHub repository
   - Repository: https://github.com/trulyno/php-site-with-unit-tests
   - Branch: main
5. **Install Composer dependencies** - Installs production dependencies
   ```bash
   composer install --no-dev --no-interaction --prefer-dist --optimize-autoloader
   ```
6. **Ensure web directory exists** - Creates target directory with correct permissions
7. **Copy project files** - Syncs project to web root using rsync
   ```bash
   rsync -av --delete /tmp/phpproject/ /var/www/html/phpproject/
   ```

## Steps for Creating Jenkins Pipelines

### 1. PHP Build and Test Pipeline (php_build_and_test_pipeline.groovy)

**Purpose:** Builds the PHP project and runs unit tests using the SSH agent.

**Pipeline Stages:**

1. **Clone Repository**
   - Connects to SSH agent using credentials
   - Clones PHP project repository
   - Removes old project directory first

2. **Install Dependencies**
   - Executes `composer install` on SSH agent
   - Installs all project dependencies including dev dependencies
   - Uses `--no-interaction --prefer-dist` for automated execution

3. **Run Unit Tests**
   - Executes PHPUnit test suite
   - Generates JUnit XML report (`test-results.xml`)
   - Command: `./vendor/bin/phpunit --log-junit test-results.xml`

4. **Report Results**
   - Copies test results from SSH agent to Jenkins
   - Uses JUnit plugin to display test results in Jenkins UI
   - Provides visual feedback on test success/failure

**Creating the Pipeline in Jenkins:**

1. Navigate to Jenkins dashboard → **New Item**
2. Enter name: "PHP Build and Test"
3. Select **Pipeline** → Click **OK**
4. Under **Pipeline** section:
   - Definition: **Pipeline script from SCM**
   - SCM: **Git**
   - Repository URL: Your GitHub repository
   - Script Path: `lab05/pipelines/php_build_and_test_pipeline.groovy`
5. Save and run the pipeline

### 2. Ansible Setup Pipeline (ansible_setup_pipeline.groovy)

**Purpose:** Configures the test server using Ansible playbooks.

**Pipeline Stages:**

1. **Clone Repository**
   - Connects to Ansible agent via SSH
   - Clones repository containing Ansible playbooks
   - Navigates to `lab05/ansible` directory

2. **Execute Ansible Playbook**
   - Runs `ansible-playbook -i hosts.ini setup_test_server.yml`
   - Configures Apache, PHP, and virtual host
   - Sets up complete web server environment

**Creating the Pipeline in Jenkins:**

1. Navigate to Jenkins dashboard → **New Item**
2. Enter name: "Configure Test Server"
3. Select **Pipeline** → Click **OK**
4. Under **Pipeline** section:
   - Definition: **Pipeline script from SCM**
   - SCM: **Git**
   - Repository URL: Your GitHub repository
   - Script Path: `lab05/pipelines/ansible_setup_pipeline.groovy`
5. Save and run the pipeline

### 3. PHP Deploy Pipeline (php_deploy_pipeline.groovy)

**Purpose:** Deploys the PHP application to the configured test server.

**Pipeline Stages:**

1. **Clone Repository**
   - Connects to Ansible agent
   - Clones repository containing deployment playbook

2. **Deploy to Test Server**
   - Runs `ansible-playbook -i hosts.ini deploy_php_project.yml`
   - Clones PHP project on test server
   - Installs Composer dependencies
   - Copies files to Apache web root
   - Sets correct permissions

**Creating the Pipeline in Jenkins:**

1. Navigate to Jenkins dashboard → **New Item**
2. Enter name: "Deploy PHP Project"
3. Select **Pipeline** → Click **OK**
4. Under **Pipeline** section:
   - Definition: **Pipeline script from SCM**
   - SCM: **Git**
   - Repository URL: Your GitHub repository
   - Script Path: `lab05/pipelines/php_deploy_pipeline.groovy`
5. Save and run the pipeline

### Pipeline Execution Order

1. **First:** Run "Configure Test Server" - Sets up the environment
2. **Second:** Run "PHP Build and Test" - Verifies code quality
3. **Third:** Run "Deploy PHP Project" - Deploys to test server

### Testing the Deployment

After running all pipelines successfully:

1. Open browser and navigate to `http://localhost:8081`
2. Verify the PHP application loads correctly
3. Test application functionality
4. Check Apache logs if issues occur:
   ```bash
   docker exec test-server cat /var/log/apache2/error.log
   docker exec test-server cat /var/log/apache2/access.log
   ```

## Questions and Answers

### What are the advantages of using Ansible for server configuration?

1. **Idempotency** - Ansible ensures that running the same playbook multiple times produces the same result without causing unintended changes. This makes configurations predictable and safe to re-run.

2. **Agentless Architecture** - Unlike other configuration management tools, Ansible doesn't require agents to be installed on target servers. It uses SSH for communication, reducing overhead and complexity.

3. **Human-Readable Syntax** - Ansible playbooks use YAML, which is easy to read and write. This makes playbooks accessible to team members who may not be developers.

4. **Declarative Language** - You describe the desired state, not the steps to achieve it. Ansible figures out how to get from the current state to the desired state.

5. **Extensive Module Library** - Ansible provides modules for virtually every system administration task (package management, service control, file operations, cloud provisioning, etc.).

6. **Reusability** - Playbooks and roles can be shared across projects and teams, promoting best practices and reducing duplication.

7. **Version Control Integration** - Playbooks are text files that integrate seamlessly with Git, enabling infrastructure as code practices with full audit trails.

8. **Orchestration Capabilities** - Can coordinate complex multi-tier deployments across multiple servers in a specific order.

9. **Error Handling** - Built-in error handling and rollback capabilities ensure reliable deployments.

10. **Cross-Platform Support** - Works with Linux, Windows, cloud providers, network devices, and containers.

### What other Ansible modules exist for configuration management?

Ansible provides hundreds of modules across various categories:

**System Modules:**
- `user` - Manage user accounts
- `group` - Manage groups
- `cron` - Manage cron jobs
- `systemd` - Manage systemd services
- `sysctl` - Manage kernel parameters
- `mount` - Manage filesystems and mount points
- `hostname` - Manage system hostname

**Package Management:**
- `apt` - Manage packages on Debian/Ubuntu
- `yum` / `dnf` - Manage packages on RedHat/CentOS/Fedora
- `pip` - Manage Python packages
- `npm` - Manage Node.js packages
- `gem` - Manage Ruby gems

**File Operations:**
- `file` - Manage files and directories
- `copy` - Copy files to remote hosts
- `template` - Deploy Jinja2 templates
- `lineinfile` - Modify specific lines in files
- `blockinfile` - Insert/update/remove text blocks
- `fetch` - Retrieve files from remote hosts
- `synchronize` - rsync-based file synchronization

**Web Server Modules:**
- `apache2_module` - Enable/disable Apache modules
- `htpasswd` - Manage htpasswd files
- `nginx` - Manage Nginx configuration

**Database Modules:**
- `mysql_db` - Manage MySQL databases
- `mysql_user` - Manage MySQL users
- `postgresql_db` - Manage PostgreSQL databases
- `mongodb_user` - Manage MongoDB users

**Cloud Modules:**
- `ec2` - Manage AWS EC2 instances
- `azure_rm_virtualmachine` - Manage Azure VMs
- `gcp_compute_instance` - Manage GCP instances
- `docker_container` - Manage Docker containers
- `docker_image` - Manage Docker images

**Network Modules:**
- `firewalld` - Manage firewalld rules
- `iptables` - Manage iptables rules
- `ufw` - Manage UFW firewall
- `nmcli` - Manage NetworkManager connections

**Security Modules:**
- `selinux` - Manage SELinux settings
- `authorized_key` - Manage SSH authorized keys
- `openssl_certificate` - Manage SSL certificates
- `acl` - Manage file ACLs

**Notification Modules:**
- `slack` - Send Slack notifications
- `mail` - Send email notifications
- `telegram` - Send Telegram messages

### What problems did you encounter when creating the Ansible playbook and how did you solve them?

**Problem: Rsync Not Available**

**Issue:** The synchronize module failed because rsync wasn't installed on the test server.

**Solution:** Added rsync to the package installation task:
```yaml
- name: Install system packages
  apt:
    name:
      - rsync
      - git
    state: present
```
