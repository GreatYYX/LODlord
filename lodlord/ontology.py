from rdflib import Graph


class Ontology(object):
    def __init__(self):
        self.graph = Graph(identifier='ontology')

    def load(self, *args, **kwargs):
        self.graph.parse(*args, **kwargs)
