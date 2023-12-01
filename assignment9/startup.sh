#! /bin/bash
sudo apt update
sudo apt -y upgrade
sudo apt-get install python3-pip -y
sudo apt-get install git -y
sudo apt-get install python3-venv -y
cd /home/vishwasb
rm -r DS561-vishwas-assignments
rm -r assignment9
git clone https://github.com/vishwas21/DS561-vishwas-assignments.git
cd DS561-vishwas-assignments
pwd
cp -r /home/vishwasb/DS561-vishwas-assignments/assignment9 /home/vishwasb
cd /home/vishwasb/assignment9
python3 -m venv env
source /home/vishwasb/assignment9/env/bin/activate
pip3 install -r requirements.txt
deactivate
touch assignment9.service
echo "[Unit]
Description=Gunicorn instance to serve Assignment 4 app
After=network.target

[Service]
User=vishwasb
Group=www-data
WorkingDirectory=/home/vishwasb/assignment9
Environment="PATH=/home/vishwasb/assignment9/env/bin"
ExecStart=/home/vishwasb/assignment9/env/bin/gunicorn --workers 3 --bind 0.0.0.0:8085 wsgi:app

[Install]
WantedBy=multi-user.target" > assignment9.service
sudo chown root:root assignment9.service
sudo cp assignment9.service /etc/systemd/system/assignment9.service
sudo chown vishwasb:vishwasb /home/vishwasb/assignment9
sudo systemctl stop assignment9
sudo systemctl daemon-reload
sudo systemctl start assignment9
sudo systemctl daemon-reload
sudo systemctl restart assignment9
sudo systemctl enable assignment9