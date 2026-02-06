def agent_detecting_context():
    """
    This function if for detecting whether context is for storing in the database or it's just for the current note

    True: for storing in the database

    this logic can be simplified by adding an emoji or sign, which means do not store it , like: writing in bold in the message or may be a command with / might be detected, like /pass , means pass storing
    """

    return True