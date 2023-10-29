import os
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./googleCredentials.json"

from flask import Flask, request
from dotenv import load_dotenv
from datetime import datetime, timezone

from google.cloud import storage as storage
from google.cloud import pubsub_v1
from google.cloud.sql.connector import Connector
from google.cloud import secretmanager

import sqlalchemy as sa
from sqlalchemy import insert
import google.cloud.logging
import os
import json
import ssl
import time

load_dotenv("./.env")

os.environ["INSTANCE_CONNECTION_NAME"] = "ds561-visb-assignment:us-central1:ds561-psql-server"
os.environ["DB_USER"] = "postgres"
os.environ["DB_NAME"] = "ds561-db"

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

def insertRequestDetails(request):
    isBanned = "false"
    if(request.headers.get("X-country") in ["North Korea", "Iran", "Cuba", "Myanmar", "Iraq", "Libya", "Sudan", "Zimbabwe", "Syria"]):
        isBanned= "true"
    
    timeOfRequest = datetime.now(timezone.utc)
    requestedFile = "files/" + request.path.split("/")[-1]

    insertStmt = sa.text(f"""INSERT INTO request_details (country, client_ip, gender, age, income, is_banned, time_of_request, requested_file) VALUES('{request.headers.get("X-country")}', '{request.headers.get("X-client-ip")}', '{request.headers.get("X-gender")}', {request.headers.get("X-age")}, {request.headers.get("X-income")}, {isBanned}, '{timeOfRequest}', '{requestedFile}') RETURNING request_id;""")

    res = ""

    with pool.connect() as dbConn:
        res = dbConn.execute(insertStmt)
        dbConn.commit()
    
    return (res.fetchone()).request_id

def insertErrorDetails(request_id, errorCode):
    insertStmt = sa.text(f"""INSERT INTO error_details (request_id, error_code) VALUES({request_id}, {errorCode});""")

    with pool.connect() as dbConn:
        dbConn.execute(insertStmt)
        dbConn.commit()
    return

# initialize Python Connector object
def connectToDb():
    global pool

    createFileFromSM("server-ca.pem", "dbserverca", "2")
    createFileFromSM("client-cert.pem", "dbclientcert", "1")
    createFileFromSM("client-key.pem", "dbclientkey", "1")

    db_root_cert = "./server-ca.pem"  # e.g. '/path/to/my/server-ca.pem'
    db_cert = "./client-cert.pem"  # e.g. '/path/to/my/client-cert.pem'
    db_key = "./client-key.pem"  # e.g. '/path/to/my/client-key.pem'

    connect_args = {}

    ssl_context = ssl.SSLContext()
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    ssl_context.load_verify_locations(db_root_cert)
    ssl_context.load_cert_chain(db_cert, db_key)
    connect_args["ssl_context"] = ssl_context

    pool = sa.create_engine(
        sa.engine.url.URL.create(
            drivername="postgresql+pg8000",
            username="postgres",
            password=getSecretFromSecretManager("dbpostgrespwd", "1"),
            host="34.42.5.93",
            port="5432",
            database="ds561-db",
        ),
        connect_args=connect_args,
    )

connectToDb()

# a simple page that says hello
@app.route('/<fileName>', methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS", "PUT"])
def getFileFromGcp(fileName):

    print(fileName)
    request_id = insertRequestDetails(request)

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
        insertErrorDetails(request_id, 400)
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
            insertErrorDetails(request_id, 404)
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
        insertErrorDetails(request_id, 501)
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

if __name__ == "__main__":
    app.run("0.0.0.0", "8080")
