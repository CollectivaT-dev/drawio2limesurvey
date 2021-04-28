from bs4 import BeautifulSoup as bs
from graph import Graph
import sys
import os
import re
import pandas as pd


## TO_DO:
## 1. In from_dictlist_to_df() we did not implement the case where we have multiple source questions and one or more of them have multiple answers bringing to the same box
## 2. In main(), before merging the "header" we'll have to add a loop on the different branches and append all the df in a single one 
   
def from_dictlist_to_df(dict_list, branch_name='test', language='en'):
    dd=[]
    dd.append([branch_name, 'G','1', 1, 'Preguntes temàtiques de '+branch_name, language, None, None, None])
 
    for dic in dict_list:
        #print('-------------- ',dic)
        #print('***** ', dic.keys())
                
        text=dic.get('text')
        class_type='Q'
        
        #print('********  ',text)
        #print(dic.get('answers'))

    
        if dic.get('source_element_id'):
            #print('--------**** Question: ', text)
            #print('--- Number of  source elements: ',len(dic.get('source_element_id')))
            if len(dic.get('source_element_id'))==1:
                source_question=next((item for item in dict_list if item["id"] == dic.get('source_element_id')[0]), None)
                source_answers=source_question.get('answers')
                #print('-- Possible answers of the source_question: ', source_answers)
                #print('-- Length of answers_source_question array: ', len(source_answers))     
                #print('-- This is the answer that triggers the question: ',dic.get('source_answer'))
                #print('')

                ## Loop to take into account those cases where more than one answer to the source question lead to the question in consideration
                j=0
                for reply in dic.get('source_answer'):
                    ai=source_answers.index(reply)
                    if j==0:
                        relevance=dic.get('source_element_id')[0]+"=='a"+str(ai+1)+"'"
                    else:
                        relevance=relevance+" || "+dic.get('source_element_id')[0]+"=='a"+str(ai+1)+"'"
                    j=j+1

            else:
                #print('----- More than one source question!!!!!!!!: ', len(dic.get('source_element_id')))
                i=0
                for quest in dic.get('source_element_id'):
                    reply=dic.get('source_answer')[i]
                    
                    source_question=next((item for item in dict_list if item["id"] == quest), None)
                    source_answers=source_question.get('answers')

                    ai=source_answers.index(reply)                                                        

                    if i==0:
                        relevance=quest+".NAOK=='a"+str(ai+1)+"'"
                    else:
                        relevance=relevance+" || "+quest+".NAOK=='a"+str(ai+1)+"'"
                    i=i+1                 
 
        
        else:
            relevance=1
            
        if (len(list(set(dic.get('answers'))))==1 and list(set(dic.get('answers')))[0]==''):
            nreplies=0
        else:
            nreplies=len(dic.get('answers'))
                
        if nreplies>0:
            question_type='L'
            mandatory='Y'
        else:
            question_type='X'
            mandatory='N'
            if (re.search('font color', text)): ##Might be a good idea to look for a more general rule to identify the red boxes..
                service = re.sub('<.*?>', '', dic.get('text'))
            
                if (re.search('CONTINUA A', text)):   ## Used to separate the "MOVE TO BRANCH..." box from the service boxes
                    text="You can move to a new branch"
                    mandatory='Y'
                else:
                    text="You might be interested in the following service: "+service
                    
            
        dd.append([dic.get('id'), class_type, question_type, relevance,  text, language, None, mandatory, 'N'])
    
        if nreplies>0 and question_type=='L': 
            for i in range(0, nreplies): ## Adding a new record for each possible answer
                dd.append(['a'+str(i+1), 'A', 0, None, dic.get('answers')[i], language, 0.0, None, None])


    df = pd.DataFrame(dd, columns=['name',  'class', 'type/scale', 'relevance','text', 'language', 'assessment_value', 'mandatory', 'other'])


    ## Reordering the df (putting all the messages about possible services at the end and the "move to new branch"-message as the last one)
    final_row=df.index[df['text'].str.contains("continua a", case=False)].tolist()
    print(final_row)
    message_rows=df.index[(df['type/scale'] == 'X')].tolist()
    message_rows.remove(final_row[0])
    #print('Indexes of rows to show at the end: ', message_rows)
    #print('Index of final message: ', final_row)

    df_part1=df.iloc[[i for i in df.index if (i not in message_rows) and (i not in final_row)], :]
    df_part2=df.iloc[message_rows, :]
    df_part3=df.iloc[final_row, :]

    df=pd.concat([df_part1, df_part2, df_part3])
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


def main(filename, branch_name):
    graph = Graph(filename)
    graph.get_first_vertex()
    graph.connect_graph(graph.first_vertex_id)

    dics=[]
    for survey_element in graph.survey_elements:
        print(survey_element)
        dics.append(survey_element)

    #print(dics)

    df=from_dictlist_to_df(dics, branch_name)
    print(df.tail(10))
    
    ##TO_DO: Before merging the "header" we'll have to add a loop on the different branches and append all the df in a single one 
    
    ##-- Loading a csv containing the general survey information (obtained from the export of a survey created in limesurvey as example)
    survey_head=pd.read_csv('AF_limesurvey_headlines.csv', sep='\t')

    ##-- Adding the "header"
    df_survey=add_survey_headers(df, survey_head)

    outfile = os.path.basename(filename).replace('.xml','')+'.txt'
    ##-- Saving the final df as csv:
    df_survey.drop(['index'],axis=1).to_csv(outfile, sep='\t', index=False)


    
if __name__ == "__main__":
    filename = sys.argv[1]
    branch_name = sys.argv[2] 
    main(filename, branch_name)
