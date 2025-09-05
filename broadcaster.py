import os
import traceback
from datetime import datetime
from threading import Event
from collections import deque
from typing import Optional, Callable
from dotenv import load_dotenv
from weatherlink_client import WeatherlinkClient
from windrecord import WindRecord
import time

load_dotenv()

class Broadcaster:
    def __init__(self, query_delay: int = 30, history_size: int = 12):
        self.station_interval=300
        self.request_timeout = 180
        self.minimum_delay = query_delay
        self.history_size = history_size
        self.wind_records: deque[WindRecord] = deque(maxlen=history_size)

        self.client = WeatherlinkClient(
            api_key=os.getenv("API_KEY"),
            api_secret=os.getenv("API_SECRET"),
            station_id=os.getenv("STATION_ID"),
        )

        self.on_new_data: Optional[Callable[[WindRecord], None]] = None        
        self.start = int(datetime.now().timestamp()) - self.station_interval*self.history_size 
        self.last_record_ts: Optional[int] = None
    
    def _notify(self, record: WindRecord):
        if self.on_new_data:
            self.on_new_data(record)

    def _station_next(self, ts: int) -> int: ##station default interval 0;5;10;15 ...
        return (ts // self.station_interval + 1) * self.station_interval
    
    #******* CORE LOOP *******
    def listen(
        self,
        sigint_handler_event: Event,
        max_iterations: Optional[int] = None,
        estimated_wait_time: float = 10.0 * 60.0 + 30.0,
    ):
        self.last_record_ts = self.start
        next_expected = self._station_next(int(datetime.now().timestamp() - 180))
        first_run = True
        iteration = 0        
        backoff = self.minimum_delay        
    
        while not sigint_handler_event.is_set():
            iteration += 1
            if max_iterations and iteration > max_iterations:
                break                      
            
            if not first_run:                                                            
                now = int(datetime.now().timestamp())

                if now > next_expected + self.request_timeout:
                    next_expected = self._station_next(self._station_next(now) -self.station_interval + estimated_wait_time)
                    print("[LISTENER] Skip requesting, request time window over. Waiting for one intervall time.")

                wait_time = max(next_expected - now, backoff, self.minimum_delay)                
                print(f"[LISTENER] Waiting {wait_time}s before next query at {datetime.fromtimestamp(now + wait_time)}") 
                
                for _ in range(int(wait_time)):
                    if sigint_handler_event.is_set():
                        return
                    time.sleep(1)

            first_run = False

            try:
                end = int(datetime.now().timestamp())                
                start = self.last_record_ts

                print(f"[LISTENER] Request historic data from {datetime.fromtimestamp(start)} to {datetime.fromtimestamp(end)}")

                historic_data = self.client.get_historic_data(start, end)
                if historic_data == None:
                    continue
                
                new_records = self.client.parse_wind_from_historic_sensor_data(historic_data)

                if not new_records:
                    print("[LISTENER] No wind records, retrying later...")
                    continue
                
                fresh = [rec for rec in reversed(new_records) if rec.timestamp > self.last_record_ts]                

                if not fresh:
                    print("[LISTENER] No new wind records. Skipping this cycle.")
                    continue

                for rec in fresh:                    
                    rec_ts = int(rec.timestamp)                    
                    self.wind_records.append(rec)
                    print(f"[LISTENER] New record {datetime.fromtimestamp(rec.timestamp)} added to queue")                    

                    recent=self._get_recent_records(recent=4)
                    if len(recent) < 4:
                        print("[LISTENER] No average values for this windrecord so far < 4 values")

                    elif self._check_record_block(recent):                 
                        rec.wind_dir_of_gust_20_min, rec.wind_gust_20_min = self._get_strongest_gust(recent)
                        rec.wind_dir_20_min, rec.wind_speed_20_min = self._get_average(recent)                     

                    self.last_record_ts = rec_ts                                                            
                                               
                if self.last_record_ts + 30 < next_expected:                     
                    print(
                        f"[LISTENER] {datetime.now().strftime('%H:%M:%S')} . Record {datetime.fromtimestamp(self.last_record_ts).strftime('%H:%M:%S')} too old, "
                        f"waiting for next expected >= {datetime.fromtimestamp(next_expected).strftime('%H:%M:%S')}."
                    )                                                                        

                    continue
                
                next_expected = self.last_record_ts + estimated_wait_time #floating
                print(f"[LISTENER] Next request at {datetime.fromtimestamp(next_expected)}")

                backoff = self.minimum_delay

                # Notify subscribers with lastest valid record
                self._notify(self.wind_records[-1])                                                            

            except Exception as e:
                                
                print(f"[LISTENER] Error during fetch: {e}. Retrying in {backoff}s.", flush=True)
                #traceback.print_exc()
                #sigint_handler_event.wait(estimated_wait_time)
                for _ in range(int(backoff)):
                    if sigint_handler_event.is_set():
                        return
                    time.sleep(1)               
                
                backoff = min(backoff * 2, 3600)  # exponential backoff, cap at 1 our
                
                continue

    def _check_record_block(self, block:list[WindRecord], required:int = 4, window_minutes: int = 20) -> bool:        
        if len(block) < required:
            print("[Broadcaster] Less than 4 records")
            return False
                
        timestamps = [rec.timestamp for rec in block]
        
        if any(t2 <= t1 for t1, t2 in zip(timestamps, timestamps[1:])):
            print("[Broadcaster] Records not strictly increasing")
            return False

        #timestamps unique?
        if len(set(timestamps)) != required:
            print(f"[Broadcaster] Expected {required} unique timestamps, got {len(set(timestamps))}")
            return False

        #timestamps up-to-date within time window?
        newest = timestamps[-1]
        cutoff = newest - window_minutes * 60
        if any(ts < cutoff for ts in timestamps):
            print(f"[Broadcaster] Last {required} records not within {window_minutes} min window")
            return False

        return True
    
    def _get_recent_records(self, recent: int) -> list[WindRecord]:
        return(list(self.wind_records)[-recent:])

    #if same gust max speed recent, take direction from latest                       
    def _get_strongest_gust(self, recent: list[WindRecord]) -> int : 
        max_speed = max(r.wind_gust_5_min for r in recent)
        candidates = [r for r in recent if r.wind_gust_5_min == max_speed]
        latest_with_max_speed = candidates[-1]        
        return latest_with_max_speed.wind_dir_of_gust_5_min, max_speed
       
    def _get_average(self, recent: list[WindRecord]) -> tuple[Optional[int], Optional[int]]:
          avg_speed = sum(r.wind_speed_5_min for r in recent) / len(recent)
          avg_dir = sum(r.wind_dir_5_min for r in recent) / len(recent)
          return round(avg_dir), round(avg_speed)
    