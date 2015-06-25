#!/usr/bin/python3

import json
import urllib.request
import picamera
import io

KEY_FILE = "api_key.txt"

BASE_URL = "https://api.telegram.org/bot"
API_KEY = ""

UPDATE_METHOD = "getUpdates"
UPDATE_PARAMS = {"timeout" : 120}

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
            if message["message"]["text"].startswith("/photo "):
                yield message

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
            in_mem_photo = io.BufferedWriter()
            camera.capture(in_mem_photo)
