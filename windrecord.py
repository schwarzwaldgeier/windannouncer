from datetime import datetime, timedelta

class WindRecord:    
    #for textblocks (~filenames)
    DIRECTIONS_SHORT = [
        'n', 'nno', 'no', 'ono', 
        'o', 'oso', 'so', 'sso', 
        's', 'ssw', 'sw', 'wsw', 
        'w', 'wnw', 'nw', 'nnw'
    ]

    #for KI voice
    DIRECTIONS_VERBOSE = [ 
        "nord", "nord-nordost", "nordost", "ost-nordost",
        "ost", "ost-südost", "südost", "süd-südost",
        "süd", "süd-südwest", "südwest", "west-südwest",
        "west", "west-nordwest", "nordwest", "nord-nordwest"
    ]

    def __init__(self, 
                 timestamp:int, 
                 wind_dir_5_min:int, wind_speed_5_min:int, 
                 wind_dir_of_gust_5_min:int, wind_gust_5_min:int,                                   
                 wind_dir_20_min: int | None = None, wind_speed_20_min: int | None = None, 
                 wind_dir_of_gust_20_min: int | None = None, wind_gust_20_min: int | None = None):
        
        self.timestamp = timestamp
        self.datetime_timestamp = datetime.fromtimestamp(timestamp)                
        
        #5 minutes average
        self.wind_dir_5_min=wind_dir_5_min        
        self.wind_speed_5_min = round(wind_speed_5_min)

        #5 minutes gust
        self.wind_gust_5_min = round(wind_gust_5_min)        
        self.wind_dir_of_gust_5_min=wind_dir_of_gust_5_min
        
        #20 minutes average
        self.wind_speed_20_min = wind_speed_20_min        
        self.wind_dir_20_min = wind_dir_20_min

        #20 minutes gust
        self.wind_gust_20_min = wind_gust_20_min    
        self.wind_dir_of_gust_20_min = wind_dir_of_gust_20_min    
                    
    @classmethod
    def ordinal_short(cls, direction: int | None) -> str | None:
        if direction is None:
            return None
        return cls.DIRECTIONS_SHORT[direction % 16]

    @classmethod
    def ordinal_verbose(cls, direction: int | None) -> str | None:
        if direction is None:
            return None
        return cls.DIRECTIONS_VERBOSE[direction % 16]

    @property
    def str_wind_dir_5_min_short(self): return self.ordinal_short(self.wind_dir_5_min)
    @property
    def str_wind_dir_5_min_verbose(self): return self.ordinal_verbose(self.wind_dir_5_min)

    @property
    def str_wind_dir_of_gust_5_min_short(self): return self.ordinal_short(self.wind_dir_of_gust_5_min)
    @property
    def str_wind_dir_of_gust_5_min_verbose(self): return self.ordinal_verbose(self.wind_dir_of_gust_5_min)

    @property
    def str_wind_dir_20_min_short(self): return self.ordinal_short(self.wind_dir_20_min)
    @property
    def str_wind_dir_20_min_verbose(self): return self.ordinal_verbose(self.wind_dir_20_min)

    @property
    def str_wind_dir_of_gust_20_min_short(self): return self.ordinal_short(self.wind_dir_of_gust_20_min)
    @property
    def str_wind_dir_of_gust_20_min_verbose(self): return self.ordinal_verbose(self.wind_dir_of_gust_20_min)


    def __repr__(self):
        return (f"WindRecord({self.datetime_timestamp}, "
        f"avg5={self.wind_speed_5_min}km/h {self.str_wind_dir_5_min_verbose}, "
        f"gust5={self.wind_gust_5_min}km/h {self.str_wind_dir_of_gust_5_min_verbose})")


    def is_recent(self, max_age=3) -> bool:
        return datetime.now() - self.datetime_timestamp <= timedelta(minutes=max_age)