from django.core.management.base import BaseCommand, CommandError
import os
from pathlib import Path
import chat.constants as constants
from chat.utils.rag import RagMetrics
from chat.utils.utils import TerminalColor,Markdown

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

    def markdown_creation(self,name):
        md = Markdown(name)
        report_file = md.markdown_creator()
        if report_file:
            print(f"Markdown file is generated based on stored data, file path: {report_file}")
            success = True
            return success

    def handle(self,*args,**options):
        """
        add arguments:
        calculating new values: yes / no
            - passing hyper parameters
        showing numeric result : yes / no
        showing full result (visualization + numeric)
        
        
        """
        try:
            name = constants.BUSINESS_NAME_FOR_DATA
            success = False
            color = TerminalColor()
            beta = constants.BETA
            top_k = constants.TOP_K
            
            ragmetrics = RagMetrics(name=name,model=constants.OPENAI_CHAT_MODEL,top_k=top_k,beta=beta)
            # iterations = options["iterations"] #list
            div ='\n' + '-'*40 + '\n'
            if options['new']:
                try:
                    print(f"{div}You have selected to re-evaluate the RAG system, available Evaluations:\n- Retrieval: Recall, Precision, Map@top \n- LLM: LLM Hallucination{div}")
                    change_value = input(f'Here are the default values for hyperpramteres:\n{'-'*10}\nbeta: {beta} \ntop_k: {top_k}\n{'-'*10}\nif you like to change these values, type yes: ')

                    if 'yes' in change_value.strip():
                        try:
                            beta = input('Add the value for beta: (from 0 to 1): ')
                            beta = ragmetrics.beta_validator(float(beta.strip()))

                            top_k = input('Please select the value for top_k (from 1 to 50): ')
                            top_k = ragmetrics.top_k_validator(int(top_k.strip()))

                            
                            new_values = f"\n{'-'*10}\nbeta: {beta} \ntop_k: {top_k}\n{'-'*10}\n"
                            print(f"\nNew values: {new_values}\n")

                            # re-instantiate rag metrics with updated values
                            ragmetrics = RagMetrics(name=name,model=constants.OPENAI_CHAT_MODEL,top_k=top_k,beta=beta)

                            # Retrieval Metrics
                            retrieveal_metrics = ragmetrics.retrieveal_metrics()

                            # Hallucination Metrics
                            hallucination = ragmetrics.llm_hallucination()

                            success = self.markdown_creation(name)
                        except ValueError as e:
                            print(f"{color.red('Error')} \nValueError : {e}\n")
                    else:
                        retrieveal_metrics = ragmetrics.retrieveal_metrics()
                        hallucination = ragmetrics.llm_hallucination()

                        success = self.markdown_creation(name)
                except ValueError as e:
                    print(f'Error {e}')
                except KeyboardInterrupt:
                    print('\n\nYou have intreupted the operation\n')

            else:
                """
                Creating visualizations and markdown file from current values
                
                """
                success = self.markdown_creation(name)



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
        except TypeError as e :
            print(f"Type Error in rag_evaluation.py : {e}")