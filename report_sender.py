# report_sender.py
import os
import pandas as pd
from supabase import create_client, Client
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

def generate_excel_report():
    # Fetch attendance data
    response = supabase.table('students').select("*").execute()
    students_data = response.data

    # Create DataFrame
    df = pd.DataFrame(students_data)
    
    # Convert datetime to readable format
    df['last_attendance_time'] = pd.to_datetime(df['last_attendance_time']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Generate filename with timestamp
    report_date = datetime.now().strftime("%Y-%m-%d")
    filename = f"attendance_report_{report_date}.xlsx"
    
    # Save to Excel
    df.to_excel(filename, index=False)
    return filename

def send_email_with_attachment(filename):
    # Create email message
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = f"Attendance Report - {datetime.now().strftime('%d %B %Y')}"
    
    # Email body
    body = f"""\
    Dear Faculty,
    
    Please find attached the daily attendance report.
    
    Best regards,
    Attendance System
    """
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach Excel file
    with open(filename, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
    
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {filename}",
    )
    msg.attach(part)
    
    # Send email
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
    
    print(f"Email sent with {filename}")

if __name__ == "__main__":
    try:
        report_file = generate_excel_report()
        send_email_with_attachment(report_file)
        # Clean up the generated file
        os.remove(report_file)
        print("Report process completed successfully")
    except Exception as e:

        print(f"Error generating/sending report: {str(e)}")
