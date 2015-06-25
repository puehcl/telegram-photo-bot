#!/usr/bin/python3

import json
import urllib.request
import requests
import picamera
import io
import os

KEY_FILE = "api_key.txt"

BASE_URL = "https://api.telegram.org/bot"
API_KEY = ""

UPDATE_METHOD = "getUpdates"
UPDATE_PARAMS = {"timeout" : 120}

SEND_PHOTO_METHOD = "sendPhoto"

LAST_UPDATE_ID = 0

def updates():
    while True:
        url = build_url(UPDATE_METHOD, UPDATE_PARAMS)
        print("sending request to: " + url)
        httpresponse = urllib.request.urlopen(url, timeout=150)
        response_object = json.loads(httpresponse.read().decode("utf-8"))
        if not response_object["ok"]:
            yield []
        else:
            messages = sorted(response_object["result"], key=(lambda x: x["update_id"]))
            if(len(messages) == 0):
                yield messages
            else:
                LAST_UPDATE_ID = messages[-1]["update_id"]
                UPDATE_PARAMS["offset"] = LAST_UPDATE_ID + 1
                yield messages

def filtered_updates():
    for messages in updates():
        for message in messages:
            print(message)
            if not "text" in message["message"]:
                yield message
            else:
                if message["message"]["text"].startswith("/photo"):
                    yield message

def send_photo(chat_id, filename):
    post_data = {"photo": open(filename, "rb")}
    url = build_url(SEND_PHOTO_METHOD, {"chat_id": str(chat_id)})
    response = requests.post(url, files=post_data)
    print(response)
    print(response.content)

def build_url(method, params):
    url = BASE_URL + API_KEY + "/" + method + "?"
    for key in params:
        url = url + key + "=" + str(params[key]) + "&"
    return url

def load_api_key():
    global API_KEY
    with open(KEY_FILE, "r") as kf:
        API_KEY = kf.readline()[:-1]

if __name__ == "__main__":
    load_api_key();
    for message in filtered_updates():
        print(message)
        with picamera.PiCamera() as camera:
            camera.capture("temp.jpeg", format="jpeg")
            send_photo(message["message"]["chat"]["id"], "temp.jpeg")
            os.remove("temp.jpeg")
