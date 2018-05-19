import re, hashlib
from urllib.parse import urlparse, parse_qs

from rdflib import Graph, Namespace, URIRef, BNode, Literal, RDF, XSD
from rdflib.namespace import NamespaceManager
from rdflib.plugins.parsers.notation3 import BadSyntax

from lodlord.triple_term import TripleURI, TripleLiteral, TripleBlank
from .record import Record, slot

LL_PREFIX = 'll'
LL_URI = 'http://lodlord/'
# ll:uri(v1)
re_uri = re.compile(LL_PREFIX + ':uri\((\w{1,255})\)')
# ll:bnode(b1)
re_blank = re.compile(LL_PREFIX + ':blank\((\w{1,255})\)')
# ll:literal(b3, type, lang), type and lang is optional
re_literal = re.compile(LL_PREFIX +
            ':literal\((\w{1,255})(,\s*type\s*=\s*([\w:]{1,255})){0,1}(,\s*lang\s*=\s*(\w{1,255})){0,1}\)')


class Model(object):
    def __init__(self, ontology, name='Unnamed Model'):
        self.error_stack = []
        self.ontolog = ontology
        # self.ontolog.graph.namespace_manager.bind(LL_PREFIX, Namespace(LL_URI))

        self.model_graph = Graph(identifier='model')

        # generate default namespaces
        ns_manager = NamespaceManager(self.model_graph)
        ns_manager.bind(LL_PREFIX, Namespace(LL_URI))
        for prefix, uri in ontology.graph.namespaces():
            ns_manager.bind(prefix, uri, override=True, replace=True)
        ns_manager.bind('', Namespace(''), override=True, replace=True)
        # self.all_namespaces = list(ns_manager.namespaces())
        self.all_namespaces = {ns[0]: ns[1] for ns in list(ns_manager.namespaces())}
        # print(self.all_namespaces)

        self.name = name
        self._reset()

    def _reset(self):
        self.all_terms = {} # all s, p and o terms
        self.all_relations = {} # node -> p_ref -> [node]
        self.template = []

    def _pre_process(self, raw_model):
        def process_literal(m):
            ret = r'{}:literal\?v\={}'.format(LL_PREFIX, m.group(1))
            if m.group(3): # type
                ret += '\&type\={}'.format(m.group(3))
            if m.group(5): # lang
                ret += '\&lang\={}'.format(m.group(5))
            return ret

        # print(raw_model)
        raw_model = re_uri.sub(r'{}:uri\?v\=\1'.format(LL_PREFIX), raw_model)
        raw_model = re_blank.sub(r'{}:blank\?v\=\1'.format(LL_PREFIX), raw_model)
        raw_model = re_literal.sub(lambda m: process_literal(m), raw_model)
        # print(raw_model)
        return raw_model

    @staticmethod
    def _get_obj_id(obj):
        if isinstance(obj, URIRef) or isinstance(obj, BNode):
            content = str(obj)
        else: # literal
            content = str(id(obj))
        hash_ = hashlib.md5()
        hash_.update(content.encode())
        return hash_.hexdigest()

    def get_short_uri(self, obj):
        if not obj:
            return

        uri = str(obj)
        if not uri.startswith(LL_URI):
            uri = self.model_graph.namespace_manager.qname(uri)
        else:
            parsed_uri = urlparse(uri)
            term = parsed_uri.path.strip('/')
            if term in ('uri', 'blank', 'literal'):
                params = {k: v[0] for k, v in parse_qs(parsed_uri.query).items()}
                parsed_uri = '{}:{}({})'.format(LL_PREFIX, term, params['v'])
                uri = parsed_uri
            else:
                # print(uri)
                uri = self.model_graph.namespace_manager.qname(uri)

        return uri

    def get_long_uri(self, short_uri):
        parsed_uri = short_uri.split(':')
        if len(parsed_uri) < 2:
            return parsed_uri

        prefix, suffix = parsed_uri
        if prefix in self.all_namespaces:
            return '{}{}'.format(self.all_namespaces[prefix], suffix)

        return parsed_uri


    @staticmethod
    def _is_rdf_type(p):
        return p == RDF.type

    def _create_node(self, obj):

        if isinstance(obj, URIRef):
            # not ll node
            uri = str(obj)
            if not uri.startswith(LL_URI):
                return TripleURI(self.get_short_uri(uri))

            # ll node
            parsed_uri = urlparse(uri)
            term = parsed_uri.path.strip('/')
            params = {k: v[0] for k, v in parse_qs(parsed_uri.query).items()}
            if term == 'uri':
                return TripleURI(uri=uri, slot=params['v'], short_uri=self.get_short_uri(uri))
            elif term == 'blank':
                return TripleBlank(uri=uri, slot=params['v'], short_uri=self.get_short_uri(uri))
            elif term == 'literal':

                data_type = params.get('type')
                lang = params.get('lang')

                if data_type:
                    data_type = self.get_long_uri(data_type)

                return TripleLiteral(value='',
                                     data_type=data_type, short_data_type=self.get_short_uri(data_type),
                                     lang=lang, slot=params['v'],
                                     uri=uri, short_uri=self.get_short_uri(uri))
            else:
                return TripleURI(uri=uri, short_uri=self.get_short_uri(uri))

        elif isinstance(obj, BNode):
            return TripleBlank(uri=str(obj))
        else:  # isinstance(obj, Literal)
            return TripleLiteral(value=obj._value, lang=obj._language,
                            data_type=obj._datatype, short_data_type=self.get_short_uri(obj._datatype))

    def _post_process(self):

        for s, p, o in self.model_graph:
            # print (s, p, o)
            s_ref, p_ref, o_ref = map(self._get_obj_id, [s, p, o])

            # create all nodes
            if s_ref not in self.all_terms:
                self.all_terms[s_ref] = self._create_node(s)
                self.all_terms[s_ref].id = s_ref

            if p_ref not in self.all_terms:
                self.all_terms[p_ref] = self._create_node(p)
                self.all_terms[p_ref].id = p_ref
                self.all_terms[p_ref].is_predicate = True

            if o_ref not in self.all_terms:
                self.all_terms[o_ref] = self._create_node(o)
                self.all_terms[o_ref].id = o_ref

            # link nodes by predicates
            if s_ref not in self.all_relations:
                self.all_relations[s_ref] = {}

            if p_ref not in self.all_relations[s_ref]:
                self.all_relations[s_ref][p_ref] = set()

            if o_ref not in self.all_relations[s_ref][p_ref]:
                self.all_relations[s_ref][p_ref].add(o_ref)


    def parse(self, data):
        '''
        
        :param data: 
        :return: 
        '''

        # TODO:
        # 1. remove bnode (only if all its referencer are bnode)?
        # 2. detect cycle
        # 3.

        # reset
        self._reset()

        # add prefixes
        data = '\n'.join(['@prefix {}:<{}> .'.format(k, v) for k, v in self.all_namespaces.items()]) + data
        # print(data)

        try:
            # pre process
            data = self._pre_process(data)

            # parse graph
            self.model_graph.parse(data=data, format='ttl')

            # post process
            self._post_process()

            return self.model_graph

        except BadSyntax as e:
            self.error_stack.append({'line': e.lines + 1, 'message': e.message})
            print(self.error_stack)

    def render(self, record: Record):
        self.template = []
        self.slots = []

        # for prop_name, prop_type in record.__class__.__dict__.items():
        #     if isinstance(prop_type, slot):
        #         print('slot detected:', prop_name)
        print(self.model_graph.serialize(format='nt').decode('utf-8'))
        exit()

        # bnode_mapping = {} # TripleBlank: BNode
        # for s_ref, s in self.all_nodes.items():
        #     for p_ref, objs in s.props.items():
        #         p = self.all_predicates[p_ref]
        #         for o in objs:
        #             # TODO: Literal
        #             # print(s_str, p_str, o_str)
        #             print(s, p, o)
        #             if isinstance(s, TripleBlank):
        #                 print(s.ref_count)
        #             if isinstance(p, TripleBlank):
        #                 print(p.ref_count)
        #             if isinstance(o, TripleBlank):
        #                 print(o.ref_count)
        #         # template = [s_str, p_str, o_str]

