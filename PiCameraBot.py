#!/usr/bin/python3

import json
import urllib.request
import requests
import picamera
import io
import os
import time

KEY_FILE = "api_key.txt"

BASE_URL = "https://api.telegram.org/bot"
API_KEY = ""

UPDATE_METHOD = "getUpdates"
UPDATE_PARAMS = {"timeout" : 120}

SEND_PHOTO_METHOD = "sendPhoto"
SEND_MESSAGE_METHOD = "sendMessage"

LAST_UPDATE_ID = 0

PHOTO_INDEX = 0
MAX_CAPTURE_TRIES = 5
MAX_SEND_PHOTO_TRIES = 5

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
            if not "text" in message["message"]:
                yield message
            else:
                if message["message"]["text"].startswith("/photo"):
                    yield message

def send_photo(chat_id, filename):
    global MAX_SEND_PHOTO_TRIES
    tries = 0
    error_msg = ""
    while tries < MAX_SEND_PHOTO_TRIES:
        with open(filename, "rb") as photo:
            post_data = {"photo": photo}
            url = build_url(SEND_PHOTO_METHOD, {"chat_id": str(chat_id)})
            response = requests.post(url, files=post_data)
            response_object = json.loads(response.content.decode("utf-8"))
            print(response_object)
            if response_object["ok"]:
                return
            else:
                print("sending failed, try: " + str(tries))
                error_msg = response_object["description"]
        tries = tries + 1
    error = IOError()
    error.msg = error_msg
    raise error

def send_message(chat_id, message):
    url = build_url(SEND_MESSAGE_METHOD, {"chat_id": str(chat_id), "text": message})
    response = requests.post(url)
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

def take_photo():
    global PHOTO_INDEX
    global MAX_CAPTURE_TRIES
    photo_file_name = "temp" + str(PHOTO_INDEX) + ".jpeg"
    tries = 0
    while not os.path.exists(photo_file_name):
        if(tries == MAX_CAPTURE_TRIES):
            error = IOError()
            error.msg = "could not capture photo"
            raise error
        tries = tries + 1
        with picamera.PiCamera() as camera:
            camera.start_preview()
            time.sleep(2)
            camera.capture(photo_file_name, format="jpeg")
            time.sleep(1)
    return photo_file_name

if __name__ == "__main__":
    global PHOTO_INDEX
    load_api_key();
    max_tries = 5
    index = 0
    for message in filtered_updates():
        print(message)
        try:
            photo_file_name = take_photo()
            try:
                send_photo(message["message"]["chat"]["id"], photo_file_name)
                os.remove(photo_file_name)
                PHOTO_INDEX = PHOTO_INDEX + 1
            except IOError as e:
                        send_message(message["message"]["chat"]["id"], "could not send photo, please try again later, error: " + e.msg)
        except IOError as e:
            send_message(message["message"]["chat"]["id"], "could not capture photo, please try again later")
