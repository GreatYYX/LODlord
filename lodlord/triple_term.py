from rdflib import URIRef, BNode, Literal

"""
the subject, which is an IRI or a blank node
the predicate, which is an IRI
the object, which is an IRI, a literal or a blank node
"""


class TripleTerm(object):
    # need to have value and type

    def __str__(self):
        raise NotImplementedError


class TripleURI(TripleTerm):
    def __init__(self, uri, slot=None, short_uri=None, is_predicate=False):
        self.uri = uri
        self.short_uri = short_uri or uri
        self.slot = slot
        self.id = None
        self.is_predicate = is_predicate
        self.ref_count = 0

    def __str__(self):
        return '{}'.format(self.short_uri)


class TripleBlank(TripleTerm):
    def __init__(self, uri, slot=None, short_uri=None):
        self.uri = uri
        self.short_uri = short_uri or uri
        self.slot = slot
        self.id = None
        self.ref_count = 0

    def __str__(self):
        if self.slot:
            return '{}'.format(self.short_uri)
        else:
            return '_:{}'.format(self.short_uri)


class TripleLiteral(TripleTerm):
    def __init__(self, value, data_type=None, short_data_type=None, lang=None, uri=None, slot=None, short_uri=None):
        self.value = value
        self.data_type = data_type
        self.short_data_type = short_data_type or data_type
        self.lang = lang
        self.uri = uri
        self.short_uri = short_uri
        self.slot = slot
        self.id = None
        self.ref_count = 0

    def __str__(self):
        value = self.value if not self.slot else self.short_uri
        if self.data_type:
            return '{}^^{}'.format(value, self.short_data_type)
        elif self.lang:
            return '{}@{}'.format(value, self.lang)
        else:
            return '{}'.format(value)
