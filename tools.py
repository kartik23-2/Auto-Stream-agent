import csv
import os
import re

def valid_email(email):
    return re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email) is not None

def mock_lead_capture(name, email, platform):
    file_exists = os.path.exists('leads.csv')
    with open('leads.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['name', 'email', 'platform'])
        writer.writerow([name, email, platform])
    print(f'Lead captured successfully: {name}, {email}, {platform}')