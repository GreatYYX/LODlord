from graphviz import Digraph

from lodlord.triple_term import TripleURI, TripleBlank, TripleLiteral


class ModelVisualizer(object):
    def __init__(self, model):
        self._g = Digraph(comment='Graph')
        self.model = model

    def render(self, *args, **kwargs):
        self._g.attr(label=self.model.name)

        # create all nodes
        for node_id, node in self.model.all_terms.items():
            if isinstance(node, TripleURI):
                if node.is_predicate:
                    continue
                self._g.attr('node', style='solid', color='', shape='oval',
                             fontcolor='red' if node.slot else '')
                self._g.node(node_id, str(node))
            elif isinstance(node, TripleBlank):
                self._g.attr('node', style='dashed', color='', shape='oval',
                             fontcolor='red' if node.slot else '')
                self._g.node(node_id, str(node))
            elif isinstance(node, TripleLiteral):
                self._g.attr('node', style='filled', color='grey', shape='box',
                             fontcolor='red' if node.slot else '')
                self._g.node(node_id, str(node))
            else:
                raise Exception('Unknown type of node')

        # create edges
        for s_ref, p_dict in self.model.all_relations.items():
            for p_ref, o_refs in p_dict.items():
                for o_ref in o_refs:
                    p_obj = self.model.all_terms[p_ref]
                    self._g.edge(s_ref, o_ref, label=str(p_obj),
                                 fontcolor='red' if p_obj.slot else '')

        self._g.render(*args, **kwargs)
