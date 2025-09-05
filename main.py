from signal import signal, SIGINT
from threading import Event
from platform import system
from pathlib import Path
from soundplayer import SoundBlockPlayer, EdgeTTSPlayer
from announcer import WindAnnouncer
from windrecord import WindRecord
from broadcaster import Broadcaster
from datetime import datetime
import os
# -------------------- CONFIG --------------------
BROADCAST_INTERVAL : int = 15  #minutes

SOUND_DIR = Path(__file__).parent / "sound" / "natural"

#output DIR for wav
if system() == "Windows":
    TEMP_DIR = Path("C:/temp")
else:
    TEMP_DIR = Path("/tmp")

def get_sigint_handler():
    waiter = Event()

    # pylint: disable=unused-argument
    def sigint_handler(signum, frame):
        waiter.set()  # pragma: no cover

    signal(SIGINT, sigint_handler)
    return waiter

def main():
    sigint_handler = get_sigint_handler()

    player_type = os.getenv("SOUND_PLAYER", "soundblock").lower()   
    if player_type == "tts":
        player = EdgeTTSPlayer(temp_dir=TEMP_DIR) 
    else:
        player = SoundBlockPlayer(sound_dir=SOUND_DIR, temp_dir=TEMP_DIR)
            
    announcer = WindAnnouncer(player=player, interval=10, max_age=3)
    
    def on_new_weather(record:WindRecord):
            print(f"[MAIN] {datetime.now():%H:%M:%S} received record: {record}")
            announcer.announce(record)
   
    broadcaster = Broadcaster()

    broadcaster.on_new_data = on_new_weather
    
    broadcaster.listen(sigint_handler_event=sigint_handler, estimated_wait_time = BROADCAST_INTERVAL * 60.0 + 30.0)

if __name__ == "__main__":
    main()
    


    