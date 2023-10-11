import os
import json
from google.cloud import pubsub_v1
from concurrent.futures import TimeoutError
import time

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/vishwasb/personal/masters/Fall2023/DS561/Assignments/DS561-vishwas-assignments/googleCredentials/ds561-visb-assignment-292b3b8eb57e.json"

PUB_SUB_TOPIC = "ds561-assignment3"
PUB_SUB_PROJECT = "ds561-visb-assignment"
PUB_SUB_SUBSCRIPTION = "ds561-assignment3-sub"

consumerTimeout = 3.0

def payloadProcessor(message):
    print(f"Received the message from pub : {message.data}.")
    message.ack()  

def consumer(project, subscription, callback, period):
        subscriber = pubsub_v1.SubscriberClient()
        subscription_path = subscriber.subscription_path(project, subscription)
        print(f"Listening for messages on {subscription_path}..\n")
        streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
        with subscriber:
            try:
                streaming_pull_future.result(timeout=period)
            except TimeoutError:
                streaming_pull_future.cancel()


while (True):
     print("-----------")
     consumer(PUB_SUB_PROJECT, PUB_SUB_SUBSCRIPTION, payloadProcessor, consumerTimeout)
     time.sleep(3)