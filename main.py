import pytchat
import threading
from flask import Flask, render_template, jsonify
import logging

log = logging.getLogger('werkzeug') # make flask shut up
log.setLevel(logging.ERROR)

app = Flask(__name__)

print("enter your video id:")
VIDEO_ID = input()

chat_history = []
seen_message_ids = set()

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
                if check_if_command(c.message) == True:
                    check_what_command(c.message)
                
                if len(chat_history) > 500:
                    old_msg = chat_history.pop(0)
                    seen_message_ids.discard(old_msg['id'])

def check_if_command(message):
    return message.startswith("!")

def check_what_command(message):
    command = message.split()[0]
    match command:
        case "!help":
            print("Hallo moto")
        case _:
            print("Unknown command!")

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
    app.run(debug=True, use_reloader=False)