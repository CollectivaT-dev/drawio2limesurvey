from bs4 import BeautifulSoup as bs
import sys

class Graph(object):
    def __init__(self, filename):
        #TODO check if file xml and correct format
        with open(filename) as f:
            content = f.read()
        self.bs_content = bs(content, "lxml")
        self.edges = self.bs_content.findAll('mxcell', attrs={'edge':'1'})
        
    def get_first_vertex(self):
        sources = set()
        targets = set()
        for e in self.edges:
            sources.add(e.get('source'))
            targets.add(e.get('target'))
        self.first_vertex_id = sources.difference(targets)
        if not self.first_vertex_id:
            raise ValueError('First vertex not found')
        else:
            q = self.bs_content.find('mxcell',
                                     attrs={'id':self.first_vertex_id})\
                                     .get('value')
            print('First vertex with question:', )

    def connect_graph(self):
        vertices_to_process = [self.first_vertex_id]
        while vertices_to_process:
            vertex = self.bs_content.find('mxcell',
                                          attrs={'id':vertices_to_process[0]})
            vertex_edges = self.get_out_edges(vertex.get('id'))
            vertex_answers = [v[1] for v in vertex_edges]
            next_vertices = self.get_next_vertices(vertex_edges)
            survey_element = self.gen_survey_elements(vertex, vertex_edges)
            print(survey_element)
            if None in survey_element['targets']:
                raise ValueError('%s has an edge without a target'%survey_element['text'])
            vertices_to_process.pop(0)
            #TODO next vertices should be added only once
            vertices_to_process += next_vertices
            #print(vertices_to_process)

    def get_out_edges(self, source_id):
        v_edges = []
        for edge in self.edges:
            if edge.get('source') == source_id:
                v_edges.append(edge)

        vertex_edges_wanswer = []
        for edge in v_edges:
            edge_text_box = self.bs_content.find('mxcell',
                                  attrs={'vertex':'1',
                                         'parent':edge.get('id')})
            if edge_text_box:
                value = edge_text_box.get('value')
            else:
                value = ''
            vertex_edges_wanswer.append((edge, value))
        #TODO if there are more than one edge and one or more
        #TODO does not have a 'value' give error
        if len(vertex_edges_wanswer) > 1:
            for edge in vertex_edges_wanswer:
                if None in edge:
                    # source vertex
                    # target vertex
                    raise ValueError('an vertex has an edge without an answer')
        return vertex_edges_wanswer

    def get_next_vertices(self, vertex_edges):
        next_vertices = [edge[0].get('target')\
                         for edge in vertex_edges\
                         if edge[0].get('target')]
        return next_vertices

    def gen_survey_elements(self, vertex, vertex_edges):
        survey_element = {'id':vertex.get('id'),
                          'text': vertex.get('value'),
                          'answers':[v[1] for v in vertex_edges],
                          'targets':[v[0].get('target') for v in vertex_edges]}
        return survey_element

def main(filename):
    graph = Graph(filename)
    graph.get_first_vertex()
    graph.connect_graph()


if __name__ == "__main__":
    filename = sys.argv[1] 
    main(filename)
