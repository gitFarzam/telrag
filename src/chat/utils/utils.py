import pandas as pd
import json
import os

def telegram_input_filter(text:str)->bool:
    if len(text) < 10:
        return False
    
class Utils():
    """
    This class if made for evaluating retrieval performance, it gets multiple test query and will compare them with oberserved query, both queryies belong to a unique category, if categories were matched together, it means that retrieval worked properly with providing right documents @k

    test_query : jsonl file, will compite to dict: sample: {"query": "TelBurger submits refund requests immediately after approval", "category": "crm_support"}
    observed_query : fetches from database by retrieval and compiles as a dictionary like above
    k : a positive integer number will determine how many documents have to be retrieved from database

    Steps:
        1. Assigning an embedding model
        2. having the path for input_queries ready
        3. creating {'query':'embedding','category':'value'} for oberserved_query, by annotating Embedding model object
        4. seprating vector embeddings from Embedding model as an numpy 2D array from categories as a different list
        5. creating an embedding and category from test data as well, storing in the database
        6. measuring hybrid search function by considering these values
    """
    def __init__(self):
        return super().__init__()

    def text_strip(text:str):
        return text.strip()
    
    def jsonl_reader(self,path)->pd.DataFrame:
        """
        jsonL works fine with large data, as its possible to stream it and no need to load all at once. (for big size using yield for streaming)
        """

        with open(path) as f:
            return pd.DataFrame([json.loads(line) for line in f])
        

    def value_checker(self,df:pd.DataFrame,test_raw_path):
        """
        This method will check are all keys from source data (category and file_name) existed in the dataframe or not
        """
        unique_categories = sorted(df['category'].unique().tolist())
        unique_files = sorted(df['file_name'].unique().tolist())
        
        categories = sorted([dir.name for dir in os.scandir(test_raw_path) if dir.is_dir()])
        files=[]
        for category in categories:
            files +=[f for f in os.listdir(os.path.join(test_raw_path,category)) if f.endswith('.txt')]
        
        files = sorted(files)

        
        if unique_files == files and unique_categories == categories:
            return True
        else:
            print("there is a mismatch: unique_categories, categories , unique_files , files -> \n\n" , 
                        f"{unique_categories}\n\n{categories}\n\n{unique_files}\n\n{files}"
                    )
            return False
        
class Markdown():
    def __init__(self):
        pass

    def markdown_file_creator(self):
        result = "Evaluation result"

        table = self.md_table_creator(self.ret_result_df)


    def table_creator(self,df:pd.DataFrame):
        print(df.to_markdown())
        # columns = df.columns
        # values = df.values
        # """
        # sample:

        # | col1 | col2 | col3 |
        # | ---- | ---- | ---- |
        # | val1 | val2 | val3 |
        # | val4 | val5 | val6 |
        # """
        # table = "|"
        # for column in columns:
        #     table+= ' '+ column+' |' 

        # divider = "\n" +"| ---- "*columns.__len__() + "|"

        # table += divider

        # for

        # # print(table)
        # print(values[1])

        # return table
