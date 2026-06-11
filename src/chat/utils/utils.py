import pandas as pd
import json
import os
import chat.constants as constants

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
        ut = Utils()
        path = constants.data_path('telmart')

        # Retrieval
        self.df_ret = ut.jsonl_reader(path['result'])
        self.df_ret_history = ut.jsonl_reader(path['result_history'])

        # LLM
        self.df_llm = ut.jsonl_reader(path['llm_result'])
        self.df_llm__history = ut.jsonl_reader(path['result_llm_history'])

        # Plots
        self.ret_plot = path['ret_plot']
        self.llm_plot = path['llm_plot']

        # Report file
        self.report_file = path['evaluation_report']

    def save_file(self,content):
        with open(self.report_file,'w',encoding='utf-8') as file:
            file.write(content)

    def markdown_creator(self):

        intro = "Evaluation result: \n"

        # Retrieval Result
        retrieval_table = f"## Retrieval Evaluation{self.table_creator(self.df_ret)}"
        retrieval_plot = self.image_creator(self.ret_plot)


        ending = "Thank you for reviewing this information"

        content = f"""{intro}{retrieval_table}{retrieval_plot}{ending}"""

        self.save_file(content)


    def table_creator(self,df:pd.DataFrame):
        table = df.to_markdown()
        table = f"\n\n{table}\n\n"
        return table
    
    def image_creator(self,image_path):
        image = f"![](plots/retrieval.png)"
        image = f"\n\n{image}\n\n"

        return image
