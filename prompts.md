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

PAY ATTENTION!: -> you have to add this data at the END of `telmart_retrieval.jsonl` file!

your job is to read all `.txt` files in this dir: `data/knowledge_base/telmart/test_data/source/product_help` and extract what the lines and add it to `telmart_retrieval.jsonl` as follows

you should not use a python script or any script to chunk the txt files senteces, because in this way the quality of extracted sentences are meaningless, you have to read txt files line by line and extract senteces from that, sentences should be completed and should be understandble by their own, not an incomplete or vauge sentence, so you have read them carefully.

All the pronouns for `query` key, you, your -> should point to The customer (the third person) , and sentences should be re written and then be pasted there. All of the sentences should be revised to check if they are to third person or not.

-> you have to add this data at the end of jsonl file!

## Promp 6

Your job is to generate unique questions instead of each query, and replace it with the current value for the query in this file: `data/knowledge_base/telmart/test_data/telmart_retrieval.jsonl`

Example 1:
before: Payment types accepted include cash, credit card, debit card, TelMart Pay, EBT/SNAP, gift cards, and other approved payment methods.
after: What payment types are accepted?

Example 2:
before: Most items are returnable within 90 days of purchase or receipt unless otherwise specified; items sold by third-party sellers may have a 30-day return window.
after: What is your return policy for purchased items and third-party seller items?

Example 3:
before: If the customer cannot renew their membership because the payment method is expired or declined they should update the payment method before attempting to renew.
after: What should a customer do if their membership renewal payment method is expired or declined?

Example 4:
before: The customer can find the nearest TelMart location that can process the replacement request by visiting TelMart.com or calling 800-925-6278.
after: How can a customer find the nearest TelMart location to process a replacement request?


IMPORTANT: What do I mean by generating unique question?

none of the 2 query should have similar questions, if one of them looks like another one, you have to change words , and way of asking to another way to look different , but you have to keep the context

for instance if a query is :
"Alternatively, the customer may contact Customer Service by chat, call 1-400-840-4060, or email help@telmart.com to report a delivery issue."
and you reached to a question like this: "How can a customer report a delivery issue to Customer Service?" and you found that you exactly generated a similar question, you have to write a new question , for example like this: "What phone number can a customer call to report a delivery issue?"