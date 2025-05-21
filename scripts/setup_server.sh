#!/bin/bash

# Update system
sudo yum update -y

# Install required packages
sudo yum install -y python3-pip python3-devel nginx

# Add PostgreSQL repository for Amazon Linux 2023
sudo tee /etc/yum.repos.d/pgdg.repo << EOF
[pgdg15]
name=PostgreSQL 15 for RHEL/CentOS 8 - x86_64
baseurl=https://download.postgresql.org/pub/repos/yum/15/redhat/rhel-8-x86_64
enabled=1
gpgcheck=1
gpgkey=https://download.postgresql.org/pub/repos/yum/RPM-GPG-KEY-PGDG
EOF

# Install PostgreSQL
sudo yum install -y postgresql15 postgresql15-server

# Initialize PostgreSQL
sudo postgresql-setup --initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Create application directory and copy files
sudo mkdir -p /var/www/waterlevel
sudo cp -r /home/ec2-user/var/www/waterlevel/* /var/www/waterlevel/
sudo chown -R ec2-user:ec2-user /var/www/waterlevel

# Setup PostgreSQL
sudo -u postgres psql -c "CREATE USER waterlevel WITH PASSWORD 'sa';"
sudo -u postgres psql -c "CREATE DATABASE waterlevel;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE waterlevel TO waterlevel;"
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'sa';"

# Setup Python environment
cd /var/www/waterlevel
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create systemd service for scheduler
sudo tee /etc/systemd/system/waterlevel-scheduler.service << EOF
[Unit]
Description=Water Level Data Scheduler
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/var/www/waterlevel
Environment="PATH=/var/www/waterlevel/venv/bin"
EnvironmentFile=/var/www/waterlevel/.env
ExecStart=/var/www/waterlevel/venv/bin/python scripts/scheduler.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for API
sudo tee /etc/systemd/system/waterlevel-api.service << EOF
[Unit]
Description=Water Level API
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/var/www/waterlevel
Environment="PATH=/var/www/waterlevel/venv/bin"
ExecStart=/var/www/waterlevel/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Setup Nginx
sudo mkdir -p /etc/nginx/conf.d
sudo tee /etc/nginx/conf.d/waterlevel.conf << EOF
server {
    listen 8080;
    server_name _;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable and start Nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# Enable and start services
sudo systemctl enable waterlevel-scheduler
sudo systemctl enable waterlevel-api
sudo systemctl start waterlevel-scheduler
sudo systemctl start waterlevel-api

# Setup automatic updates
sudo yum install -y dnf-automatic
sudo systemctl enable dnf-automatic.timer
sudo systemctl start dnf-automatic.timer

# Change PostgreSQL configuration
echo '# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                md5
host    all             postgres        127.0.0.1/32            md5
host    all             postgres        ::1/128                 md5' > /tmp/pg_hba.conf

sudo cp /tmp/pg_hba.conf /var/lib/pgsql/data/pg_hba.conf

# Restart PostgreSQL
sudo systemctl restart postgresql 