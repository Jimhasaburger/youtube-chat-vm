import pytchat
import time

chat = pytchat.create(video_id="Kz3hYIzEYec")

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
if __name__ == "__main__":
    main()
