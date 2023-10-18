gcloud compute --project=ds561-visb-assignment firewall-rules create allow-https-8080 --description="Custom Firewall rule to allow external traffic" --direction=INGRESS --priority=1000 --network=default --action=ALLOW --rules=tcp:8080 --source-ranges=0.0.0.0/0 --target-tags=http-server-8080

gcloud compute instances create assignment4-http-vm --project=ds561-visb-assignment --zone=us-central1-a --machine-type=e2-standard-2 --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default --maintenance-policy=MIGRATE --provisioning-model=STANDARD --service-account=776935284294-compute@developer.gserviceaccount.com --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append --tags=http-server-8080,http-server,https-server --create-disk=auto-delete=yes,boot=yes,device-name=assignment4-http-vm,image=projects/ubuntu-os-cloud/global/images/ubuntu-2004-focal-v20230918,mode=rw,size=10,type=projects/ds561-visb-assignment/zones/us-central1-a/diskTypes/pd-balanced --no-shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring --labels=goog-ec-src=vm_add-gcloud --reservation-affinity=any

gcloud compute scp --recurse ./ assignment4-http-vm:~/assignment4 --zone us-central1-a

gcloud compute ssh assignment4-http-vm --zone us-central1-a

gcloud compute addresses create visb-a4-ip-address \
 --region=us-central1

gcloud compute addresses describe visb-a4-ip-address

gcloud compute instances create assignment4-http-vm --address=34.27.2.159 --zone=us-central1-a

gcloud compute instances describe assignment4-http-vm

gcloud compute instances delete-access-config assignment4-http-vm \
 --access-config-name="External NAT" \
 --zone=us-central1-a

gcloud compute instances add-access-config assignment4-http-vm \
--access-config-name="Exteral Static IP" --address=34.27.2.159 \
--zone=us-central1-a

---

gunicorn --bind 0.0.0.0:8080 wsgi:app

sudo nano /etc/systemd/system/assignment4.service

[Unit]
Description=Gunicorn instance to serve Assignment 4 app
After=network.target

[Service]
User=vishwasb
Group=www-data
WorkingDirectory=/home/vishwasb/assignment4
Environment="PATH=/home/vishwasb/assignment4/env/bin"
ExecStart=/home/vishwasb/assignment4/env/bin/gunicorn --workers 3 --bind 0.0.0.0:8080 wsgi:app

[Install]
WantedBy=multi-user.target

gcloud compute instances create assignment4-http-client \
 --project=ds561-visb-assignment \
 --zone=us-central1-a \
 --machine-type=e2-micro \
 --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default \
 --maintenance-policy=MIGRATE \
 --provisioning-model=STANDARD \
 --service-account=776935284294-compute@developer.gserviceaccount.com \
 --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append \
 --tags=http-server,https-server \
 --create-disk=auto-delete=yes,boot=yes,device-name=assignment4-http-client,image=projects/ubuntu-os-cloud/global/images/ubuntu-2004-focal-v20230918,mode=rw,size=10,type=projects/ds561-visb-assignment/zones/us-central1-a/diskTypes/pd-balanced \
 --no-shielded-secure-boot \
 --shielded-vtpm \
 --shielded-integrity-monitoring \
 --labels=goog-ec-src=vm_add-gcloud \
 --reservation-affinity=any

gcloud compute scp http_client.py assignment4-http-client:~/ --zone us-central1-a

python3 http_client.py -d 34.27.2.159 -p 8080 -b none -i 10000 -n 1 -v -w none
