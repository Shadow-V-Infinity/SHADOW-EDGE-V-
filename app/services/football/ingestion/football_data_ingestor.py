import os
import requests
from .base_ingestor import BaseIngestor

class FootballDataIngestor(BaseIngestor):
    BASE_URL = "https://api.football-data.org/v4"

    def __init__(self):
        self.api_key = os.getenv("X-Auth-Token")

    def fetch(self, endpoint="/competitions"):
        if not self.api_key:
            raise ValueError("X-Auth-Token is missing in environment variables")

        headers = {
            "X-Auth-Token": self.api_key
        }

        url = f"{self.BASE_URL}{endpoint}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise RuntimeError(f"API error: {response.status_code} — {response.text}")

        return response.json()

    def parse(self, raw):
        return raw

    def load(self, parsed):
        return parsed
