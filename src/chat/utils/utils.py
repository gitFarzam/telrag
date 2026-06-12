import pandas as pd
import matplotlib.pyplot as plt
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
        try:
            with open(path) as f:
                output = [json.loads(line) for line in f]
                try:
                    return pd.DataFrame(output)
                except ValueError as e :
                    print(f"Data creatio failed: {e}")
                except TypeError as e :
                    print(f"Wrong data type in the jsonl file: {e}")

        except json.decoder.JSONDecodeError as e:
            print(f'Error in decoding json file: {e}')


        

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
    def __init__(self,name):
        self.ut = Utils()
        self.color = TerminalColor()

        try:
            # Retrieval
            self.df_ret = self.ut.jsonl_reader(constants.data_path(name,'ret_result'))
            self.df_ret_history = self.ut.jsonl_reader(constants.data_path(name,'ret_result_history'))

            # LLM
            self.df_llm = self.ut.jsonl_reader(constants.data_path(name,'llm_result'))
            self.df_llm__history = self.ut.jsonl_reader(constants.data_path(name,'llm_result_history'))

            # Plots
            self.ret_plot = constants.data_path(name,'ret_plot')
            self.ret_history_plot = constants.data_path(name,'ret_history_plot')
            self.llm_plot = constants.data_path(name,'ret_plot')
            self.llm_history_plot = constants.data_path(name,'llm_history_plot')

            # Report file
            self.report_file = constants.data_path(name,'evaluation_report')
            self.ret_history_plot_md = constants.data_path(name,'ret_history_plot_md')
            self.llm_history_plot_md = constants.data_path(name,'llm_history_plot_md')


        except FileNotFoundError as e :

            # Turning of traceback message
            import sys
            sys.tracebacklimit = 0

            # raising exception at init level to avoid running program to the end of the process.
            raise FileNotFoundError(f"Can not initializae Markdown class and create markdown report, because of lack of some the files.\nmake sure use {self.color.yellow('--new')} flag to run the evaluator and generate necessary outputs (jsonl outputs and plots)\nError: {e}\n")
            




    def save_file(self,content):
        with open(self.report_file,'w',encoding='utf-8') as file:
            file.write(content)
        return self.report_file

    def markdown_creator(self):

        # Creating Visualizations
        try:
            visualization = self.visualization()
        except Exception as e:
            print(f"An error in visualization: {e}\n")

        try:
            if visualization:

                intro = "# Evaluation result: \n"

                # Retrieval Result
                retrieval_table = f"## Retrieval Evaluation{self.table_creator(self.df_ret)}"
                retrieval_plot = self.image_creator(self.ret_plot)

                ending = "Thank you for reviewing this information"

                # Shaping final content
                content = f"""{intro}{retrieval_table}{retrieval_plot}{ending}"""

                report_file = self.save_file(content)

                return report_file
        except UnboundLocalError as e :
            print(f"UnboundLocalError in markdown_creator method : {e}\n")


    def table_creator(self,df:pd.DataFrame):
        table = df.to_markdown()
        table = f"\n\n{table}\n\n"
        return table


    def visualization(self):
        # Making sure the path is existed
        plot_path = constants.data_path('telmart','result_plots')
        if not os.path.exists(plot_path):
            os.mkdir(plot_path)

        # Creating line plot for retriever metrics (evaluation process)
        for col in self.df_ret.columns.to_list():
            plt.plot(self.df_ret[col.__str__()])
        plt.savefig(self.ret_plot , dpi=300, bbox_inches='tight')

        # Creating line plot for llm metrics (evaluation process)
        for col in self.df_llm.columns.to_list():
            plt.plot(self.df_llm[col.__str__()])
        plt.savefig(self.llm_plot, dpi=300, bbox_inches='tight')


        return True

    def image_creator(self,image_path):
        image = f"![](plots/retrieval.png)"
        image = f"\n\n{image}\n\n"

        return image



class TerminalColor():
    def __init__(self):
        pass

    def red(self,text):
        return f"\033[1;31m{text}\033[0m"
    
    def blue(self,text):
        return f"\033[1;34m{text}\033[0m"
    
    def green(self,text):
        return f"\033[1;32m{text}\033[0m"
    
    def yellow(self,text):
        return f"\033[1;33m{text}\033[0m"