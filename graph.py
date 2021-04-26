from bs4 import BeautifulSoup as bs
from copy import copy
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
            print('First vertex with question:', q)

    def connect_graph(self, first_vertex):
        vertices_to_process = [self.bs_content.find('mxcell',
                                            attrs={'id':first_vertex})]
        self.survey_elements = []
        survey_elements = {}
        while vertices_to_process:
            vertex = vertices_to_process[0]
            vertex_edges = self.get_out_edges(vertex.get('id'))
            vertex_answers = [v[1] for v in vertex_edges]
            #print('* processing', vertex.get('id'), vertex.get('value').replace('\n',''), vertex.get('source_answer'))
            next_vertices = self.get_next_vertices(vertex, vertex_edges)
            survey_element = self.gen_survey_elements(vertex, vertex_edges)
            print('will be written as', survey_element)
            # repeating vertices are merged to incorporate different parents
            self.merge_survey_elements(survey_elements, survey_element)
            if None in survey_element['targets']:
                raise ValueError('%s has an edge without a target'%survey_element['text'])
            vertices_to_process.pop(0)
            vertices_to_process += next_vertices
            #print('vertices left to be processed')
            #print([(v.get('id'), v.get('source_element_id'), v.get('source_answer')) for v in vertices_to_process])
        self.survey_elements = list(survey_elements.values())

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

    def get_next_vertices(self, vertex, vertex_edges):
        next_vertices = []
        for edge, value in vertex_edges:
            if edge.get('target'):
                # check if vertex already exists
                source_element_id = edge.get('source')
                nv = self.bs_content.find('mxcell',
                                      attrs= {'id':edge.get('target')})
                nv['source_element_id'] = []
                nv['source_answer'] = []
                nv['source_element_id'].append(edge.get('source'))
                source_answer = self.bs_content.find('mxcell',
                                             attrs={'vertex':'1',
                                                    'parent':edge.get('id')})

                if source_answer:
                    nv['source_answer'].append(source_answer.get('value'))
                else:
                    # if there is no source answer it means the parent
                    # is a service we need to go to the grandparent
                    nv['source_element_id'].pop(-1)
                    nv['source_element_id'] = vertex['source_element_id']
                    nv['source_answer'] = vertex['source_answer']
                next_vertices.append(copy(nv))
        
        return next_vertices

    def gen_survey_elements(self, vertex, vertex_edges):
        survey_element = {"id":vertex.get('id')[-7:],
                          "text": vertex.get('value').replace('\n',' '),
                          "answers":[v[1] for v in vertex_edges],
                          "targets":[v[0].get('target')[-7:] for v in vertex_edges]}
        if vertex.get("source_element_id"):
            #survey_element["source_element_id"] = vertex.get("source_element_id")[-7:]
            survey_element["source_element_id"]=[s_id[-7:] for s_id in vertex.get('source_element_id')]
        survey_element["source_answer"] = vertex.get("source_answer")

        return survey_element

    def merge_survey_elements(self, se_dic, se_element):
        # if se_element is already in se_dic, new values are appended
        if se_dic.get(se_element['id']):
            se_original = se_dic.get(se_element['id'])
            # joining the two dicts, order matters
            # se_original comes last, hence its list will propagate to joined
            # disregarding the se_element value of the conflicting key
            se_joined = {**se_element, **se_original}
            for key, value in se_joined.items():
                if key in se_original and key in se_element and type(value) == list:
                    se_joined[key] = value + se_element[key]
            se_dic[se_element['id']] = se_joined
        else:
            se_dic[se_element['id']] = se_element
