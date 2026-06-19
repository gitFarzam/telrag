<<<<<<< HEAD
def telegram_input_filter(text:str)->bool:
    if len(text) < 10:
        return False
||||||| 6d2c1b6
=======
import json
import os

import chat.constants as constants

import pandas as pd
import matplotlib.pyplot as plt

def telegram_input_filter(text:str)->bool:
    if len(text) < 10:
        return False

class Utils():

    """This class includes some functions for some generic purposes"""

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
        self.name:str = name
        self.ut = Utils()
        self.color = TerminalColor()

        try:
            # Retrieval
            self.df_ret = self.ut.jsonl_reader(constants.data_path(name,'ret_result'))
            self.df_ret_history= self.ut.jsonl_reader(constants.data_path(name,'ret_result_history'))

            # LLM
            self.df_llm = self.ut.jsonl_reader(constants.data_path(name,'llm_result'))
            self.df_llm__history = self.ut.jsonl_reader(constants.data_path(name,'llm_result_history'))

            # Plots Directory
            self.plot_path = constants.data_path('telmart','result_plots')

            # Retireval Plots
            self.ret_plot = constants.data_path(name,'ret_plot')

            # LLM Plots
            self.llm_plot = constants.data_path(name,'llm_plot')

            # Markdown file: Report
            self.report_file = constants.data_path(name,'evaluation_report')

            # Markdown plots path - Retrieval
            self.ret_plot_md = constants.data_path(name,'ret_plot_md')

            # Markdown plots path - LLM
            self.llm_plot_md = constants.data_path(name,'llm_plot_md')



        except FileNotFoundError as e :

            # Turning of traceback message
            import sys
            sys.tracebacklimit = 0

            # raising exception at init level to avoid running program to the end of the process.
            raise FileNotFoundError(f"Can not initializae Markdown class and create markdown report, because of lack of some the files.\nmake sure use {self.color.yellow('--new')} flag to run the evaluator and generate necessary outputs (jsonl outputs and plots)\nError: {e}\n")
            

    def path_creation(self):
        if not os.path.exists(self.plot_path):
            os.mkdir(self.plot_path)

    def save_file(self,content):
        with open(self.report_file,'w',encoding='utf-8') as file:
            file.write(content)
        return self.report_file

    def markdown_creator(self):

        # Creating required directories
        self.path_creation()

        # Retrieval Plot Creation
        self.plot_creator(self.df_ret,self.ret_plot)

        # LLM Plot Creation
        self.plot_creator(self.df_llm,self.llm_plot)

        # Intro
        intro = constants.REPORT_INTRO.format(name=self.name.capitalize())

        # Retrieval Result
        ret_intro = constants.RET_REPORT_INTRO
        ret_table = f"{self.table_creator(self.df_ret)}"
        ret_plot = self.image_creator(self.ret_plot_md)
        ret_history_table = f"### History\n{self.table_creator(self.df_ret_history)}"

        # LLM Result
        llm_intro = constants.LLM_REPORT_INTRO
        llm_table = f"{self.table_creator(self.df_llm)}"
        llm_plot = self.image_creator(self.llm_plot_md)
        llm_history_table = f"### History\n{self.table_creator(self.df_llm__history)}"

        # Ending
        ending = constants.REPORT_ENDING

        # Shaping final content
        content = self.template_creator([intro,ret_intro,ret_table,ret_plot,ret_history_table,llm_intro,llm_table,llm_plot,llm_history_table,ending])

        report_file = self.save_file(content)
        return report_file
    
    def table_creator(self,df:pd.DataFrame):
        table = df.to_markdown()
        table = f"\n\n{table}\n\n"
        return table

    def plot_creator(self,df:pd.DataFrame,path:str):
        for col in df.columns:
            plt.plot(df[col],label=col)
        plt.legend()
        plt.savefig(path , dpi=300, bbox_inches='tight')
        plt.close()

    def image_creator(self,image_path):
        image = f"![]({image_path})"
        image = f"\n\n{image}\n\n"

        return image

    def template_creator(self,content_list:list):
        """
        This functions adds a \n between each content item to make sure of no disorder in the markdown file
        """
        return "\n\n".join(content_list)

class TerminalColor():
    """
    This class is for colorizing texts in the terminal output.
    """
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
>>>>>>> demo
