from ..ingestion.football_data_ingestor import FootballDataIngestor

class CoreService:
    def __init__(self):
        self.ingestor = FootballDataIngestor()

    def health_check(self):
        return {"status": "alive", "data": {"message": "ok"}}

    def test_competitions(self):
        data = self.ingestor.fetch("/competitions")
        return data
