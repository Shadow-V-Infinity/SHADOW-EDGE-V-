from ..ingestion.dummy_ingestor import DummyIngestor

class CoreService:
    def __init__(self):
        self.ingestor = DummyIngestor()

    def health_check(self):
        data = self.ingestor.fetch()
        return {"status": "alive", "data": data}
