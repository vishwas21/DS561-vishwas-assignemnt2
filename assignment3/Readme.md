gcloud functions deploy ds561-python-http-server \
 --gen2 \
 --runtime=python311 \
 --region=us-central1 \
 --source=. \
 --entry-point=ds561_fileRequest_http \
 --trigger-http \
 --allow-unauthenticated \
 --memory=256MB \
 --max-instances=83

gcloud functions describe ds561-python-http-server \
 --region us-central1

gcloud functions describe ds561-python-http-server \
 --region us-central1
buildConfig:
build: projects/776935284294/locations/us-central1/builds/2f374b1b-59d1-4ca5-a2d6-a0297a26c471
dockerRegistry: ARTIFACT_REGISTRY
entryPoint: ds561_fileRequest_http
runtime: python311
source:
storageSource:
bucket: gcf-v2-sources-776935284294-us-central1
generation: '1696977664596551'
object: ds561-python-http-server/function-source.zip
sourceProvenance:
resolvedStorageSource:
bucket: gcf-v2-sources-776935284294-us-central1
generation: '1696977664596551'
object: ds561-python-http-server/function-source.zip
environment: GEN_2
labels:
deployment-tool: cli-gcloud
name: projects/ds561-visb-assignment/locations/us-central1/functions/ds561-python-http-server
serviceConfig:
allTrafficOnLatestRevision: true
availableCpu: '0.1666'
availableMemory: 256M
ingressSettings: ALLOW_ALL
maxInstanceCount: 83
maxInstanceRequestConcurrency: 1
revision: ds561-python-http-server-00001-cot
service: projects/ds561-visb-assignment/locations/us-central1/services/ds561-python-http-server
serviceAccountEmail: 776935284294-compute@developer.gserviceaccount.com
timeoutSeconds: 60
uri: https://ds561-python-http-server-gbzbgqktlq-uc.a.run.app
state: ACTIVE
updateTime: '2023-10-10T22:42:28.557170555Z'
url: https://us-central1-ds561-visb-assignment.cloudfunctions.net/ds561-python-http-server
