import threading
from bot import bot, monitor
import logging
import time

logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

def retry_monitor():
    while True:
        try:
            monitor()
            break
        except Exception as e:
            print(f"An error occurred: {e}", flush=True)
            time.sleep(10*60)
    print("Monitor is over", flush=True)

thread1 = threading.Thread(target=bot.infinity_polling)
thread2 = threading.Thread(target=retry_monitor)

thread1.start()
thread2.start()

# Keep the main program running by joining the threads
thread1.join()
thread2.join()
