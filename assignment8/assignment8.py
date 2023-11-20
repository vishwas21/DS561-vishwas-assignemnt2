import os
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./googleCredentials.json"

from flask import Flask, make_response, render_template, request
from dotenv import load_dotenv
from datetime import datetime, timezone

from google.cloud import storage as storage
from google.cloud import pubsub_v1
from google.cloud import secretmanager

import sqlalchemy as sa
import google.cloud.logging
import os
import json
import ssl

load_dotenv("./.env")

# def create_app(test_config=None):
#     # create and configure the app
app = Flask(__name__)

pool = ""

def getSecretFromSecretManager(secret_id, version_id):
    secretClient = secretmanager.SecretManagerServiceClient()
    name = f"projects/776935284294/secrets/{secret_id}/versions/{version_id}"
    response = secretClient.access_secret_version(name=name)
    return response.payload.data.decode('UTF-8')

def createFileFromSM(fileName, secret_id, version_id):
    f = open (fileName, "w")
    f.write(getSecretFromSecretManager(secret_id, version_id))
    f.close()

# a simple page that says hello
@app.route('/<fileName>', methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS", "PUT"])
def getFileFromGcp(fileName):

    # Check if the request is from a prohbitted country, if yes then send a 404 response and add a message to the publisher with the details
    if(request.headers.get("X-country") in ["North Korea", "Iran", "Cuba", "Myanmar", "Iraq", "Libya", "Sudan", "Zimbabwe", "Syria"]):
        # Push the message to a Pub/Sub Model topic
        pubClient = connectToGooglePubSub()
        payload = {"country" : str(request.headers.get("X-country")),
                    "request": str(request.method),
                    "args": str(request.args),
                    "data": str(request.data),
                    "message": "Request from an unauthorized country"}
        pushMessagePubSub(pubClient, payload)
        return ("Permission Denied - Unauthorized Country", 400)
    
    loggingClient = connectToCloudLogging()
    import logging

    currentLog = {
        "httpRequest":{
            "requestMethod": request.method
        },
        "severity": "",
        "message": "",
        "statusCode": 000
    }

    if request.method == "GET":

        # Connect to google storage if not already connected
        storageClient = connectToGoogle()
        storageBucket, filesInBucket = connectToStorageBucketAndRead(storageClient, "cs561-assignment2-storage-bucket")
        fileName = "files/" + request.path.split("/")[-1]

        # Get the file name and check if the file is present in the bucket
        if(not checkFileIfExists(filesInBucket, fileName)):
            currentLog["severity"] = "ERROR"
            currentLog["message"] = "User tried to search for non existant file: " + fileName
            currentLog["statusCode"] = 404
            print(currentLog)
            logging.warning(currentLog)
            return ("File Not Found", 404)

        # If present, retreive the file, read it and return the contents of the file with a 200 code
        currentLog["severity"] = "SUCCESS"
        currentLog["message"] = "File Found and returned Successfully"
        currentLog["statusCode"] = 200
        logging.info(currentLog)
        response = make_response(readFileFromStorage(storageBucket, fileName), 200)
        response.headers['X-response-vm-zone'] = os.environ['VMZONE']
        return response
    else:
        currentLog["severity"] = "INTERNAL SERVER ERROR"
        currentLog["message"] = "Not Implemented method call : " + request.method
        currentLog["statusCode"] = 501
        logging.warning(currentLog)
        return ("Not Implemented yet", 501)
    
def connectToGoogle():
    storageClient = storage.Client.create_anonymous_client()
    return storageClient

def connectToStorageBucketAndRead(storageClient, storageBucketName):
    storageBucket = storageClient.bucket(storageBucketName)
    filesInBucket = [blob.name for blob in storageBucket.list_blobs()]

    return storageBucket, filesInBucket

def checkFileIfExists(filesInBucket, fileName):
    if(fileName in filesInBucket):
        return True
    return False

def readFileFromStorage(storageBucket, blobName):
    blob = storageBucket.blob(blobName)
    fileContent = ""

    with blob.open("r") as f:
        fileContent = f.read()
    
    return fileContent

def connectToCloudLogging():
    loggingClient = google.cloud.logging.Client()
    loggingClient.setup_logging()
    return loggingClient

def connectToGooglePubSub():
    pubClient = pubsub_v1.PublisherClient() 
    return pubClient
    
def pushMessagePubSub(pubClient, payload):
    PUB_SUB_TOPIC = "ds561-assignment3"
    PUB_SUB_PROJECT = "ds561-visb-assignment"

    topicPath = pubClient.topic_path(PUB_SUB_PROJECT, PUB_SUB_TOPIC)        
    jsonData = json.dumps(payload).encode("utf-8")           
    future = pubClient.publish(topicPath, data=jsonData) 
    return

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
