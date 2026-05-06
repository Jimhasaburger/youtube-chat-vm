import pytchat
import threading
from flask import Flask, render_template, jsonify
import logging
import uuid
import virtualbox
import time
import json

# -------------------- config ---------------
print("enter your video id:")
VIDEO_ID = input()
VM_NAME = "windXP"
# --------------------------------------------

vbox_manager = virtualbox.Manager() # vbox stuff
vbox = vbox_manager.get_virtualbox()
machine = vbox.find_machine(VM_NAME)
session = virtualbox.Session()
machine.lock_machine(session, virtualbox.library.LockType.shared)

log = logging.getLogger('werkzeug') # make flask shut up
log.setLevel(logging.ERROR)

app = Flask(__name__)

chat_history = []
seen_message_ids = set()

with open('scancodes.json', 'r') as f:
    KEY_MAP = json.load(f)

def fetch_chat():
    global chat_history
    chat = pytchat.create(video_id=VIDEO_ID, interruptable=False)
    
    while chat.is_alive():
        for c in chat.get().sync_items():
            if c.id not in seen_message_ids:
                msg_data = {
                    "id": c.id,
                    "user": c.author.name,
                    "text": c.message,
                    "pfp_url": c.author.imageUrl,
                    "is_owner": c.author.isChatOwner,
                    "is_moderator": c.author.isChatModerator,
                    "timestamp": c.datetime
                }
                chat_history.append(msg_data)
                seen_message_ids.add(c.id)
                if check_if_command(c.message) == True: # checks if command
                    check_what_command(c.message)       # checks which command
                
                if len(chat_history) > 500:             # removes old messages
                    old_msg = chat_history.pop(0)
                    seen_message_ids.discard(old_msg['id'])

def check_if_command(message):
    return message.startswith("!")

def check_what_command(message):
    parts = message.strip().split()
    
    if not parts:
        return

    command = parts[0].lower()
    args = parts[1:]

    match command:
        case "!help":
            add_sys_message("check description")
        case "!key":
            if args:
                key_name = args[0].lower()
                press_key(get_key_scancode(key_name))
            else:
                add_sys_message("Specify a key.")
        case "!combo":
            if args:
                key_names = args
                scancodes = [get_key_scancode(key_name) for key_name in key_names]
                press_key(scancodes)
            else:
                add_sys_message("Specify at least one key.")
        case _:
            add_sys_message("Unknown Command!")

def add_sys_message(message): # add system message
    global chat_history
    msg_data = {
        "id": str(uuid.uuid4()),
        "user": "System",
        "text": message,
        "pfp_url": "",
        "is_owner": False,
        "is_moderator": False
    }
    chat_history.append(msg_data)
    print("System: " + message)

def get_key_scancode(keyname):
    return KEY_MAP.get(keyname.lower(), None)

def press_key(scancode_list):
    if not scancode_list:
        return
    session.console.keyboard.put_scancodes(scancode_list)
    time.sleep(0.05)
    break_codes = []
    for code in scancode_list:
        if code == 0xE0:
            break_codes.append(code)
        else:
            break_codes.append(code + 0x80)
            
    session.console.keyboard.put_scancodes(break_codes)
    print(f"Sent scancodes: {scancode_list} and {break_codes}")

@app.route("/")
def index():
    return render_template("chat.html")

@app.route("/chatjson")
def chatjson():
    return jsonify({
        "messages": chat_history,
        "show_pfp": True,
        "status": "Live"
    })

if __name__ == "__main__":
    thread = threading.Thread(target=fetch_chat, daemon=True) 
    thread.start()
    app.run(debug=False, port=5000)