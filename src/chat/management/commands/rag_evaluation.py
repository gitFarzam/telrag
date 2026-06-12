from django.core.management.base import BaseCommand, CommandError
import os
from pathlib import Path
import chat.constants as constants
from chat.utils.rag import RagMetrics
from chat.utils.utils import TerminalColor

class Command(BaseCommand):

    help = f"""
    RAG Evluation Help \n\n
    """

    def add_arguments(self, parser):
        # Positional arguments
        # parser.add_argument("iterations", nargs="+", type=int) # this is mandatory

        # Named (optional) arguments
        parser.add_argument(
            "--new",
            action="store_true",
            help="Renew Evaluation for all metrics",
        ) # this is not mandatory

    def handle(self,*args,**options):
        """
        add arguments:
        calculating new values: yes / no
            - passing hyper parameters
        showing numeric result : yes / no
        showing full result (visualization + numeric)
        
        
        """
        success = False
        color = TerminalColor()
        beta = constants.BETA
        top_k = constants.TOP_K

        ret_test_data_path = constants.data_path('telmart')['test_retrieval_question_jsonl']
        llm_test_data_path = constants.data_path('telmart')['llm_eval_qa']
        ragmetrics = RagMetrics(model=constants.OPENAI_CHAT_MODEL,top_k=top_k,beta=beta)
        
        # iterations = options["iterations"] #list
        if options['new']:
            try:
                change_value = input(f'Here are the current values for hyperpramteres:\n{'-'*10}\nbeta: {beta} \ntop_k: {top_k}\n{'-'*10}\nif you like to change these values, type yes: ')

                if 'yes' in change_value.strip():
                    try:
                        beta = input('Add the value for beta: (from 0 to 1): ')
                        beta = ragmetrics.beta_validator(float(beta.strip()))

                        top_k = input('Please select the value for top_k (from 1 to 50): ')
                        top_k = ragmetrics.top_k_validator(int(top_k.strip()))

                        
                        new_values = f"\n{'-'*10}\nbeta: {beta} \ntop_k: {top_k}\n{'-'*10}\n"
                        print(f"\nNew values: {new_values}\n")
                        success = True
                    except ValueError as e:
                        print(f"{color.red('Error')} \nValueError : {e}")
                else:
                    print(f"Going ahead with default values")
                    success = True
            except ValueError as e:
                print(f'Error {e}')

        else:
            """
            Creating visualizations and markdown file from current values
            
            """
            pass
            




        # print(iterations)


        # try:
        # retrieveal_metrics = ragmetrics.retrieveal_metrics(ret_test_data_path, top_k=10) # this should find the same document and not the same category (or maybe both)
        # hallucination = ragmetrics.llm_hallucination(llm_test_data_path)

        # visualization = ragmetrics.visualization('telmart')

        # except Exception as e:
        #     raise CommandError(f"Error: {e}")

        if success:
            self.stdout.write(
                self.style.SUCCESS(f"Done!")
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"Unsuccessfull Operation")
            )

        # python manage.py rag_evaluation