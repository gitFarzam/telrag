def telegram_input_filter(text:str)->bool:
    if len(text) < 10:
        return False