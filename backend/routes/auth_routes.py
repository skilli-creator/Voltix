# backend/routes/auth_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, decode_token
from flask_jwt_extended.exceptions import JWTExtendedException
from models.database import db
from services.email_service import EmailService
import re
from datetime import datetime, timedelta
import bcrypt

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email)

def validate_phone(phone):
    digits = re.sub(r'\D', '', phone)
    return 8 <= len(digits) <= 15


# ==================== SIGNUP ====================

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not all([first_name, last_name, phone, email, password]):
        return jsonify({'error': 'All fields required'}), 400
    
    if not validate_email(email):
        return jsonify({'error': 'Invalid email'}), 400
    
    if not validate_phone(phone):
        return jsonify({'error': 'Invalid phone number'}), 400
    
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    
    if db.get_user_by_email(email):
        return jsonify({'error': 'Email already registered'}), 400
    
    if db.get_user_by_phone(phone):
        return jsonify({'error': 'Phone number already registered'}), 400
    
    user_id = db.create_user(first_name, last_name, phone, email, password)
    
    if not user_id:
        return jsonify({'error': 'Registration failed'}), 500
    
    code = db.generate_code()
    db.save_verification_code(user_id, code)
    EmailService.send_verification_email(email, code)
    
    return jsonify({
        'message': 'Account created! Check your email for verification code.',
        'user_id': user_id
    }), 201


# ==================== EMAIL VERIFICATION ====================

@auth_bp.route('/verify', methods=['POST'])
def verify():
    data = request.json
    user_id = data.get('user_id')
    code = data.get('code')
    
    if not user_id or not code:
        return jsonify({'error': 'User ID and code required'}), 400
    
    if db.verify_code(user_id, code):
        db.update_email_verified(user_id)
        return jsonify({'message': 'Email verified successfully!'}), 200
    else:
        return jsonify({'error': 'Invalid or expired code'}), 400


# ==================== LOGIN ====================

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    password = data.get('password', '')
    
    if not password:
        return jsonify({'error': 'Password required'}), 400
    
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    
    user = None
    
    if email:
        user = db.get_user_by_email(email)
    elif phone:
        if not validate_phone(phone):
            return jsonify({'error': 'Invalid phone number format'}), 400
        user = db.get_user_by_phone(phone)
    else:
        return jsonify({'error': 'Email or phone number required'}), 400
    
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user.get('email_verified', False):
        return jsonify({'error': 'Please verify your email first'}), 403
    
    db.update_last_login(user['id'])
    
    # FIX: Convert user_id to string to avoid "Subject must be a string" error
    token = create_access_token(identity=str(user['id']))
    
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': {
            'id': user['id'],
            'email': user['email'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'phone': user.get('phone', '')
        }
    }), 200


# ==================== FORGOT PASSWORD ====================

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'error': 'Email address required'}), 400
    
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    user = db.get_user_by_email(email)
    if not user:
        return jsonify({'error': 'No account found with this email'}), 404
    
    reset_code = db.generate_code()
    expires_at = datetime.now() + timedelta(minutes=10)
    
    conn = db.get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET reset_code = %s, reset_code_expires_at = %s WHERE id = %s
        """, (reset_code, expires_at, user['id']))
        conn.commit()
        cursor.close()
        conn.close()
    
    EmailService.send_password_reset_email(email, reset_code)
    
    return jsonify({
        'message': 'Reset code sent to your email',
        'email': email
    }), 200


@auth_bp.route('/verify-reset-code', methods=['POST'])
def verify_reset_code():
    data = request.json
    email = data.get('email', '').strip().lower()
    code = data.get('code', '').strip()
    
    if not email or not code:
        return jsonify({'error': 'Email and code required'}), 400
    
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    user = db.get_user_by_email(email)
    if not user:
        return jsonify({'error': 'No account found with this email'}), 404
    
    conn = db.get_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT reset_code, reset_code_expires_at FROM users WHERE id = %s
    """, (user['id'],))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not result or not result['reset_code']:
        return jsonify({'error': 'No reset request found. Please request a new code.'}), 400
    
    if result['reset_code'] != code:
        return jsonify({'error': 'Invalid verification code'}), 400
    
    if datetime.now() > result['reset_code_expires_at']:
        return jsonify({'error': 'Code has expired. Please request a new one.'}), 400
    
    # FIX: Convert user_id to string for reset token as well
    reset_token = create_access_token(
        identity=str(user['id']),  # Convert to string!
        additional_claims={'reset_mode': True},
        expires_delta=timedelta(minutes=5)
    )
    
    return jsonify({
        'message': 'Code verified successfully',
        'reset_token': reset_token
    }), 200


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    reset_token = data.get('reset_token', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')
    
    print(f"DEBUG: reset_token received: {reset_token[:50] if reset_token else 'None'}...")
    
    if not reset_token or not new_password or not confirm_password:
        return jsonify({'error': 'All fields required'}), 400
    
    if new_password != confirm_password:
        return jsonify({'error': 'Passwords do not match'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    try:
        decoded = decode_token(reset_token)
        print(f"DEBUG: decoded token: {decoded}")
        user_id = decoded['sub']
        
        if not decoded.get('reset_mode'):
            return jsonify({'error': 'Invalid reset token type'}), 400
            
    except JWTExtendedException as e:
        print(f"DEBUG: JWT Error: {e}")
        return jsonify({'error': 'Invalid or expired reset token'}), 400
    except Exception as e:
        print(f"DEBUG: Other error: {e}")
        return jsonify({'error': 'Invalid or expired reset token'}), 400
    
    user = db.get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    
    conn = db.get_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET password_hash = %s, reset_code = NULL, reset_code_expires_at = NULL WHERE id = %s
    """, (new_password_hash.decode('utf-8'), user_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({
        'message': 'Password reset successful! Please login with your new password.'
    }), 200