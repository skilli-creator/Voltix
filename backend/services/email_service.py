# backend/services/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

class EmailService:
    
    @staticmethod
    def send_verification_email(to_email, code):
        """Send email verification code to new user"""
        try:
            msg = MIMEMultipart()
            msg['From'] = Config.EMAIL_USER
            msg['To'] = to_email
            msg['Subject'] = 'Verify Your Voltix Account'
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Voltix | Verify your account</title>
            <style>
                * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                }}
                body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                background-color: #0a0f1e;
                padding: 24px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                }}
                .container {{
                max-width: 600px;
                width: 100%;
                margin: 0 auto;
                background: #10172e;
                border-radius: 32px;
                padding: 44px 40px 40px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8), 0 0 0 1px rgba(34, 197, 94, 0.15);
                border: 1px solid rgba(34, 197, 94, 0.08);
                }}
                .header {{
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 28px;
                }}
                .brand-icon {{
                background: #1e293b;
                width: 48px;
                height: 48px;
                border-radius: 16px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 28px;
                font-weight: 600;
                color: #22c55e;
                border: 1px solid rgba(34, 197, 94, 0.2);
                box-shadow: 0 0 20px rgba(34, 197, 94, 0.08);
                }}
                .brand-text {{
                font-size: 26px;
                font-weight: 700;
                letter-spacing: -0.5px;
                color: #f0f4ff;
                }}
                .brand-text span {{
                color: #22c55e;
                }}
                .badge {{
                background: rgba(34, 197, 94, 0.12);
                color: #22c55e;
                font-size: 12px;
                font-weight: 600;
                padding: 4px 14px;
                border-radius: 30px;
                margin-left: 8px;
                letter-spacing: 0.3px;
                border: 1px solid rgba(34, 197, 94, 0.15);
                }}
                h3 {{
                color: #f0f4ff;
                font-size: 24px;
                font-weight: 600;
                margin-bottom: 8px;
                letter-spacing: -0.3px;
                }}
                .sub-head {{
                color: #9aa4c8;
                font-size: 16px;
                line-height: 1.5;
                margin-bottom: 28px;
                font-weight: 400;
                border-left: 3px solid #22c55e;
                padding-left: 16px;
                background: rgba(34, 197, 94, 0.02);
                }}
                .code-box {{
                background: #0f1629;
                border-radius: 20px;
                padding: 28px 20px;
                text-align: center;
                border: 1px solid #28324e;
                margin: 24px 0 20px;
                box-shadow: inset 0 4px 12px rgba(0, 0, 0, 0.4);
                position: relative;
                }}
                .code-box::after {{
                content: '';
                position: absolute;
                inset: 0;
                border-radius: 20px;
                padding: 1px;
                background: linear-gradient(135deg, rgba(34, 197, 94, 0.25), transparent 60%);
                -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
                -webkit-mask-composite: xor;
                mask-composite: exclude;
                pointer-events: none;
                }}
                .code-label {{
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 2px;
                color: #6b7ba3;
                margin-bottom: 8px;
                font-weight: 500;
                }}
                .code {{
                font-size: 46px;
                letter-spacing: 14px;
                font-weight: 700;
                color: #22c55e;
                background: #0b1225;
                padding: 12px 4px;
                border-radius: 16px;
                display: inline-block;
                font-family: 'SF Mono', 'Menlo', monospace;
                text-shadow: 0 0 30px rgba(34, 197, 94, 0.15);
                }}
                .expiry {{
                color: #7b89b0;
                font-size: 14px;
                margin: 16px 0 6px;
                }}
                .expiry strong {{
                color: #f0f4ff;
                font-weight: 600;
                }}
                .divider {{
                border: 0;
                height: 1px;
                background: linear-gradient(90deg, transparent, #28324e, transparent);
                margin: 28px 0 24px;
                }}
                .trading-highlight {{
                background: #0c142b;
                border-radius: 18px;
                padding: 20px 22px;
                margin: 20px 0 26px;
                border-left: 4px solid #22c55e;
                border: 1px solid #1d2742;
                }}
                .trading-highlight p {{
                color: #bcc6e6;
                font-size: 15px;
                line-height: 1.6;
                margin-bottom: 6px;
                }}
                .trading-highlight strong {{
                color: #eef3ff;
                }}
                .feature-grid {{
                display: flex;
                flex-wrap: wrap;
                gap: 12px 20px;
                margin-top: 14px;
                }}
                .feature-item {{
                display: flex;
                align-items: center;
                gap: 8px;
                color: #bcc6e6;
                font-size: 14px;
                }}
                .feature-item::before {{
                content: "✓";
                color: #22c55e;
                font-weight: 700;
                font-size: 16px;
                }}
                .support-box {{
                background: #0f182f;
                border-radius: 20px;
                padding: 20px 24px 24px;
                margin-top: 24px;
                border: 1px solid #28324e;
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                justify-content: space-between;
                gap: 16px;
                }}
                .support-text {{
                color: #c8d0ec;
                font-size: 15px;
                }}
                .support-text strong {{
                color: #f0f4ff;
                font-weight: 600;
                }}
                .whatsapp-btn {{
                background: #25D366;
                color: #0a0f1e !important;
                text-decoration: none;
                font-weight: 700;
                font-size: 15px;
                padding: 12px 28px;
                border-radius: 60px;
                display: inline-flex;
                align-items: center;
                gap: 10px;
                letter-spacing: 0.3px;
                transition: all 0.2s;
                box-shadow: 0 4px 16px rgba(37, 211, 102, 0.25);
                border: 1px solid rgba(255, 255, 255, 0.08);
                }}
                .whatsapp-btn:hover {{
                background: #20b85f;
                transform: scale(1.02);
                box-shadow: 0 6px 24px rgba(37, 211, 102, 0.35);
                }}
                .whatsapp-btn svg {{
                width: 20px;
                height: 20px;
                fill: currentColor;
                }}
                .footer {{
                margin-top: 32px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 10px;
                color: #4d5b7c;
                font-size: 13px;
                border-top: 1px solid #1a2340;
                padding-top: 22px;
                }}
                .footer a {{
                color: #6b7ba3;
                text-decoration: none;
                margin: 0 6px;
                transition: color 0.2s;
                }}
                .footer a:hover {{
                color: #22c55e;
                }}
                .footer span {{
                color: #3d4a6b;
                }}
                .security-note {{
                margin-top: 12px;
                font-size: 12px;
                color: #35415e;
                text-align: center;
                letter-spacing: 0.3px;
                }}
                @media (max-width: 520px) {{
                .container {{ padding: 28px 18px; }}
                .code {{ font-size: 32px; letter-spacing: 10px; }}
                .support-box {{ flex-direction: column; align-items: flex-start; }}
                .whatsapp-btn {{ width: 100%; justify-content: center; }}
                .brand-text {{ font-size: 22px; }}
                }}
            </style>
            </head>
            <body>
            <div class="container">
                <!-- header -->
                <div class="header">
                <div class="brand-icon">⚡</div>
                <div class="brand-text">Volt<span>ix</span></div>
                <span class="badge">AI trading</span>
                </div>

                <!-- main message -->
                <h3>🔐 Verify your email</h3>
                <div class="sub-head">
                Welcome to Voltix — one last step to activate your trading dashboard.
                </div>

                <!-- verification code -->
                <div class="code-box">
                <div class="code-label">verification code</div>
                <div class="code"><strong>{code}</strong></div>
                <div class="expiry">⏳ This code expires in <strong>10 minutes</strong> · for your security</div>
                </div>

                <!-- trading insights / pro content -->
                <div class="trading-highlight">
                <p style="font-weight: 500; color: #eef3ff;">📈 <strong>Start trading with institutional-grade tools</strong></p>
                <p>Voltix delivers real-time market data, AI-driven signals, and low-latency execution. Access 120+ crypto pairs, indices, and commodities — all from a single dashboard.</p>
                <div class="feature-grid">
                    <span class="feature-item">AI pattern recognition</span>
                    <span class="feature-item">0.01s order execution</span>
                    <span class="feature-item">24/7 market coverage</span>
                    <span class="feature-item">Portfolio analytics</span>
                </div>
                </div>

                <!-- support + whatsapp -->
                <div class="support-box">
                <div class="support-text">
                    <strong>📞 Need help?</strong> Our support team is available 24/7. <br>
                    Reach us directly on <strong>WhatsApp</strong> for instant assistance.
                </div>
                <a href="https://wa.me/254704182603?text=Hello%20Voltix%20support%20%7C%20verification%20help" 
                    class="whatsapp-btn" 
                    target="_blank" 
                    rel="noopener noreferrer">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                    <path d="M12.032 21.965c-1.821 0-3.585-.475-5.105-1.373l-3.608 1.18 1.21-3.517c-1.045-1.638-1.61-3.538-1.61-5.545 0-5.613 4.566-10.18 10.178-10.18 2.717 0 5.27 1.06 7.19 2.98 1.92 1.92 2.98 4.473 2.98 7.19 0 5.612-4.567 10.179-10.18 10.179h-.045zm5.61-6.038c-.307-.154-1.817-.897-2.098-1.002-.281-.105-.486-.156-.69.154-.205.31-.794.998-.974 1.203-.18.205-.36.23-.667.077-.308-.154-1.298-.478-2.472-1.526-.914-.815-1.532-1.822-1.711-2.13-.18-.308-.02-.474.135-.627.14-.14.307-.359.46-.538.154-.18.205-.308.307-.513.102-.205.051-.384-.026-.538-.077-.154-.69-1.664-.944-2.278-.247-.597-.5-.503-.69-.512-.179-.01-.385-.01-.59-.01-.205 0-.538.077-.82.384-.282.307-1.076 1.052-1.076 2.565s1.102 2.976 1.256 3.182c.154.205 2.17 3.313 5.257 4.347 2.79.936 3.404.733 4.018.674.614-.059 1.973-.806 2.25-1.586.277-.78.277-1.448.194-1.587-.083-.139-.307-.22-.614-.374z"/>
                    </svg>
                    Chat with support
                </a>
                </div>
                <!-- extra contact hint -->
                <p style="color: #5b6b91; font-size: 13px; margin-top: 12px; text-align: right; letter-spacing: 0.2px;">
                WhatsApp <strong style="color: #9aaacf;">0704 182 603</strong> · response within 2 min
                </p>

                <hr class="divider">

                <!-- footer -->
                <div class="footer">
                <span>© 2026 Voltix — AI Trading Platform</span>
                <span>
                    <a href="#">Privacy</a> · <a href="#">Terms</a> · <a href="#">Security</a>
                </span>
                </div>
                <div class="security-note">
                This email was sent to you as part of your Voltix account verification. If you didn't request this, ignore it.
                </div>
            </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            with smtplib.SMTP(Config.EMAIL_HOST, Config.EMAIL_PORT) as server:
                server.starttls()
                server.login(Config.EMAIL_USER, Config.EMAIL_PASS)
                server.send_message(msg)
            
            print(f"✅ Verification email sent to {to_email}")
            return True
        except Exception as e:
            print(f"Verification email error: {e}")
            return False

    @staticmethod
    def send_password_reset_email(to_email, code):
        """Send password reset code to user"""
        try:
            msg = MIMEMultipart()
            msg['From'] = Config.EMAIL_USER
            msg['To'] = to_email
            msg['Subject'] = '🔑 Voltix - Password Reset Code'
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }}
                    body {{
                        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
                        background-color: #0a0f1e;
                        padding: 24px;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                        margin: 0;
                    }}
                    .container {{
                        max-width: 600px;
                        width: 100%;
                        margin: 0 auto;
                        background: #10172e;
                        border-radius: 32px;
                        padding: 44px 40px 40px;
                        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8), 0 0 0 1px rgba(34, 197, 94, 0.15);
                        border: 1px solid rgba(34, 197, 94, 0.08);
                    }}
                    .header {{
                        display: flex;
                        align-items: center;
                        gap: 10px;
                        margin-bottom: 28px;
                    }}
                    .brand-icon {{
                        background: #1e293b;
                        width: 48px;
                        height: 48px;
                        border-radius: 16px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 28px;
                        font-weight: 600;
                        color: #22c55e;
                        border: 1px solid rgba(34, 197, 94, 0.2);
                    }}
                    .brand-text {{
                        font-size: 26px;
                        font-weight: 700;
                        letter-spacing: -0.5px;
                        color: #f0f4ff;
                    }}
                    .brand-text span {{
                        color: #22c55e;
                    }}
                    .badge {{
                        background: rgba(34, 197, 94, 0.12);
                        color: #22c55e;
                        font-size: 12px;
                        font-weight: 600;
                        padding: 4px 14px;
                        border-radius: 30px;
                        margin-left: 8px;
                        border: 1px solid rgba(34, 197, 94, 0.15);
                    }}
                    h3 {{
                        color: #f0f4ff;
                        font-size: 24px;
                        font-weight: 600;
                        margin-bottom: 8px;
                    }}
                    .sub-head {{
                        color: #9aa4c8;
                        font-size: 16px;
                        line-height: 1.5;
                        margin-bottom: 28px;
                        border-left: 3px solid #f59e0b;
                        padding-left: 16px;
                    }}
                    .code-box {{
                        background: #0f1629;
                        border-radius: 20px;
                        padding: 28px 20px;
                        text-align: center;
                        border: 1px solid #28324e;
                        margin: 24px 0 20px;
                        box-shadow: inset 0 4px 12px rgba(0, 0, 0, 0.4);
                    }}
                    .code-label {{
                        font-size: 12px;
                        text-transform: uppercase;
                        letter-spacing: 2px;
                        color: #6b7ba3;
                        margin-bottom: 8px;
                        font-weight: 500;
                    }}
                    .code {{
                        font-size: 46px;
                        letter-spacing: 14px;
                        font-weight: 700;
                        color: #f59e0b;
                        background: #0b1225;
                        padding: 12px 4px;
                        border-radius: 16px;
                        display: inline-block;
                        font-family: 'SF Mono', 'Menlo', monospace;
                        text-shadow: 0 0 30px rgba(245, 158, 11, 0.15);
                    }}
                    .expiry {{
                        color: #7b89b0;
                        font-size: 14px;
                        margin: 16px 0 6px;
                    }}
                    .expiry strong {{
                        color: #f0f4ff;
                        font-weight: 600;
                    }}
                    .warning-box {{
                        background: rgba(245, 158, 11, 0.08);
                        border: 1px solid rgba(245, 158, 11, 0.2);
                        border-radius: 14px;
                        padding: 16px 20px;
                        margin: 20px 0;
                        color: #fcd34d;
                        font-size: 14px;
                        display: flex;
                        align-items: center;
                        gap: 10px;
                    }}
                    .warning-box::before {{
                        content: "⚠️";
                        font-size: 18px;
                    }}
                    .divider {{
                        border: 0;
                        height: 1px;
                        background: linear-gradient(90deg, transparent, #28324e, transparent);
                        margin: 28px 0 24px;
                    }}
                    .footer {{
                        margin-top: 32px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        flex-wrap: wrap;
                        gap: 10px;
                        color: #4d5b7c;
                        font-size: 13px;
                        border-top: 1px solid #1a2340;
                        padding-top: 22px;
                    }}
                    .footer a {{
                        color: #6b7ba3;
                        text-decoration: none;
                        margin: 0 6px;
                        transition: color 0.2s;
                    }}
                    .footer a:hover {{
                        color: #f59e0b;
                    }}
                    .support-text {{
                        color: #c8d0ec;
                        font-size: 14px;
                        text-align: center;
                        margin-top: 16px;
                    }}
                    .support-text a {{
                        color: #25D366;
                        text-decoration: none;
                        font-weight: 600;
                    }}
                    @media (max-width: 520px) {{
                        .container {{ padding: 28px 18px; }}
                        .code {{ font-size: 32px; letter-spacing: 10px; }}
                        .brand-text {{ font-size: 22px; }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="brand-icon">⚡</div>
                        <div class="brand-text">Volt<span>ix</span></div>
                        <span class="badge">AI trading</span>
                    </div>

                    <h3>🔑 Password Reset Request</h3>
                    <div class="sub-head">
                        You requested to reset your password. Use the code below to proceed.
                    </div>

                    <div class="code-box">
                        <div class="code-label">reset code</div>
                        <div class="code"><strong>{code}</strong></div>
                        <div class="expiry">⏳ This code expires in <strong>10 minutes</strong></div>
                    </div>

                    <div class="warning-box">
                        If you did not request this, please ignore this email or contact support immediately.
                    </div>

                    <hr class="divider">

                    <div class="footer">
                        <span>© 2026 Voltix — AI Trading Platform</span>
                        <span>
                            <a href="#">Privacy</a> · <a href="#">Terms</a> · <a href="#">Security</a>
                        </span>
                    </div>
                    <div class="support-text">
                        📞 Need help? Reach us on <a href="https://wa.me/254704182603?text=Hello%20Voltix%20support%20%7C%20password%20reset">WhatsApp 0704 182 603</a>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            with smtplib.SMTP(Config.EMAIL_HOST, Config.EMAIL_PORT) as server:
                server.starttls()
                server.login(Config.EMAIL_USER, Config.EMAIL_PASS)
                server.send_message(msg)
            
            print(f"✅ Verification email sent to {to_email}")
            return True
        except Exception as e:
            print(f"Verification email error: {e}")
            return False
    
    @staticmethod
    def send_password_reset_email(to_email, code):
        """Send password reset code to user"""
        try:
            msg = MIMEMultipart()
            msg['From'] = Config.EMAIL_USER
            msg['To'] = to_email
            msg['Subject'] = 'Voltix - Password Reset Code'
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; background-color: #0a1428; padding: 20px; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: #0f1730; border-radius: 20px; padding: 40px; }}
                    h2 {{ color: #22c55e; }}
                    .code {{ font-size: 36px; letter-spacing: 8px; background: #1e293b; padding: 20px; border-radius: 12px; text-align: center; color: #22c55e; }}
                    .warning {{ color: #f59e0b; font-size: 12px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>⚡ Voltix</h2>
                    <h3>Password Reset Request</h3>
                    <p>You requested to reset your password. Use the code below to proceed:</p>
                    <div class="code"><strong>{code}</strong></div>
                    <p>This code expires in <strong>10 minutes</strong>.</p>
                    <p class="warning">⚠️ If you did not request this, please ignore this email or contact support.</p>
                    <hr>
                    <p style="color: #666; font-size: 12px;">© 2026 Voltix — AI Trading Platform</p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            with smtplib.SMTP(Config.EMAIL_HOST, Config.EMAIL_PORT) as server:
                server.starttls()
                server.login(Config.EMAIL_USER, Config.EMAIL_PASS)
                server.send_message(msg)
            
            print(f"✅ Password reset email sent to {to_email}")
            return True
        except Exception as e:
            print(f"Password reset email error: {e}")
            return False
    
    @staticmethod
    def send_admin_notification(subject, body):
        """Send notification to admin email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = Config.EMAIL_USER
            msg['To'] = Config.ADMIN_EMAIL
            msg['Subject'] = f"[Voltix Admin] {subject}"
            
            html = f"""
            <div style="font-family: Arial, sans-serif;">
                <h2>⚡ Voltix Admin Notification</h2>
                <hr>
                <pre style="background: #f0f0f0; padding: 15px; border-radius: 8px;">{body}</pre>
                <hr>
                <p style="color: #666; font-size: 12px;">Sent at: {__import__('datetime').datetime.now()}</p>
            </div>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            with smtplib.SMTP(Config.EMAIL_HOST, Config.EMAIL_PORT) as server:
                server.starttls()
                server.login(Config.EMAIL_USER, Config.EMAIL_PASS)
                server.send_message(msg)
            
            print(f"✅ Admin notification sent to {Config.ADMIN_EMAIL}")
            return True
        except Exception as e:
            print(f"Admin notification error: {e}")
            return False