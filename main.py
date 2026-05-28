import pytchat
import threading
from flask import Flask, render_template, jsonify
import logging
import uuid
import virtualbox
import time
import json

# edit this config file!!!!
with open('config.json', 'r') as g:
    CONFIG = json.load(g)

VIDEO_ID = CONFIG.get('videoid')
VM_NAME = CONFIG.get('vmname')

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
        case "!type":
            if args:
                text_to_type = " ".join(args)
                for char in text_to_type:
                    is_upper = char.isupper()
                    scancode = get_key_scancode(char.lower())
                    if scancode:
                        press_key(scancode, shift=is_upper)
            else:
                add_sys_message("Usage: !type <text>")

        case "!send":
            if args:
                text_to_type = " ".join(args)
                for char in text_to_type:
                    is_upper = char.isupper()
                    scancode = get_key_scancode(char.lower())
                    if scancode:
                        press_key(scancode, shift=is_upper)
                
                # Press Enter after typing
                enter_code = get_key_scancode("enter")
                if enter_code:
                    press_key(enter_code)
            else:
                add_sys_message("Usage: !send <text>")
        
        case "!move":
            if len(args) == 2:
                try:
                    x = int(args[0])
                    y = int(args[1])
                    move_mouse(x, y)
                except ValueError:
                    add_sys_message("Error: X and Y must be numbers.")
            else:
                add_sys_message("Usage: !move <x> <y>")
        
        case "!scroll":
            if len(args) == 1:
                try:
                    num = int(args[0])
                    scroll_mouse(num)
                except ValueError:
                    add_sys_message("Error: Must be a number.")
            else:
                add_sys_message("Usage: !scroll <num>")

        case "!click":
            click_mouse(1)
        case "!rclick":
            click_mouse(2)
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

def press_key(scancode_input, shift=False):
    if not scancode_input:
        return
    scancodes = scancode_input if isinstance(scancode_input, list) else [scancode_input]
    final_make_codes = [0x2A] + scancodes if shift else scancodes
    session.console.keyboard.put_scancodes(final_make_codes)
    time.sleep(0.05)
    break_codes = []
    for code in reversed(scancodes):
        break_codes.append(code + 0x80)
    if shift:
        break_codes.append(0xAA)
    session.console.keyboard.put_scancodes(break_codes)      
    session.console.keyboard.put_scancodes(break_codes)
    print(f"Sent scancodes: {scancode_list} and {break_codes}")

def move_mouse(x, y):
    # ignore this this is just so i know how to use mouse
    # Move the mouse relatively and simulate button clicks
    # dx: delta X (pixels right)
    # dy: delta Y (pixels down)
    # dz: delta Z (scroll wheel, positive = up, negative = down)
    # dw: idfk what this does
    # button_state: 0 (none), 1 (left click), 2 (right click), etc.
    # session.console.mouse.put_mouse_event(dx=50, dy=50, dz=0, button_state=0)
    session.console.mouse.put_mouse_event(dx=x, dy=y, dz=0, dw=0,button_state=0)

def click_mouse(type):
    # button_state: 0 (none), 1 (left click), 2 (right click), etc.
    session.console.mouse.put_mouse_event(dx=0, dy=0, dz=0, dw=0,button_state=type)
    session.console.mouse.put_mouse_event(dx=0, dy=0, dz=0, dw=0,button_state=0) # unclick

def scroll_mouse(num):
    # dz: delta Z (scroll wheel, positive = up, negative = down)
    session.console.mouse.put_mouse_event(dx=0, dy=0, dz=num, dw=0,button_state=0)

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