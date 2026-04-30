import pytchat
import threading
from flask import Flask, render_template, jsonify

app = Flask(__name__)

VIDEO_ID = "u7kIh97FaJs"
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
                
                if len(chat_history) > 500:
                    old_msg = chat_history.pop(0)
                    seen_message_ids.discard(old_msg['id'])

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