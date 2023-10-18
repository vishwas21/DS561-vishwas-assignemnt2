import os
import flask 

from flask import Flask, request
from dotenv import load_dotenv

from google.cloud import storage as storage
from google.cloud import pubsub_v1

import google.cloud.logging
import os
import flask
import json



load_dotenv("./.env")


# def create_app(test_config=None):
#     # create and configure the app
app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(
    SECRET_KEY='dev',
    DATABASE=os.path.join(app.instance_path, 'assignment4.sqlite'),
)

# ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

# a simple page that says hello
@app.route('/<fileName>', methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS", "PUT"])
def getFileFromGcp(fileName):

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./googleCredentials.json"

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
        return(readFileFromStorage(storageBucket, fileName), 200)
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
    print("Pushed message to topic.")   
    return

# return app

if __name__ == "__main__":
    app.run("0.0.0.0", "8080")
