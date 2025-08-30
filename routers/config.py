import os

# API URLs and credentials
WP_API_URL = os.getenv("WP_API_URL", "https://staytour.vtlink.link/wp-json/mphb/v1")
WP_CONSUMER_KEY = os.getenv("WP_CONSUMER_KEY", "ck_972eead1eeee1b8340185d63929a96058fa42757")
WP_CONSUMER_SECRET = os.getenv("WP_CONSUMER_SECRET", "cs_eb8b8e24af51ddd8e7fa793f9bf7279cff33c8bb")

# Map room types for easy ID lookup
ROOM_TYPES_MAP = {
    "Economy Classic Room": 1943,
    "Triple Classic Room": 1189,
    "Business Class Room": 1190,
    "Royal Class Room": 1191,
    "Superior Ocean Room": 1192,
    "Classic Room": 1015,
    "Double Room": 1006,
    "Standard Room": 986,
    "Deluxe room": 3632
}