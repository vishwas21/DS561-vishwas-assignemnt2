#! /bin/bash
sudo apt update
sudo apt -y upgrade
sudo apt-get install python3-pip -y
sudo apt-get install git -y
sudo apt-get install python3-venv -y
cd /home/vishwasb
rm -r DS561-vishwas-assignments
rm -r assignment8
git clone https://github.com/vishwas21/DS561-vishwas-assignments.git
cd DS561-vishwas-assignments
pwd
cp -r /home/vishwasb/DS561-vishwas-assignments/assignment8 /home/vishwasb
cd /home/vishwasb/assignment8
python3 -m venv env
source /home/vishwasb/assignment8/env/bin/activate
pip3 install -r requirements.txt
deactivate
touch assignment8.service
echo "[Unit]
Description=Gunicorn instance to serve Assignment 4 app
After=network.target

[Service]
User=vishwasb
Group=www-data
WorkingDirectory=/home/vishwasb/assignment8
Environment="PATH=/home/vishwasb/assignment8/env/bin"
ExecStart=/home/vishwasb/assignment8/env/bin/gunicorn --workers 3 --bind 0.0.0.0:8080 wsgi:app

[Install]
WantedBy=multi-user.target" > assignment8.service
sudo chown root:root assignment8.service
sudo cp assignment8.service /etc/systemd/system/assignment8.service
sudo chown vishwasb:vishwasb /home/vishwasb/assignment8
sudo systemctl stop assignment8
sudo systemctl daemon-reload
sudo systemctl start assignment8
systemctl daemon-reload
sudo systemctl restart assignment8
sudo systemctl enable assignment8