# utils/validators.py
import re

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def is_valid_phone(phone):
    pattern = r'^(0[3|5|7|8|9])+([0-9]{8})$'
    return re.match(pattern, phone) is not None

def is_valid_cccd(cccd):
    return cccd.isdigit() and len(cccd) == 12