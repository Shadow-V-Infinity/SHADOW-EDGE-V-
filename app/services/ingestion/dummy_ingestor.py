from .base_ingestor import BaseIngestor

class DummyIngestor(BaseIngestor):
    def fetch(self):
        return {"message": "ok"}

    def parse(self, raw):
        return raw

    def load(self, parsed):
        return parsed
