# backend/routes/deriv_routes.py
from flask import Blueprint, request, jsonify, session
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.database import db
from services.deriv_service import DerivService
from websocket_manager import deriv_ws  # Import the singleton
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

deriv_bp = Blueprint('deriv', __name__)


@deriv_bp.route('/connect', methods=['POST'])
@jwt_required()
def connect_deriv():
    """Connect Deriv account using API token - SINGLE CONNECTION"""
    user_id = get_jwt_identity()
    data = request.json
    
    api_token = data.get('api_token', '').strip()
    account_type = data.get('account_type', 'Demo')
    
    if not api_token:
        return jsonify({'error': 'API token required'}), 400
    
    # Use the singleton WebSocket manager
    result = deriv_ws.authorize(api_token)
    
    if result.get('status') != 'success':
        return jsonify({'error': result.get('message', 'Failed to authorize')}), 400
    
    # Get account info from result
    loginid = result.get('loginid')
    balance = result.get('balance', 0)
    account_list = result.get('account_list', [])
    
    # Find current account in list
    current_account = None
    for acc in account_list:
        if acc.get('loginid') == loginid:
            current_account = acc
            break
    
    # Determine account type
    if loginid and loginid.startswith('VRTC'):
        detected_account_type = 'Demo'
    elif loginid and loginid.startswith('CR'):
        detected_account_type = 'Real'
    else:
        detected_account_type = account_type
    
    # Save to database
    conn = db.get_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id FROM deriv_accounts WHERE user_id = %s AND account_id = %s
        """, (user_id, loginid))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
                UPDATE deriv_accounts 
                SET token = %s, balance = %s, currency = %s, account_type = %s, 
                    email = %s, last_sync_at = NOW(), is_active = 1
                WHERE user_id = %s AND account_id = %s
            """, (api_token.encode(), balance, 'USD', detected_account_type, 
                  current_account.get('email', '') if current_account else '', 
                  user_id, loginid))
        else:
            cursor.execute("""
                INSERT INTO deriv_accounts (user_id, account_id, email, token, balance, currency, account_type, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
            """, (user_id, loginid, current_account.get('email', '') if current_account else '', 
                  api_token.encode(), balance, 'USD', detected_account_type))
        
        conn.commit()
        
        # Store in Flask session for this request
        session['deriv_authorized'] = True
        session['deriv_loginid'] = loginid
        
    except Exception as e:
        logger.error(f"Database error: {e}")
        conn.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()
    
    return jsonify({
        'message': 'Deriv account connected successfully',
        'account': {
            'account_id': loginid,
            'balance': balance,
            'currency': 'USD',
            'account_type': detected_account_type,
            'email': current_account.get('email', '') if current_account else ''
        }
    }), 200


@deriv_bp.route('/balance', methods=['GET'])
@jwt_required()
def get_balance():
    """Get current balance using EXISTING WebSocket connection"""
    user_id = get_jwt_identity()
    
    # Check if we have an active Deriv connection
    if not deriv_ws.authorized:
        return jsonify({'error': 'Deriv not connected. Please connect first.'}), 401
    
    # Get active account from database
    conn = db.get_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT account_id, account_type FROM deriv_accounts 
        WHERE user_id = %s AND is_active = 1
    """, (user_id,))
    account = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not account:
        return jsonify({'error': 'No Deriv account connected'}), 404
    
    active_account = account['account_id']
    
    # ✅ CORRECT: Use existing connection, NO new authorize
    balance_data = deriv_ws.get_balance(active_account)
    
    if 'error' in balance_data:
        return jsonify({'error': balance_data['error']}), 500
    
    # Update balance in database
    conn2 = db.get_connection()
    if conn2:
        cursor2 = conn2.cursor()
        cursor2.execute("""
            UPDATE deriv_accounts SET balance = %s, last_sync_at = NOW() 
            WHERE user_id = %s AND account_id = %s
        """, (balance_data['balance'], user_id, active_account))
        conn2.commit()
        cursor2.close()
        conn2.close()
    
    account_type = 'Demo' if active_account and active_account.startswith('VRTC') else 'Real'
    
    return jsonify({
        'balance': balance_data['balance'],
        'currency': balance_data['currency'],
        'account_id': active_account,
        'account_type': account_type
    }), 200


@deriv_bp.route('/accounts', methods=['GET'])
@jwt_required()
def get_accounts():
    """Get all accounts using cached data from WebSocket"""
    user_id = get_jwt_identity()
    
    # Check if we have an active Deriv connection
    if not deriv_ws.authorized:
        return jsonify({'error': 'Deriv not connected. Please connect first.'}), 401
    
    # Get cached accounts from WebSocket manager
    accounts = deriv_ws.current_accounts
    
    if not accounts:
        return jsonify({'error': 'No accounts found'}), 404
    
    # Format accounts for response
    formatted_accounts = []
    for acc in accounts:
        if acc.get('account_category') == 'trading':
            formatted_accounts.append({
                'account_id': acc.get('loginid'),
                'account_type': 'Demo' if acc.get('is_virtual') else 'Real',
                'balance': acc.get('balance', 0),
                'currency': acc.get('currency', 'USD'),
                'is_virtual': acc.get('is_virtual', 1)
            })
    
    # Get currently active account from database
    conn = db.get_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT account_id FROM deriv_accounts 
            WHERE user_id = %s AND is_active = 1
        """, (user_id,))
        current = cursor.fetchone()
        cursor.close()
        conn.close()
        current_account = current['account_id'] if current else None
    else:
        current_account = None
    
    return jsonify({
        'accounts': formatted_accounts,
        'current_account': current_account
    }), 200


@deriv_bp.route('/switch-account', methods=['POST'])
@jwt_required()
def switch_account():
    """Switch to a different Deriv account - NO NEW WEBSOCKET CONNECTION"""
    user_id = get_jwt_identity()
    data = request.json
    
    new_account_id = data.get('loginid')
    account_type = data.get('account_type', 'Demo')
    
    if not new_account_id:
        return jsonify({'error': 'Account loginid required'}), 400
    
    # ✅ FIXED: Just update the database and session - NO API call needed
    conn = db.get_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    cursor = conn.cursor()
    try:
        # Update database with new active account
        cursor.execute("""
            UPDATE deriv_accounts 
            SET account_id = %s, account_type = %s, is_active = 1
            WHERE user_id = %s
        """, (new_account_id, account_type, user_id))
        
        conn.commit()
        
        # Update session
        session['deriv_loginid'] = new_account_id
        
        # Get balance for new account using existing WebSocket
        balance_data = deriv_ws.get_balance(new_account_id)
        
        # Update balance in database
        if 'balance' in balance_data:
            cursor.execute("""
                UPDATE deriv_accounts SET balance = %s WHERE user_id = %s AND account_id = %s
            """, (balance_data['balance'], user_id, new_account_id))
            conn.commit()
        
        logger.info(f"[{datetime.now()}] 🔄 Switched to account: {new_account_id}")
        
        return jsonify({
            'message': f'Switched to account: {new_account_id}',
            'account_id': new_account_id,
            'account_type': account_type,
            'balance': balance_data.get('balance', 0),
            'currency': balance_data.get('currency', 'USD')
        }), 200
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Switch account error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@deriv_bp.route('/place-trade', methods=['POST'])
@jwt_required()
def place_trade():
    """Place a manual trade using existing WebSocket connection"""
    user_id = get_jwt_identity()
    data = request.json
    
    symbol = data.get('symbol', '')
    direction = data.get('direction', '')
    amount = data.get('amount', 0)
    duration = data.get('duration', 1)
    duration_unit = data.get('duration_unit', 't')
    
    if not symbol or not direction or not amount:
        return jsonify({'error': 'Symbol, direction, and amount required'}), 400
    
    if amount < 1.50:
        return jsonify({'error': 'Minimum stake is $1.50'}), 400
    
    # Check if connected
    if not deriv_ws.authorized:
        return jsonify({'error': 'Deriv not connected'}), 401
    
    # Get active account
    conn = db.get_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT account_id FROM deriv_accounts 
        WHERE user_id = %s AND is_active = 1
    """, (user_id,))
    account = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not account:
        return jsonify({'error': 'No active account found'}), 404
    
    # Place trade using DerivService (this should be modified to use the WebSocket)
    trade_type = 'CALL' if direction.lower() == 'rise' else 'PUT'
    
    # For now, keep using DerivService but ensure it doesn't create new connection
    # You'll need to modify DerivService to use the singleton WebSocket
    success, result = DerivService.place_trade(
        api_token=deriv_ws.current_token,  # Use token from singleton
        symbol=symbol,
        trade_type=trade_type,
        amount=amount,
        duration=duration,
        duration_unit=duration_unit
    )
    
    if not success:
        return jsonify({'error': result}), 500
    
    logger.info(f"Trade placed: {direction} on {symbol} for ${amount}")
    
    return jsonify({
        'message': 'Trade placed successfully',
        'trade': result
    }), 200


@deriv_bp.route('/disconnect', methods=['POST'])
@jwt_required()
def disconnect_deriv():
    """Disconnect Deriv account and close WebSocket"""
    user_id = get_jwt_identity()
    
    # Close WebSocket connection
    deriv_ws.disconnect()
    
    # Update database
    conn = db.get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE deriv_accounts SET is_active = 0 WHERE user_id = %s
        """, (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
    
    # Clear session
    session.clear()
    
    return jsonify({'message': 'Deriv account disconnected'}), 200


@deriv_bp.route('/status', methods=['GET'])
@jwt_required()
def deriv_status():
    """Get current Deriv connection status"""
    return jsonify({
        'connected': deriv_ws.authorized,
        'active_account': session.get('deriv_loginid'),
        'websocket_active': deriv_ws.ws is not None
    }), 200


# Keep other endpoints (active-contracts, trade-history, profit-loss, test-connect)
# as they were, but they should be modified to use the singleton WebSocket

@deriv_bp.route('/active-contracts', methods=['GET'])
@jwt_required()
def get_active_contracts():
    """Get all active contracts (open trades)"""
    user_id = get_jwt_identity()
    
    if not deriv_ws.authorized:
        return jsonify({'error': 'Deriv not connected'}), 401
    
    conn = db.get_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT account_id FROM deriv_accounts WHERE user_id = %s AND is_active = 1
    """, (user_id,))
    account = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not account:
        return jsonify({'error': 'No active account found'}), 404
    
    # Use DerivService with singleton token
    success, contracts = DerivService.get_active_contracts(deriv_ws.current_token)
    
    if not success:
        return jsonify({'error': contracts}), 500
    
    return jsonify({
        'contracts': contracts,
        'count': len(contracts)
    }), 200


@deriv_bp.route('/trade-history', methods=['GET'])
@jwt_required()
def get_trade_history():
    """Get trade history from Deriv API"""
    user_id = get_jwt_identity()
    
    if not deriv_ws.authorized:
        return jsonify({'error': 'Deriv not connected'}), 401
    
    limit = request.args.get('limit', 50, type=int)
    
    success, history = DerivService.get_trade_history(deriv_ws.current_token, limit)
    
    if not success:
        return jsonify({'error': history}), 500
    
    return jsonify({
        'history': history,
        'count': len(history)
    }), 200


@deriv_bp.route('/profit-loss', methods=['GET'])
@jwt_required()
def get_profit_loss():
    """Get profit/loss summary"""
    user_id = get_jwt_identity()
    
    if not deriv_ws.authorized:
        return jsonify({'error': 'Deriv not connected'}), 401
    
    success, history = DerivService.get_trade_history(deriv_ws.current_token, 200)
    
    if not success:
        return jsonify({'error': history}), 500
    
    wins = [t for t in history if t.get('profit', 0) > 0]
    losses = [t for t in history if t.get('profit', 0) < 0]
    total_profit = sum(t.get('profit', 0) for t in wins)
    total_loss = abs(sum(t.get('profit', 0) for t in losses))
    
    return jsonify({
        'total_trades': len(history),
        'wins': len(wins),
        'losses': len(losses),
        'total_profit': total_profit,
        'total_loss': total_loss,
        'net_profit': total_profit - total_loss
    }), 200


@deriv_bp.route('/test-connect', methods=['POST'])
def test_connect():
    """Test Deriv connection without JWT (for testing only)"""
    data = request.json
    api_token = data.get('api_token', '').strip()
    account_type = data.get('account_type', 'Demo')
    
    if not api_token:
        return jsonify({'error': 'API token required'}), 400
    
    logger.info(f"Testing Deriv connection with token: {api_token[:20]}...")
    
    # Use a temporary connection for testing
    from websocket_manager import DerivWSManager
    test_ws = DerivWSManager()
    result = test_ws.authorize(api_token)
    
    if result.get('status') != 'success':
        return jsonify({'error': result.get('message', 'Failed to authorize')}), 400
    
    loginid = result.get('loginid')
    balance = result.get('balance', 0)
    
    if loginid and loginid.startswith('VRTC'):
        acc_type = 'Demo'
    elif loginid and loginid.startswith('CR'):
        acc_type = 'Real'
    else:
        acc_type = account_type
    
    # Clean up test connection
    test_ws.disconnect()
    
    return jsonify({
        'message': 'Deriv account connected successfully',
        'account': {
            'account_id': loginid,
            'balance': balance,
            'currency': 'USD',
            'account_type': acc_type,
            'email': '',
            'trading_account_id': loginid
        }
    }), 200