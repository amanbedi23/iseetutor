"""
Email service for sending parent reports and notifications.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails to parents."""
    
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@iseetutor.com")
        self.enabled = bool(self.smtp_user and self.smtp_password)
    
    async def send_weekly_report(
        self, 
        parent_email: str, 
        child_name: str, 
        report_data: Dict[str, Any],
        pdf_buffer: Optional[bytes] = None
    ) -> bool:
        """Send weekly progress report to parent."""
        if not self.enabled:
            logger.warning("Email service not configured. Skipping email.")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = parent_email
            msg['Subject'] = f"Weekly Progress Report for {child_name}"
            
            # Create HTML body
            html_body = self._create_report_html(child_name, report_data)
            msg.attach(MIMEText(html_body, 'html'))
            
            # Attach PDF if provided
            if pdf_buffer:
                pdf_attachment = MIMEApplication(pdf_buffer)
                pdf_attachment.add_header(
                    'Content-Disposition', 
                    'attachment', 
                    filename=f'weekly_report_{child_name}.pdf'
                )
                msg.attach(pdf_attachment)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Weekly report sent to {parent_email} for {child_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def _create_report_html(self, child_name: str, report_data: Dict[str, Any]) -> str:
        """Create HTML email body for the report."""
        summary = report_data.get('summary', {})
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #667eea; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .summary {{ background-color: #f4f4f4; padding: 15px; margin: 20px 0; border-radius: 10px; }}
                .metric {{ display: inline-block; margin: 10px 20px; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #667eea; }}
                .metric-label {{ font-size: 14px; color: #666; }}
                .recommendations {{ background-color: #e8f5e9; padding: 15px; margin: 20px 0; border-radius: 10px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Weekly Progress Report</h1>
                <p>{child_name} | {report_data.get('report_date', '')}</p>
            </div>
            
            <div class="content">
                <p>Dear Parent,</p>
                <p>Here's {child_name}'s learning progress for the week:</p>
                
                <div class="summary">
                    <h2>Summary</h2>
                    <div class="metric">
                        <div class="metric-value">{summary.get('total_questions', 0)}</div>
                        <div class="metric-label">Questions Answered</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{summary.get('average_accuracy', 0)}%</div>
                        <div class="metric-label">Average Accuracy</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{summary.get('study_days', 0)}/7</div>
                        <div class="metric-label">Study Days</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{summary.get('current_streak', 0)}</div>
                        <div class="metric-label">Day Streak</div>
                    </div>
                </div>
                
                <div class="recommendations">
                    <h3>Recommendations</h3>
                    <ul>
        """
        
        # Add recommendations
        progress = report_data.get('progress', {})
        for rec in progress.get('recommendations', []):
            html += f"<li>{rec}</li>"
        
        html += """
                    </ul>
                </div>
                
                <p>For detailed progress information, please log in to the parent portal or see the attached PDF report.</p>
                
                <p>Best regards,<br>The ISEE Tutor Team</p>
            </div>
            
            <div class="footer">
                <p>This is an automated email from ISEE Tutor. Please do not reply to this email.</p>
                <p>© 2024 ISEE Tutor. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    async def send_encouragement_message(
        self,
        parent_email: str,
        child_name: str,
        message: str,
        from_name: str
    ) -> bool:
        """Send an encouragement message notification to parent."""
        if not self.enabled:
            logger.warning("Email service not configured. Skipping email.")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = parent_email
            msg['Subject'] = f"New Encouragement Message for {child_name}"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #667eea;">New Encouragement Message</h2>
                <p>{from_name} sent an encouragement message to {child_name}:</p>
                <div style="background-color: #f4f4f4; padding: 15px; border-radius: 10px; margin: 20px 0;">
                    <p style="font-style: italic; font-size: 16px;">"{message}"</p>
                </div>
                <p>Log in to the parent portal to send your own message!</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send encouragement email: {str(e)}")
            return False


# Singleton instance
email_service = EmailService()