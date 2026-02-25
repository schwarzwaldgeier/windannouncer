from datetime import datetime, timedelta
from requests import get, exceptions
from windrecord import WindRecord

class WeatherlinkClient:
    api_key: str
    api_secret: str
    station_id: str
    headers: dict
    base_url: str
    get_parameters: dict

    def __init__(self, api_key: str, api_secret: str, station_id: str, base_url="https://api.weatherlink.com/v2"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.station_id = station_id
        self.headers = {
            "X-API-SECRET": self.api_secret
        }
        self.base_url = base_url
        self.get_parameters = {"api-key": self.api_key}

     
    def get_historic_data(self, start_ts: int, end_ts: int):

        ''' Sensor Type: 27 '''
        ''' Manufacturer: Davis Instruments ''' 
        ''' Product Name: Vantage Pro2, Cabled, Metric''' 
        ''' Product Number: 6322CM''' 
        ''' Category: ISS''' 
        ''' Data Structure Type: 7 '''
        ''' Data Structure Description: EnviroMonitor ISS Archive Record   ''' 

        params = {**self.get_parameters, "start-timestamp": start_ts, "end-timestamp": end_ts}
        params_str = "&".join([f"{key}={value}" for key, value in params.items()])
        #print(params_str)
        url = (f"{self.base_url}/historic/"
               f"{self.station_id}?{params_str}&start-timestamp={start_ts}&end-timestamp={end_ts}")
        
        try:
            #response = get('https://example.com/invalid') #for error testing
            response = get(url, headers=self.headers, timeout=10)
            response.raise_for_status() #raises if status != 200            
            return response.json()
        
        except exceptions.RequestException as e:
            print(f"HTTP error: {e}")
            raise
        
        except ValueError as e:
            print(f"JSON decode error: {e}")
            return None
        
    
    def parse_wind_from_historic_sensor_data(self, historic_data) -> list[WindRecord]: 
        
        wind_records = []

        if not historic_data or "sensors" not in historic_data:
            return wind_records 

        for sensor in historic_data['sensors']:       

            if sensor["sensor_type"] == 27:
                data = sensor['data']
                for dataset in data:

                    if not self.check_historic_sensor_data_sanity(dataset):
                        continue 

                    timestamp = dataset.get('ts')
                    wind_speed_avg = dataset.get('wind_speed_avg')
                    wind_speed_hi = dataset.get('wind_speed_hi')
                    wind_dir_of_hi = dataset.get('wind_dir_of_hi')
                    wind_dir_of_prevail = dataset.get('wind_dir_of_prevail')
                    
                    record = WindRecord(timestamp=timestamp,
                                        wind_speed_5_min=self.mph_to_kph(wind_speed_avg),
                                        wind_gust_5_min=self.mph_to_kph(wind_speed_hi),
                                        wind_dir_5_min=wind_dir_of_prevail,
                                        wind_dir_of_gust_5_min=wind_dir_of_hi)
                    
                    wind_records.append(record)

        wind_records.sort(key=lambda x: x.timestamp, reverse=True)
        return wind_records
  

    def check_historic_sensor_data_sanity(self, dataset: dict) -> bool:

        ''' Validate a single dataset entry from Weatherlink ISS (type 27) '''
        ''' Data Structure Type: 7 '''

        if not dataset:
            print("[SANITY] Empty dataset, skipping...")
            return False

        required_fields = ["ts", "wind_speed_avg", "wind_speed_hi",
                        "wind_dir_of_hi", "wind_dir_of_prevail"]
        
        for f in required_fields:
            if dataset.get(f) is None:
                print(f"[SANITY] Missing field: {f} in dataset {dataset}")
                return False
        
        try:
            ts = int(dataset["ts"])
            datetime.fromtimestamp(ts)
        except Exception:
            print(f"[SANITY] Invalid timestamp: {dataset.get('ts')}")
            return False
        
        try:
            avg_speed = int(dataset["wind_speed_avg"])
            max_speed = int(dataset["wind_speed_hi"])
        except (TypeError, ValueError):
            print(f"[SANITY] Non-integer wind speeds in dataset {dataset}")
            return False

        if not (0 <= avg_speed < 250):
            print(f"[SANITY] Invalid avg wind speed: {avg_speed}")
            return False
        if not (0 <= max_speed < 250):
            print(f"[SANITY] Invalid max wind speed: {max_speed}")
            return False
        
        try:
            avg_dir = int(dataset["wind_dir_of_prevail"])
            max_dir = int(dataset["wind_dir_of_hi"])
        except (TypeError, ValueError):
            print(f"[SANITY] Non-integer wind directions in dataset {dataset}")
            return False

        #direction code: 0=N, 1=NNE, ... 14=NW, 15=NNW
        if not (0 <= avg_dir <= 15):
            print(f"[SANITY] Invalid prevailing direction: {avg_dir}") 
            return False
        if not (0 <= max_dir <= 15):
            print(f"[SANITY] Invalid gust direction: {max_dir}")
            return False

        return True
   

    def mph_to_kph(self, mph: float, precision=0) -> int:
        kph = mph * 1.60934
        return int(round(kph))

#not used for now, but may be useful for future expansion to current conditions endpoint
    # def get_current_sensor_data(self):
    #     ''' Sensor Type: 27 '''
    #     ''' Manufacturer: Davis Instruments '''
    #     ''' Product Name: Vantage Pro2, Cabled, Metric '''
    #     ''' Product Number: 6322CM '''
    #     ''' Category: ISS '''
    #     ''' Data Structure Type: 6 '''
    #     ''' Data Structure Description: EnviroMonitor ISS Current Conditions Record '''

    #     params_str = "&".join([f"{key}={value}" for key, value in self.get_parameters.items()])
    #     print(f"params string {params_str}")
    #     url = f"{self.base_url}/current/{self.station_id}?{params_str}"
    #     print(url)
    #     response = get(url, headers=self.headers)
    #     data = response.json()
    #     return data
    

    # def parse_current_sensor_data(self, response) -> dict:
    #     for sensor in response.get("sensors", []):
    #         if sensor.get("sensor_type") == 27:
    #             for entry in sensor.get("data", []):
    #                 wind_entry = {
    #                     "timestamp": entry.get("ts"),
    #                     "wind_dir": entry.get("wind_dir"),
    #                     "wind_dir_of_gust_10_min": entry.get("wind_dir_of_gust_10_min"),
    #                     "wind_gust_10_min": entry.get("wind_gust_10_min"),
    #                     "wind_speed": entry.get("wind_speed"),
    #                     "wind_speed_2_min": entry.get("wind_speed_2_min"),
    #                     "wind_speed_10_min": entry.get("wind_speed_10_min")
    #                 }

    #                 #print(wind_entry)

    #     return wind_entry
