from bs4 import BeautifulSoup as bs
from graph import Graph
import sys
import re
import pandas as pd

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
        print(survey_element)
        dics.append(survey_element)

    df=from_dictlist_to_df(dics, branch_name='test')

    ##TO_DO: Before merging the "header" we'll have to add a loop on the different branches and append all the df in a single one 
    
    ##-- Loading a csv containing the general survey information (obtained from the export of a survey created in limesurvey as example)
    survey_head=pd.read_csv('AF_limesurvey_headlines.csv', sep='\t')

    ##-- Adding the "header"
    df_survey=add_survey_headers(df, survey_head)


    ##-- Saving the final df as csv:
    df_survey.drop(['index'],axis=1).to_csv('survey_enfortim_test.txt', sep='\t', index=False)


    
if __name__ == "__main__":
    filename = sys.argv[1] 
    main(filename)
