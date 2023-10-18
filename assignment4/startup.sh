#! /bin/bash
sudo apt update
sudo apt -y upgrade
sudo apt-get install python3-pip
sudo apt-get install git
cd ~
rm -r DS561-vishwas-assignments
git clone https://github.com/vishwas21/DS561-vishwas-assignments.git
cd DS561-vishwas-assignments
cd assignment4
pip3 install -r requirements.txt
touch assignment4.service
echo "[Unit]
Description=Gunicorn instance to serve Assignment 4 app
After=network.target

[Service]
User=vishwasb
Group=www-data
WorkingDirectory=/home/vishwasb/assignment4
Environment="PATH=/home/vishwasb/assignment4/env/bin"
ExecStart=/home/vishwasb/assignment4/env/bin/gunicorn --workers 3 --bind 0.0.0.0:8080 wsgi:app

[Install]
WantedBy=multi-user.target" > assignment4.service
sudo chown root:root assignment4.service
sudo cp assignment4.service /etc/systemd/system/assignment4.service
sudo systemctl stop assignment4
sudo systemctl daemon-reload
sudo systemctl start assignment4
sudo systemctl enable assignment4