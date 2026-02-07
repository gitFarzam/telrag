from langchain_text_splitters import RecursiveCharacterTextSplitter


class TextSplitter(RecursiveCharacterTextSplitter):

    def __init__(self, separators = None, keep_separator = True, is_separator_regex = False, text=None,**kwargs):
        super().__init__(separators, keep_separator, is_separator_regex,  chunk_size = 4000,
        chunk_overlap = 200,**kwargs)

    def split_documents(self, documents):
        return super().split_documents(documents)