"""Constants for the Slovak TV Program integration."""

DOMAIN = "sk_tv_program"
PLATFORMS = ["sensor"]

# Available Slovak channels
AVAILABLE_CHANNELS = {
    "rtvs1": "RTVS Jednotka",
    "rtvs2": "RTVS Dvojka",
    "rtvs24": "RTVS :24",
    "rtvs_sport": "RTVS Šport",
    "markiza": "TV Markíza",
    "doma": "TV Doma",
    "dajto": "TV Dajto",
    "joj": "TV JOJ",
    "joj_plus": "JOJ Plus",
    "wau": "WAU",
    "prima": "TV Prima",
    "ta3": "TA3",
}

# API Configuration
XMLTV_API_URL = "http://api.rtvs.sk/xml/xmltv.xml"
LEMONCZE_API_URL = "https://api.lemoncze.com/stable/program.php"
API_TIMEOUT = 30

# Default values
DEFAULT_DAYS_AHEAD = 7
