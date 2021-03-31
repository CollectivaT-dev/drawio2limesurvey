from bs4 import BeautifulSoup as bs
import sys
import re
import pandas as pd

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

    def connect_graph(self):
        vertices_to_process = [self.bs_content.find('mxcell',
                                            attrs={'id':self.first_vertex_id})]
        self.survey_elements = []
        while vertices_to_process:
            vertex = vertices_to_process[0]
            vertex_edges = self.get_out_edges(vertex.get('id'))
            vertex_answers = [v[1] for v in vertex_edges]
            next_vertices = self.get_next_vertices(vertex_edges)
            survey_element = self.gen_survey_elements(vertex, vertex_edges)
            self.survey_elements.append(survey_element)
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
        next_vertices = []
        for edge, value in vertex_edges:
            if edge.get('target'):
                nv = self.bs_content.find('mxcell',
                                          attrs= {'id':edge.get('target')})
                nv['source_element_id'] = edge.get('source')
                source_answer = self.bs_content.find('mxcell',
                                             attrs={'vertex':'1',
                                                    'parent':edge.get('id')})
                if source_answer:
                    nv['source_answer'] = source_answer.get('value')
                next_vertices.append(nv)
        
        return next_vertices

    def gen_survey_elements(self, vertex, vertex_edges):
        survey_element = {"id":vertex.get('id'),
                          "text": vertex.get('value'),
                          "answers":[v[1] for v in vertex_edges],
                          "targets":[v[0].get('target') for v in vertex_edges]}
        for key in ["source_element_id", "source_answer"]:
            survey_element[key] = vertex.get(key)

        return survey_element


def from_dictlist_to_df(dict_list, branch_name='test', language='en'):
    dd=[]
    dd.append([branch_name+'_branch', 'G','1', 1, 'Group of questions: '+branch_name+' branch', language, None, None, None])
 
    for dic in dict_list:
        nreplies=len(dic.get('answers'))
        text=dic.get('text')
        class_type='Q'
    
        if dic.get('source_element_id'):
            source_question=next((item for item in dict_list if item["id"] == dic.get('source_element_id')), None)
            source_answers=source_question.get('answers')
        
            if len(source_answers)>1:
                stringa=dic.get('source_answer')
                ai=source_answers.index(stringa)
                relevance=dic.get('source_element_id')+"=='a"+str(ai+1)+"'"
            else:
                relevance=dic.get('source_element_id') ## This must be fixed, now it is not doing what it should
        else:
            relevance=1
        
        if nreplies>1:
            question_type='L'
            mandatory='Y'
        else:
            if (re.search('font color', text)): ##Might be a good idea to look for a more general rule to identify the red boxes..
                question_type='X'
                mandatory='N'

                pattern="<b>(.*?)</b>" ## Here too, not sure how general it is this pattern
                service = re.search(pattern, dic.get('text')).group(1)
                service = re.sub('<br>', ' ', service)
            
                if (re.search('MOVE TO', text)):   ## Used to separate the "MOVE TO BRANCH..." box from the service boxes
                    text="You can move to a new branch"
                else:
                    text="You might be interested in the following service: "+service
            else:  ## In theory it never enters here, there are not such cases
                class_type=None
                question_type=None
                mandatory='N'
            
        dd.append([dic.get('id'), class_type, question_type, relevance,  text, language, None, mandatory, 'N'])
    
        if nreplies>0 and question_type=='L': 
            for i in range(0, nreplies): ## Adding a new record for each possible answer
                dd.append(['a'+str(i+1), 'A', 0, None, dic.get('answers')[i], language, 0.0, None, None])


    df = pd.DataFrame(dd, columns=['name',  'class', 'type/scale', 'relevance','text', 'language', 'assessment_value', 'mandatory', 'other'])
    return df


def add_survey_headers(df, survey_head_df):
    col1= survey_head_df.columns
    col2=df.columns

    for col in col1[~col1.isin(col2)]:
        df[col]=None
    
    dd=pd.concat([survey_head_df,df[col1]], axis=0)
    dd=dd.reset_index()

    dd=dd.drop(['index'],axis=1)
    dd=dd.reset_index()
    dd['id']=dd['index']

    return dd

def main(filename):
    graph = Graph(filename)
    graph.get_first_vertex()
    graph.connect_graph()

    dics=[]
    for survey_element in graph.survey_elements:
        #print(survey_element)
        dics.append(survey_element)

    df=from_dictlist_to_df(dics, branch_name='test')

    ##TO_DO: Before merging the "header" we'll have to add a loop on the different branches and append all the df in a single one 
    
    ##-- Loading a csv containing the general survey information (obtained from the export of a survey created in limesurvey as example)
    survey_head=pd.read_csv('AF_limesurvey_headlines.csv', sep='\t')

    ##-- Adding the "header"
    df_survey=add_survey_headers(df, survey_head)


    ##-- Saving the final df as csv:
    df_survey.drop(['index'],axis=1).to_csv('survey_enfortim_test.csv', sep='\t', index=False)


    
if __name__ == "__main__":
    filename = sys.argv[1] 
    main(filename)
