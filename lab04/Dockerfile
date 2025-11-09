FROM jenkins/ssh-agent

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