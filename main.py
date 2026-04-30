import pytchat
import time

chat = pytchat.create(video_id="uIx8l2xlYVY")

def check_chat():
    chatdata = chat.get()
    print(chatdata.json())

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
