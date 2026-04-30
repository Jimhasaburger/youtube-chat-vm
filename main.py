import pytchat
import time
from flask import Flask

app = Flask(__name__)

video_id = "u7kIh97FaJs"
chat = pytchat.create(video_id=video_id)

# check if its a replay
if chat.is_replay():
    print("UPDATE VIDEO ID")
    exit()

def check_chat():
    for c in chat.get().sync_items():
        print(f"{c.datetime} {c.author.name} {c.message}")

def main():
    try:
        while True:
            check_chat()
            time.sleep(2) # every two seconds
            
    except KeyboardInterrupt:
        # Allows for a graceful exit when you press Ctrl+C
        print("\nClosed.")

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

if __name__ == "__main__":
    main()
