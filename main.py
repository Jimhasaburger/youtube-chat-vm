import pytchat
import threading
from flask import Flask, render_template, jsonify

app = Flask(__name__)

VIDEO_ID = "u7kIh97FaJs"
chat_history = []

def fetch_chat():
    global chat_history
    chat = pytchat.create(video_id=VIDEO_ID)
    
    if chat.is_replay():
        print("UPDATE THE VIDEO ID")
        return

    while chat.is_alive():
        for c in chat.get().sync_items():
            msg_data = {
                "user": c.author.name,
                "text": c.message,
                "pfp_url": c.author.imageUrl,
                "is_owner": c.author.isChatOwner,
                "is_moderator": c.author.isChatModerator,
                "platform": "youtube",
                "timestamp": c.datetime
            }
            chat_history.append(msg_data)
            if len(chat_history) > 100:
                chat_history.pop(0)
            
            print(f"{c.datetime} {c.author.name}: {c.message}")

@app.route("/")
def index():
    return render_template("chat.html")

@app.route("/chatjson")
def chatjson():
    return jsonify({
        "messages": chat_history,
        "show_pfp": True,
        "show_platform_icon": False,
        "status": "Connected"
    })

if __name__ == "__main__":

    thread = threading.Thread(target=fetch_chat, daemon=True)
    thread.start()

    app.run(debug=True, use_reloader=False)