#!/usr/bin/python3

import json
import urllib.request
import requests
import picamera
import io
import os
import time

KEY_FILE = "api_key.txt"

TELEGRAM_URL = "https://api.telegram.org/bot"
API_KEY = ""
BASE_URL = ""

UPDATE_METHOD = "getUpdates"
UPDATE_PARAMS = {"timeout" : 120}

SEND_PHOTO_METHOD = "sendPhoto"
SEND_MESSAGE_METHOD = "sendMessage"

LAST_UPDATE_ID = 0

PHOTO_INDEX = 0
MAX_SEND_PHOTO_TRIES = 5

class JsonObject(object):

    def __init__(self, json_data):
        self.__dict__ = dict()
        for key in json_data:
            value = json_data[key]
            if isinstance(value, dict):
                value = JsonObject(value)
            if isinstance(value, list):
                values = []
                for item in value:
                    values.append(JsonObject(item))
                value = values
            self.__dict__[key] = value

    def __str__(self):
        result = "JsonObject{"
        for key in self.__dict__:
            result = result + str(key) + ":" + str(self.__dict__[key]) + ", "
        result = result[:-2] + "}"
        return result


def updates():
    global BASE_URL
    global UPDATE_METHOD
    global UPDATE_PARAMS
    while True:
        url = BASE_URL + UPDATE_METHOD
        print("sending request to: " + url)
        try:
            response = requests.get(url, params=UPDATE_PARAMS, timeout=150)
        except requests.exceptions.RequestException:
            time.sleep(10)
            continue
        response_object = JsonObject(json.loads(response.text))
        if not response_object.ok:
            yield []
        else:
            updates = sorted(response_object.result, key=(lambda x: x.update_id))
            if(len(updates) == 0):
                yield []
            else:
                LAST_UPDATE_ID = updates[-1].update_id
                UPDATE_PARAMS["offset"] = LAST_UPDATE_ID + 1
                yield updates

def messages():
    for update_list in updates():
        for update in update_list:
            message = update.message
            if not message.text:
                yield message
            else:
                if message.text.startswith("/photo"):
                    yield message

def send_photo(chat_id, filename):
    global MAX_SEND_PHOTO_TRIES
    global BASE_URL
    global SEND_PHOTO_METHOD
    tries = 0
    error_msg = ""
    url = BASE_URL + SEND_PHOTO_METHOD
    while tries < MAX_SEND_PHOTO_TRIES:
        with open(filename, "rb") as photo:
            post_data = {"photo": photo}
            params = {"chat_id": str(chat_id)}
            response = requests.post(url, params, files=post_data)
            response_object = JsonObject(json.loads(response.text))
            print(response_object)
            if response_object.ok:
                return
            else:
                print("sending failed, try: " + str(tries))
                error_msg = response_object.description
        tries = tries + 1
    raise IOError(error_msg)

def send_message(chat_id, message):
    global BASE_URL
    global SEND_MESSAGE_METHOD
    url = BASE_URL + SEND_MESSAGE_METHOD
    response = requests.post(url, {"chat_id": str(chat_id), "text": message})
    print(response.text)

def take_photo():
    global PHOTO_INDEX
    global MAX_CAPTURE_TRIES
    photo_file_name = "temp" + str(PHOTO_INDEX) + ".jpeg"
    with picamera.PiCamera() as camera:
        camera.resolution = (2560, 1920)
        camera.shutter_speed = 2000
        camera.start_preview()
        time.sleep(2)
        camera.capture(photo_file_name, format="jpeg")
    return photo_file_name

def load_api_key():
    global API_KEY
    with open(KEY_FILE, "r") as kf:
        API_KEY = kf.readline()[:-1]

def initialize():
    global API_KEY
    global BASE_URL
    global TELEGRAM_URL
    load_api_key();
    BASE_URL = TELEGRAM_URL + API_KEY + "/"

if __name__ == "__main__":
    global PHOTO_INDEX
    initialize();
    for message in messages():
        print(message)
        photo_file_name = take_photo()
        try:
            send_photo(message.chat.id, photo_file_name)
            os.remove(photo_file_name)
            PHOTO_INDEX = PHOTO_INDEX + 1
        except IOError as e:
            send_message(message.chat.id, "could not send photo, please try again later, error: " + str(e))
