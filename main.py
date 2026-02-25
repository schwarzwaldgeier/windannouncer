import sys
from signal import signal, SIGINT
from threading import Event
from soundplayer import SoundBlockPlayer, EdgeTTSPlayer
from announcer import WindAnnouncer
from windrecord import WindRecord
from broadcaster import Broadcaster
from datetime import datetime
import config
from logging_config import setup_logging

setup_logging()

def get_sigint_handler():
    waiter = Event()
    # Handle both SIGINT (Ctrl+C) and system termination
    signal(SIGINT, lambda signum, frame: waiter.set())
    return waiter

def main():
    print(f"[SYSTEM] Starting on {config.SYSTEM}. Temp path: {config.TEMP_DIR}")
    sigint_handler = get_sigint_handler()    

    if config.PLAYER_TYPE == "tts":
        player = EdgeTTSPlayer(temp_dir=config.TEMP_DIR) 
    else:
        player = SoundBlockPlayer(sound_dir=config.SOUND_DIR, temp_dir=config.TEMP_DIR)
            
    announcer = WindAnnouncer(player=player, interval=config.BROADCAST_INTERVAL, max_age=3)
    
    def on_new_weather(record:WindRecord):
            print(f"[MAIN] {datetime.now():%H:%M:%S} received record: {record}")
            announcer.announce(record)
   
    try:
        broadcaster = Broadcaster()

        broadcaster.on_new_data = on_new_weather
        
        broadcaster.listen(
            sigint_handler_event=sigint_handler, 
            estimated_wait_time = config.BROADCAST_INTERVAL * 60 + 30)

    except Exception as e:
        print(f"[FATAL ERROR] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
    


    