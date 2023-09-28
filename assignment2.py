from google.cloud import storage as storage
from bs4 import BeautifulSoup

import os
import re
import json
import numpy as np

global pageGraph
global pageRank
global sumPageRank


def readStorageBucket(googleClient, storageBucketName):
    storageBucket = googleClient.bucket(storageBucketName)
    filesInBucket = [blob.name for blob in storageBucket.list_blobs()]

    return storageBucket, filesInBucket

def parseFileHTML(fileName, fileContent):
    soup = BeautifulSoup(fileContent, 'html.parser')
    listOfAnchorTags = soup.find_all('a')

    if fileName not in pageGraph.keys():
        pageGraph[fileName] = {
            'incomingLinks': 0,
            'outgoingLinks': 0,
            'links': []
        }
    
    for anchorTag in listOfAnchorTags:
        hrefLink = anchorTag.get('href')

        if hrefLink not in pageGraph[fileName]['links']:
            pageGraph[fileName]['links'].append(hrefLink)
            pageGraph[fileName]['outgoingLinks'] = pageGraph[fileName]['outgoingLinks'] + 1

        if hrefLink not in pageGraph.keys():
            pageGraph[hrefLink] = {
                'incomingLinks': 0,
                'outgoingLinks': 0,
                'links': []
            }
        
        pageGraph[hrefLink]['incomingLinks'] = pageGraph[hrefLink]['incomingLinks'] + 1

def saveToFile():
    openFile = open("data.json", "w")
    json.dump(pageGraph, openFile)

def readFromJson():
    openFile = open("data.json")
    global pageGraph
    pageGraph = json.load(openFile)

def calculateStatistics():
    incomingLinks = []
    outgoingLinks = []

    for page in pageGraph.keys():
        incomingLinks.append(pageGraph[page]["incomingLinks"])
        outgoingLinks.append(pageGraph[page]["outgoingLinks"])
    
    incomingMean = np.mean(incomingLinks)
    outgoingMean = np.mean(outgoingLinks)

    incomingMedian = np.median(incomingLinks)
    outgoingMedian = np.median(outgoingLinks)

    incomingMin = min(incomingLinks)
    incomingMax = max(incomingLinks)

    outgoingMin = min(outgoingLinks)
    outgoingMax = max(outgoingLinks)

    incomingQuintiles = np.percentile(incomingLinks, [20, 40, 60, 80])
    outgoingQuintiles = np.percentile(outgoingLinks, [20, 40, 60, 80])

    # Print the results
    print("Incoming Links:")
    print(f"Mean: {incomingMean}")
    print(f"Median: {incomingMedian}")
    print(f"Max: {incomingMax}")
    print(f"Min: {incomingMin}")
    print(f"Quintiles: {incomingQuintiles}")

    print("\nOutgoing Links:")
    print(f"Mean: {outgoingMean}")
    print(f"Median: {outgoingMedian}")
    print(f"Max: {outgoingMax}")
    print(f"Min: {outgoingMin}")
    print(f"Quintiles: {outgoingQuintiles}")

def operationsForMetrics(storageBucket, filesInBucket):
    index = 1
    for file in filesInBucket:
        try:
            fileName = (re.findall("\/([a-zA-Z0-9]*.{1}.html)", file))[0]
            blob = storageBucket.blob(file)
            content = blob.download_as_text()
            parseFileHTML(fileName, content)
            index = index + 1
        except:
            continue
    
    saveToFile()
    readFromJson()

    calculateStatistics()

    while(True):
        calculatePageRank()
        if not checkPageRankUpdate():
            break
    
    global pageRank
    
    pageRank = sorted(pageRank.items(), key=lambda x:x[1], reverse=True)

    print("Top 5 files: ")
    for index in range(0,5):
        print("File: ", pageRank[index])

def calculatePRX(fileName):
    defaultPageRankValue = 0.15
    sum = 0.0

    for connectedFile in pageGraph[fileName]["links"]:
        if connectedFile not in pageRank.keys():
            pageRank[connectedFile] = defaultPageRankValue     
        if(pageGraph[connectedFile]["outgoingLinks"] == 0):
            continue
        sum += pageRank[connectedFile] / (pageGraph[connectedFile]["outgoingLinks"] * 1.0)
    return sum

def calculatePageRank():
    global pageRank
    newPageRank = dict()
    for fileName in pageGraph.keys():
        prValue = 0.15 + (0.85 * calculatePRX(fileName))
        newPageRank[fileName] = prValue
    
    pageRank = newPageRank

def checkPageRankUpdate():
    global sumPageRank

    currentSum = 0.0
    for pr in pageRank.keys():
        currentSum += pageRank[pr]

    diff = ((abs(currentSum - sumPageRank)) / sumPageRank) 

    if diff > 0.005:
        sumPageRank = currentSum
        return True
    return False

def main():
    global pageGraph
    global pageRank
    global sumPageRank


    sumPageRank = (0.15 * 10000)
    pageRank = dict()
    pageGraph = dict()
    googleClient = storage.Client.create_anonymous_client()
    # Upload the generated files to the bucket
    # for root, _, files in os.walk("files"):
    #     for file in files:
    #         local_path = os.path.join(root, file)
    #         bucket = googleClient.bucket("cs561-assignment2-storage-bucket")
    #         blob = bucket.blob(os.path.join("files", file))
    #         blob.upload_from_filename(local_path)
    storageBucket, filesInBucket = readStorageBucket(googleClient, "cs561-assignment2-storage-bucket")
    operationsForMetrics(storageBucket, filesInBucket)

if __name__ == "__main__":
    main()