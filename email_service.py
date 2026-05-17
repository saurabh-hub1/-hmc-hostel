# email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email_config import EMAIL_ADDRESS, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT

def get_app_id(application):
    """Safely get app_id from application dict (handles both '_id' and 'app_id')"""
    return application.get('app_id') or str(application.get('_id', 'N/A'))

def send_approval_email(application):
    """Send approval email to student"""
    try:
        # Get email recipient
        recipient = application.get('email')
        if not recipient:
            print(f"⚠️ No email found for application")
            return False
        
        # Safely get app_id
        app_id = get_app_id(application)
        applicant_name = application.get('applicant_name', 'Sir/Madam')
        from_date = application.get('from_date', 'N/A')
        to_date = application.get('to_date', 'N/A')
        rooms_required = application.get('rooms_required', 1)
        purpose = application.get('purpose', 'N/A')
        
        subject = f"✅ HMC Hostel Application Approved - #{app_id}"
        
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; }}
                .header {{ background: #2c3e50; color: white; padding: 10px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ padding: 20px; }}
                .details {{ background: #f8f9fa; padding: 15px; border-radius: 10px; margin: 15px 0; }}
                .footer {{ text-align: center; font-size: 12px; color: #666; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🏢 HMC Godavari/Yamuna Hostel</h2>
                    <p>Defence Institute of Advanced Technology, Pune</p>
                </div>
                <div class="content">
                    <h3>Dear {applicant_name},</h3>
                    <p>Your room booking application has been <strong style="color: #27ae60;">APPROVED</strong>!</p>
                    
                    <div class="details">
                        <h4>📋 Booking Details:</h4>
                        <p><strong>Application ID:</strong> #{app_id}</p>
                        <p><strong>Room Required:</strong> {rooms_required} room(s)</p>
                        <p><strong>From:</strong> {from_date}</p>
                        <p><strong>To:</strong> {to_date}</p>
                        <p><strong>Purpose:</strong> {purpose}</p>
                    </div>
                    
                    <p><strong>Next Steps:</strong></p>
                    <ul>
                        <li>Please visit the hostel for check-in</li>
                        <li>Carry a valid ID proof at the time of check-in</li>
                        <li>Contact the warden for room allocation</li>
                    </ul>
                    
                    <p>Thank you for choosing HMC Hostel!</p>
                    <p><strong>Wishing you a pleasant stay! 🏨</strong></p>
                </div>
                <div class="footer">
                    <p>© 2025 HMC Hostel, DIAT Pune | This is an auto-generated email</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        print(f"📧 Sending approval email to {recipient}...")
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Approval email sent successfully to {recipient}")
        return True
        
    except Exception as e:
        print(f"❌ Approval email failed: {e}")
        return False

def send_rejection_email_with_reason(application, rejection_reason="No reason provided"):
    """Send rejection email with reason"""
    try:
        recipient = application.get('email')
        if not recipient:
            print(f"⚠️ No email found for application")
            return False
        
        app_id = get_app_id(application)
        applicant_name = application.get('applicant_name', 'Sir/Madam')
        
        subject = f"❌ HMC Hostel Application Update - #{app_id}"
        
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; }}
                .header {{ background: #e74c3c; color: white; padding: 10px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ padding: 20px; }}
                .details {{ background: #f8f9fa; padding: 15px; border-radius: 10px; margin: 15px 0; }}
                .footer {{ text-align: center; font-size: 12px; color: #666; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🏢 HMC Godavari/Yamuna Hostel</h2>
                    <p>Defence Institute of Advanced Technology, Pune</p>
                </div>
                <div class="content">
                    <h3>Dear {applicant_name},</h3>
                    <p>We regret to inform you that your room booking application has been <strong style="color: #e74c3c;">REJECTED</strong>.</p>
                    
                    <div class="details">
                        <h4>📋 Application Details:</h4>
                        <p><strong>Application ID:</strong> #{app_id}</p>
                        <p><strong>Reason:</strong> {rejection_reason}</p>
                    </div>
                    
                    <p>If you have any questions, please contact the HMC office.</p>
                    <p>You may submit a new application if needed.</p>
                    
                    <p>Thank you for your understanding.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        print(f"📧 Sending rejection email to {recipient}...")
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Rejection email sent successfully to {recipient}")
        return True
        
    except Exception as e:
        print(f"❌ Rejection email failed: {e}")
        return False

# For backward compatibility
def send_rejection_email(application):
    """Send rejection email without reason (for backward compatibility)"""
    return send_rejection_email_with_reason(application, "Not specified")