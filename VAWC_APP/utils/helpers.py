from datetime import datetime

def calculate_age(birthdate):
    today = datetime.now()
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age

def show_success(message):
    # Placeholder for success popup
    pass

def show_error(message):
    # Placeholder for error popup
    pass