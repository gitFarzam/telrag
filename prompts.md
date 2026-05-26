## Prompt 1
Task: Rewriting all txt files in this directory : `data/knowledge_base/telmart/initial_data`

Your job is to rewrite all the .txt files in the provided directory.

you have to:
1. keep names, the meanings and data and information and contexts
2. keep TelMart name
3. rewriting using different words but common and natural words and sentences.

## Prompt 2
Task: Extracting each sentence or semantic part and add it to jsonl file : `telmart_retrieval.jsonl`

category: is the name of the parent directory where file is located
file_name: is the name of the file

your job is to read `data/knowledge_base/telmart/initial_data/checkout_support/self_checkout_help.txt` file and it to `telmart_retrieval.jsonl` as follows

you should not use a python script or any script to chunk the txt files senteces, because in this way the quality of extracted sentences are meaningless, you have to read txt files line by line and extract senteces from that, sentences should be completed and should be understandble by their own, not an incomplete or vauge sentence, so you have read them carefully.

All the pronouns for `query` key, you, your -> should point to The customer (the third person) , and sentences should be re written and then be pasted there. All of the sentences should be revised to check if they are to third person or not.

## Prompt 3
Task: Extracting each sentence or semantic part from .txt file and add it to jsonl file : `telmart_retrieval.jsonl`

category: is the name of the parent directory where file is located
file_name: is the name of the file

Example: this operation is already done for :`data/knowledge_base/telmart/test_data/source/checkout_support/cashier_help.txt` file and corrosponded data are already added to `telmart_retrieval.jsonl` file, so use that examlple to understand the data structure and skip doing this operation for`cashier_help.txt` file

your job is to read all `.txt` files in this path: `data/knowledge_base/telmart/test_data/source` and it to `telmart_retrieval.jsonl` as follows. 

you should not use a python script or any script to chunk the txt files senteces, because in this way the quality of extracted sentences are meaningless, you have to read txt files lines by lines and extract senteces from that, sentences should be completed and should be understandble by their own, not an incomplete or vauge sentence, so you have read them carefully.

## Prompt 4

check this path: `data/knowledge_base/telmart/test_data/telmart_retrieval.jsonl`

The pronouns are wrong in this file for `query` key, you, your -> should point to The customer , and sentences should be re written. All of the sentences should be revised to check if they are to third person or not.



## Prompt 5
Task: Extracting each sentence or semantic part and add it to jsonl file : `telmart_retrieval.jsonl`

category: is the name of the parent directory where file is located
file_name: is the name of the file

your job is to read all `.txt` files in this dir: `data/knowledge_base/telmart/initial_data/membership_and_account` and extract what the lines and add it to `telmart_retrieval.jsonl` as follows

you should not use a python script or any script to chunk the txt files senteces, because in this way the quality of extracted sentences are meaningless, you have to read txt files line by line and extract senteces from that, sentences should be completed and should be understandble by their own, not an incomplete or vauge sentence, so you have read them carefully.

All the pronouns for `query` key, you, your -> should point to The customer (the third person) , and sentences should be re written and then be pasted there. All of the sentences should be revised to check if they are to third person or not.