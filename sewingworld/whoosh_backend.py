from haystack.backends.whoosh_backend import WhooshEngine, WhooshSearchBackend
from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import TEXT
from whoosh.lang.snowball.russian import RussianStemmer


class RussianWhooshSearchBackend(WhooshSearchBackend):
    def build_schema(self, fields):
        schema = super(RussianWhooshSearchBackend, self).build_schema(fields)
        stemmer = RussianStemmer()
        for name, field in schema[1].items():
            if isinstance(field, TEXT):
                field.analyzer = StemmingAnalyzer(stemfn=stemmer.stem)
        return schema


class RussianWhooshEngine(WhooshEngine):
    backend = RussianWhooshSearchBackend
