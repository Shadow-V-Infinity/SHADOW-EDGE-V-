class BaseIngestor:
    def fetch(self):
        raise NotImplementedError

    def parse(self, raw):
        raise NotImplementedError

    def load(self, parsed):
        raise NotImplementedError
