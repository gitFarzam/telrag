import re



class Redact():
    """
    This class is for redacting sensitive data in log files
    
    """
    def __init__(self):
        pass

    def redact_id(self,value):
        value = str(value)
        """
        Redacting numbers, ids, usernames, samples:
        1239747203 -> 1***03
        jack.brown22 -> j***22
        """
        if len(value) > 3:
            return str(value)[0] + '***' + str(value[-2:])
        return value

    def redact_email(self,value):
        value = str(value)
        if len(value) > 3:
            if '@' in value:
                email = value.split('@')
                part_1 = email[0]
                part_2 = email[1]
                value_1 = part_1[0] + '***' + part_1[-2:]
                value_2 = part_2[0] + '***' + part_2[-2:]

                return value_1 + value_2
            else:
                return '***'
        return value

    def redact_text(self,value):
        value = str(value)
        length = len(value)
        if length > 15 :
            return str(value)[5] + '***' + str(value[-5:])
        if length > 6 and length <= 15:
            return str(value)[3] + '***' + str(value[-3:])
        else:
            return value