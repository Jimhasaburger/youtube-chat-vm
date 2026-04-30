import time

def say_hello():
    print("Hello, World!")

def main():
    try:
        while True:
            say_hello()
            time.sleep(2) 
            
    except KeyboardInterrupt:
        # Allows for a graceful exit when you press Ctrl+C
        print("\nClosed.")
if __name__ == "__main__":
    main()
