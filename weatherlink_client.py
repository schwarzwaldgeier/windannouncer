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
   

    def mph_to_kph(self, mph: float, precision=0) -> float:
        kph = mph * 1.60934
        return round(kph, precision)


    def get_current_sensor_data(self):
        ''' Sensor Type: 27 '''
        ''' Manufacturer: Davis Instruments '''
        ''' Product Name: Vantage Pro2, Cabled, Metric '''
        ''' Product Number: 6322CM '''
        ''' Category: ISS '''
        ''' Data Structure Type: 6 '''
        ''' Data Structure Description: EnviroMonitor ISS Current Conditions Record '''

        params_str = "&".join([f"{key}={value}" for key, value in self.get_parameters.items()])
        print(f"params string {params_str}")
        url = f"{self.base_url}/current/{self.station_id}?{params_str}"
        print(url)
        response = get(url, headers=self.headers)
        data = response.json()
        return data
    

    def parse_current_sensor_data(self, response) -> WindRecord:
        for sensor in response.get("sensors", []):
            if sensor.get("sensor_type") == 27:
                for entry in sensor.get("data", []):
                    wind_entry = {
                        "timestamp": entry.get("ts"),
                        "wind_dir": entry.get("wind_dir"),
                        "wind_dir_of_gust_10_min": entry.get("wind_dir_of_gust_10_min"),
                        "wind_gust_10_min": entry.get("wind_gust_10_min"),
                        "wind_speed": entry.get("wind_speed"),
                        "wind_speed_2_min": entry.get("wind_speed_2_min"),
                        "wind_speed_10_min": entry.get("wind_speed_10_min")
                    }

                    #print(wind_entry)

        return wind_entry

#     # @lru_cache
#     def get_sensors_data(self, sensor_id_list):
#         sensors_list_comma_separated = ",".join(map(str, sensor_id_list))
#         params_str = "&".join([f"{key}={value}" for key, value in self.get_parameters.items()])
#         url = f"{self.base_url}/sensors/{str(sensors_list_comma_separated)}?{params_str}"
#         response = get(url, headers=self.headers)
#         data = response.json()
#         return data

#     def get_single_sensor_data(self, sensor_id):
#         params_str = "&".join([f"{key}={value}" for key, value in self.get_parameters.items()])
#         url = f"{self.base_url}/sensors/{sensor_id}?{params_str}"
#         response = get(url, headers=self.headers)
#         data = response.json()
#         return data

#     def get_sensor_catalog(self):
#         params_str = "&".join([f"{key}={value}" for key, value in self.get_parameters.items()])
#         url = f"{self.base_url}/sensor-catalog?{params_str}"
#         response = get(url, headers=self.headers)
#         data = response.json()
#         return data

#     def convert_wind_dir(self, ordinal: int) -> str:
#         if ordinal < 0 or ordinal > 15:
#             raise ValueError("Must be a value between 0 and 15")
#         directions = [
#             "N", "NNO", "NO", "ONO", "O", "OSO", "SO", "SSO",
#             "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
#         ]

#         return directions[ordinal]


#     def inches_of_mercury_to_hpa(self, inches: float) -> float:
#         return inches * 33.8639

#     def generate_wind_records_html(self, wind_records, n):

#         html = """<!doctype html>
# <html>
#         <head>
#             <title>
#             Wetter Merkur
#             </title>
#         </head>
#         <body>
#         <style>
#     table {
#         width: 90%;
#         border-collapse: collapse;
#     }
#     th, td {
#         padding: 8px 12px;
#         border: 1px solid #ddd;
#         text-align: center;
#     }
#     th {
#         background-color: #f2f2f2;
#     }
#     tr:nth-child(even) {
#         background-color: #f9f9f9;
#     }
    
#     tr:nth-child(2) {
#     font-size: 150%;
#     }
    
#     .speed {
#         font-size: 150%;   
#     }
    
#     .direction {
#         font-size: 150%;   
        
#     }
# </style>
#         <table border="1" >
#             <tr>
#                 <th>&nbsp;</th>
#                 <th>Wind Ø</th>
#                 <th>Wind max.</th>
#             </tr>
#         """

#         arrow_svg_template = """
#                     <svg 
                   
#                     width="65"
#                     viewBox="0 0 100 75" 
#                     xmlns="http://www.w3.org/2000/svg">
#                       <g transform="rotate({rotation}, 50, 50)">
#                         <polygon points="50,15 60,50 50,40 40,50" fill="black" />
#                       </g>
#                     </svg>
#                     """
#         td_template = ("""
#         <td 
#             style="vertical-align: middle; font-size: 1.2em;">
#             <span class="speed">
#                 {speed}
#             </span>&nbsp;km/h&nbsp;

#             <span class="direction">
#                 {direction} {svg}
#             </span>
#         </td>
#         """)

#         rotation = 22.5
#         for record in wind_records[:n]:
#             avg_direction_svg = arrow_svg_template.format(rotation=record.avg_direction * rotation + 180)
#             max_direction_svg = arrow_svg_template.format(rotation=record.max_direction * rotation + 180)

#             avg_td = td_template.format(speed=int(record.avg_speed),
#                                         direction=self.convert_wind_dir(record.avg_direction), svg=avg_direction_svg)
#             max_td = td_template.format(speed=int(record.max_speed),
#                                         direction=self.convert_wind_dir(record.max_direction), svg=max_direction_svg)

#             html += f"""
#             <tr>
#                 <td><span>{(datetime.fromtimestamp(record.timestamp)
#                       + timedelta(hours=1)).strftime('%H:%M')}</span></td>
#                 {avg_td}
#                 {max_td}
#             </tr>
#             """

#         html += "</table></body></html>"
#         return html
