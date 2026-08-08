import pytchat
import threading
from flask import Flask, render_template, jsonify
import logging
import uuid
import virtualbox
import time
import json
import subprocess
import os

# edit this config file!!!!
with open('config.json', 'r') as g:
    CONFIG = json.load(g)

VIDEO_ID = CONFIG.get('videoid')
VM_NAME = CONFIG.get('vmname')
VBOXMANAGE = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"

vbox_manager = virtualbox.Manager() # vbox stuff
vbox = vbox_manager.get_virtualbox()
machine = vbox.find_machine(VM_NAME)
session = virtualbox.Session()


def initialize_vm_session():
    global session
    try:
        if str(machine.state) in ("PoweredOff", "Aborted"):
            print(f"VM '{VM_NAME}' is powered off. Launching...")
            progress = machine.launch_vm_process(session, "gui", [])
            progress.wait_for_completion(-1)
            print("VM launched and session locked.")
        else:
            machine.lock_machine(session, virtualbox.library.LockType.shared)
            print("Connected to running VM session.")
    except Exception as e:
        print(f"Initialization error: {e}")

initialize_vm_session()

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
    idxs = []
    
    for i,v in enumerate(parts):
        if check_if_command(v): idxs.append(i)
    print(idxs)
    
    for i, v in enumerate(idxs):
        print (i, v)
        newparts = []
        if i == len(idxs)-1:
            newparts = parts[v:len(parts)]
        else:
            newparts = parts[v:idxs[i+1]]
        print(newparts)
        process_command_array(newparts)

def process_command_array(parts):
    # parts = message.strip().split()
    
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
        case "!repeat":
            if len(args) == 3: 
                try:
                    key = int(args[1])
                    times = int(args[2])
                    for _ in range(times):
                        press_key(get_key_scancode(key))
                except Exception as e:
                    print(f"Fehler beim Ausführen: {e}")
                    add_sys_message("ERROR")
            else:
                add_sys_message("Usage: !repeat [key] [times]")

        case "!combo":
            if args:
                key_names = args
                scancodes = [code for key_name in key_names
                   for code in (get_key_scancode(key_name) or [])]
                if scancodes:
                    press_key(scancodes)
                else:
                    add_sys_message("Unknown key in combo.")
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
        case "!mclick":
            click_mouse(4)
        case "!revert":
            revert_vm()
        case "!restart":
            restart_vm()
        case "!start":
            if str(machine.state) in ("PoweredOff", "Aborted", "Saved"):
                add_sys_message("Starting VM...")
                start_vm()
                add_sys_message("Started!")
            else:
                add_sys_message("VM is already running.")
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
# ai made this part idk how to do key stuff.

def split_into_keys(scancode_list):
    """Split a flat scancode list back into individual key sequences."""
    keys = []
    i = 0
    while i < len(scancode_list):
        if scancode_list[i] == 224 and i + 1 < len(scancode_list):  # extended key (0xE0)
            keys.append([224, scancode_list[i + 1]])
            i += 2
        else:
            keys.append([scancode_list[i]])
            i += 1
    return keys

def generate_break_code(key_sequence):
    """Generate break codes for a single key sequence."""
    if len(key_sequence) == 2 and key_sequence[0] == 224:  # extended key
        return [224, key_sequence[1] + 128]
    return [key_sequence[0] + 128]

def press_key(scancode_input, shift=False):
    if not scancode_input:
        return

    scancode_list = scancode_input if isinstance(scancode_input, list) else [scancode_input]

    if shift:
        session.console.keyboard.put_scancodes([42])   # shift make

    # Send all make codes
    session.console.keyboard.put_scancodes(scancode_list)
    time.sleep(0.05)

    # Split into individual keys, release in reverse order
    keys = split_into_keys(scancode_list)
    for key in reversed(keys):
        session.console.keyboard.put_scancodes(generate_break_code(key))

    if shift:
        session.console.keyboard.put_scancodes([170])  # shift break (42 + 128)
#ai ends here
def move_mouse(x, y):
    # ignore this this is just so i know how to use mouse
    # Move the mouse relatively and simulate button clicks
    # dx: delta X (pixels right)
    # dy: delta Y (pixels down)
    # dz: delta Z (scroll wheel, positive = up, negative = down)
    # dw: idfk what this does
    # button_state: 0 (none), 1 (left click), 2 (right click), 4 middle click
    # session.console.mouse.put_mouse_event(dx=50, dy=50, dz=0, button_state=0)
    session.console.mouse.put_mouse_event(dx=x, dy=y, dz=0, dw=0,button_state=0)

def click_mouse(type):
    # button_state: 0 (none), 1 (left click), 2 (right click), 4 mclick
    session.console.mouse.put_mouse_event(dx=0, dy=0, dz=0, dw=0,button_state=type)
    session.console.mouse.put_mouse_event(dx=0, dy=0, dz=0, dw=0,button_state=0) # unclick

def scroll_mouse(num):
    # dz: delta Z (scroll wheel, positive = up, negative = down)
    session.console.mouse.put_mouse_event(dx=0, dy=0, dz=num, dw=0,button_state=0)

def revert_vm():
    try:
        add_sys_message("Reverting VM...")
        
        session.unlock_machine()
        
        result = subprocess.run(
            [VBOXMANAGE, "controlvm", VM_NAME, "poweroff"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Poweroff warning (may already be off): {result.stderr.strip()}")
        
        time.sleep(2)
        
        subprocess.run(
            [VBOXMANAGE, "snapshot", VM_NAME, "restorecurrent"],
            check=True, capture_output=True
        )
        time.sleep(2)
        
        subprocess.run(
            [VBOXMANAGE, "startvm", VM_NAME, "--type", "gui"],
            check=True, capture_output=True
        )
        time.sleep(5)
        
        machine.lock_machine(session, virtualbox.library.LockType.shared)
        
        add_sys_message("VM reverted and restarted successfully.")
        
    except subprocess.CalledProcessError as e:
        print(f"VBoxManage error: {e.stderr.strip() if e.stderr else e}")
        add_sys_message("Revert failed due to VBoxManage error.")
    except Exception as e:
        print(f"Error reverting: {e}")
        add_sys_message("Revert failed.")

def wait_for_unlock(machine, timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        state = str(machine.session_state)
        if state == "Unlocked":
            return True
        time.sleep(0.3)
    return False

def start_vm():
    global session

    session = virtualbox.Session()

    if str(machine.state) in ("PoweredOff", "Aborted", "Saved"):
        last_exc = None
        for attempt in range(5):
            try:
                progress = machine.launch_vm_process(session, "gui", [])
                progress.wait_for_completion(-1)
                last_exc = None
                break
            except Exception as e:
                last_exc = e
                print(f"launch_vm_process attempt {attempt+1} failed: {e}")
                time.sleep(1)
        if last_exc:
            raise last_exc
    else:
        # already running somehow, just lock onto it
        machine.lock_machine(session, virtualbox.library.LockType.shared)

def restart_vm():
    global session

    try:
        if str(machine.state) != "PoweredOff":
            add_sys_message("Shutting down VM...")

            progress = session.console.power_down()
            progress.wait_for_completion(-1)

            add_sys_message("VM now off...")

        try:
            session.unlock_machine()
        except Exception as e:
            print(f"Session unlock: {e}")

        if not wait_for_unlock(machine):
            print("Warning: machine did not Unlock in time")

        add_sys_message("Turning on...")

        start_vm()

        add_sys_message("Turned on!")

    except Exception as e:
        print(f"Error restarting VM: {e}")
        add_sys_message("Failed")

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
