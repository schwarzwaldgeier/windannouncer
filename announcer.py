from soundplayer import SoundBlockPlayer, Player, EdgeTTSPlayer
from windrecord import WindRecord
from datetime import datetime, timedelta
import asyncio, logging

logger = logging.getLogger(__name__)

class WindAnnouncer:
    def __init__(self, player: Player, interval=10, max_age: int = 3):
        self.last_announcement: datetime | None = None
        self.sound_player = player
        self.interval=interval - max_age
        self.max_age=max_age
        self._last_record_timestamp: datetime | None = None

    def _is_valid_record(self, record: WindRecord) -> bool:                
        
        if not hasattr(record , "timestamp"):
            return False
        
        if not record.is_recent(self.max_age):
            return False
        
        return True
                     
    def _can_announce(self, record: WindRecord) -> bool:

        now = datetime.now()
        
        if not self._is_valid_record(record):
            print("[Announcer] Record too old for announcement...waiting for next")
            logger.warning("Record too old for announcement...waiting for next")
            return False
        
        if self.last_announcement and (now - self.last_announcement) < timedelta(minutes=self.interval):
            print("[Announcer] Too soon since last announcement.")
            logger.warning("Too soon since last announcement.")
            return False
        
        if self._last_record_timestamp == record.timestamp:
            print("[Announcer] Same record as before, skipping.")
            logger.warning("Same record as before, skipping.")
            return False

        logger.info(f"valid record: {record}")
        return True


    def announce(self, record:WindRecord) ->bool:
        
        if not self._can_announce(record):
            return False       

        msg_blocks = ["hier-ist-die-wetterstation-des-gleitschirmvereins-baden-auf-dem-merkur",
                      "durchschnittlicher-wind-der-letzten-5-minuten",
                      str(record.str_wind_dir_5_min_short), str(record.wind_speed_5_min), "kmh",
                      "staerkste-windboe-der-letzten-20-minuten",
                      str(record.str_wind_dir_of_gust_20_min_short),str(record.wind_gust_20_min), "kmh",
                      "tschuess"
                     ]   
                       

        #message for TTS soundplayer
        msg_tts = (
                    f"Hier ist die Wetterstation des Gleitschirmvereins Baden auf dem Merkur. "            
                    #f"Aktuelle Windmessung:  {record.current_direction} {record.current_speed} Kilometer pro Stunde. " #no current speed from historic sensor, instead using 5 minutes average
                    f"Durchschnittlicher Wind der letzten 5 Minuten:  {record.str_wind_dir_5_min_verbose} {record.wind_speed_5_min} Kilometer pro Stunde. "
                    f"Stärkste Windböe der letzten 20 Minuten: {record.str_wind_dir_of_gust_20_min_verbose} {record.wind_gust_20_min} Kilometer pro Stunde. "
                    #f"Tschüss! "
                  )
        
        print(f"[WindAnnouncer {datetime.now():%H:%M:%S}] Start announcing...\n")
        
        
        if isinstance(self.sound_player, SoundBlockPlayer):
            print("[Soundblock Mode]")            
            print(msg_blocks)
            logger.info(msg_blocks)
            try:
                sound_files = self.sound_player.create_sound_files_array(msg_blocks)                
                self.sound_player.play_message(sound_files)
            except FileNotFoundError as e:                
                print(f"[SoundblockPlayer ERROR] {e}")
            except ValueError as e:
                print(f"[SoundblockPlayer ERROR] {e}")
                
        elif isinstance(self.sound_player, EdgeTTSPlayer):
            print("[TTS Mode with EdgeTTSPlayer]")
            #self.sound_player.play_message(msg_tts)
            print(msg_tts)
            asyncio.run(self.sound_player.play_message(msg_tts))

        self.last_announcement = datetime.now()
        self._last_record_timestamp = record.timestamp

        return True