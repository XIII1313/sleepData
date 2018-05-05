# --------
# imports
# --------
from flask import Flask, request
import requests
import sys
import os
import json
from Credentials import *
import time
import datetime
import urllib.request
app = Flask(__name__)
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# ------------
# global vars
# ------------
utc_plus = 2

quick_replies_list = [
         {
        "content_type": "text",
        "title": "add",
        "payload": "add",
         }
]


# --------------------
# Google Spreadsheets
# --------------------
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)
sleep_sheet = client.open("sleep").sheet1


def refresh_credentials():
	global scope, creds, client
    global sleep_sheet
    print("Refreshing credentials ...")
    scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)
    sleep_sheet = client.open("sleep").sheet1
    print("Refreshed credentials.")


# ------------------------
# Google Spreadsheet defs
# ------------------------
def nb_rows(sheet):
    nb_rows = len(sheet.get_all_records()) + 1
    return nb_rows


def upload_sleep_data(sheet, date, time_now, comment):
    row_index = nb_rows(sheet) + 1
    sheet.update_cell(row_index, 1, date)
    sheet.update_cell(row_index, 2, time_now)
    sheet.update_cell(row_index, 3, comment)
    print("uploaded values")


# -----------
# Extra Defs
# -----------
def slice_words(string, begin_index, end_index):
    string_list = string.split()
    string_list = string_list[begin_index:end_index]
    new_string = ""

    for word in string_list:
        new_string += word
        new_string += " "

    new_string = new_string[0: len(new_string) - 1]
    return new_string


def get_current_date():
    now = datetime.datetime.utcnow()
    date = "{}/{}/{}".format(now.day, now.month, now.year)
    return date


def get_current_time():
    now = datetime.datetime.utcnow()
    hour = str(now.hour + utc_plus)
    minute = str(now.minute)

    if len(minute) == 1:
        minute = "0" + minute

    if len(hour) == 1:
        hour = "0" + hour
    time_now = "{}:{}".format(hour, minute)

    return time_now


# -----
# main
# -----
def main_def(comment):
    date = get_current_date()
    time_now = get_current_time()
    refresh_credentials()
    upload_sleep_data(sleep_sheet, date, time_now, comment)




@app.route('/', methods=['GET'])
def handle_verification():
    if request.args.get('hub.verify_token', '') == VERIFY_TOKEN:
        return request.args.get('hub.challenge', 200)
    else:
        return 'Error, wrong validation token'


@app.route('/', methods=['POST'])
def handle_messages():
    global userList
    data = request.get_json()
    log(data)

    if data["object"] == "page":

        for entry in data["entry"]:
         
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):
                    sender_id = messaging_event["sender"]["id"]
                    recipient_id = messaging_event["recipient"]["id"]
                  
                    try:
                        message_text = messaging_event["message"]["text"]
                    except KeyError:
                        message_text = 'image'
                  
                    first_word = slice_words(message_text, 0, 1)
                    comment = slice_words(message_text, 1, len(message_text.split()))
                    
                           
                    if first_word.lower() == "add":
                        if comment == "":
                        	try:
                           		main_def("None")
								botReply = "Updated the data with comment None."
								send_message(sender_id, botReply)
							except:
								botReply = "An error has occurred."
								send_message(sender_id, botReply)
								
                        else:
                           	try:
                           		main_def(comment)
								botReply = "Updated the data with comment None."
                        		send_message(sender_id, botReply)
							except:
								botReply = "An error has occurred."
								send_message(sender_id, botReply)

                    else:
                        botReply = "Sorry, I do not understand this message."
                        send_message(sender_id, botReply)
              

                if messaging_event.get("delivery"):
                    pass

                if messaging_event.get("optin"):
                    pass

                if messaging_event.get("postback"):
                    pass

	return "ok", 200


def send_message(recipient_id, message_text):
    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": PAGE_ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text,
            "quick_replies": quick_replies_list
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
    log(r.text)


def log(message):  # simple wrapper for logging to stdout on heroku
    print(str(message))
    sys.stdout.flush()

   
            
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
