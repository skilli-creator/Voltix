# backend/websocket_manager.py
import threading
import json
from websocket import create_connection
from datetime import datetime

class DerivWSManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.ws = None
        self.authorized = False
        self.current_token = None
        self.current_loginid = None
        self.current_balance = None
        self.current_accounts = []
        self.reconnect_lock = threading.Lock()
        self.deriv_ws_url = "wss://ws.derivws.com/websockets/v3?app_id=16929"
        
    def get_connection(self):
        """Get or create the SINGLE WebSocket connection"""
        if self.ws is None:
            with self.reconnect_lock:
                if self.ws is None:
                    try:
                        self.ws = create_connection(self.deriv_ws_url)
                        print(f"[{datetime.now()}] ✅ Global WebSocket created")
                    except Exception as e:
                        print(f"[{datetime.now()}] ❌ Failed to create WebSocket: {e}")
                        raise
        return self.ws
    
    def authorize(self, token):
        """Authorize once - uses existing or new connection"""
        ws = self.get_connection()
        
        # If already authorized with same token, return cached data
        if self.authorized and self.current_token == token:
            return {
                "status": "success",
                "msg_type": "authorize",
                "loginid": self.current_loginid,
                "balance": self.current_balance,
                "account_list": self.current_accounts
            }
        
        try:
            auth_request = {"authorize": token}
            ws.send(json.dumps(auth_request))
            response = json.loads(ws.recv())
            
            print(f"[{datetime.now()}] 📨 Auth Response: {response.get('msg_type')}")
            
            if response.get('msg_type') == 'authorize':
                self.authorized = True
                self.current_token = token
                self.current_loginid = response.get('authorize', {}).get('loginid')
                self.current_balance = response.get('authorize', {}).get('balance')
                self.current_accounts = response.get('authorize', {}).get('account_list', [])
                
                print(f"[{datetime.now()}] ✅ Authorized as {self.current_loginid}")
                print(f"[{datetime.now()}] 📊 Balance: {self.current_balance} USD")
                print(f"[{datetime.now()}] 📋 Found {len(self.current_accounts)} accounts")
                
                return {
                    "status": "success",
                    "msg_type": "authorize",
                    "loginid": self.current_loginid,
                    "balance": self.current_balance,
                    "account_list": self.current_accounts
                }
            else:
                print(f"[{datetime.now()}] ❌ Authorization failed: {response}")
                return {"status": "error", "message": "Authorization failed"}
                
        except Exception as e:
            print(f"[{datetime.now()}] ❌ Authorization error: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_balance(self, loginid=None):
        """Get balance for specific account - NO re-authorization"""
        if not self.authorized:
            return {"error": "Not authorized"}
        
        ws = self.get_connection()
        
        # ✅ Send ONLY balance request
        request = {"balance": 1}
        if loginid:
            request["loginid"] = loginid
        
        try:
            ws.send(json.dumps(request))
            response = json.loads(ws.recv())
            
            print(f"[{datetime.now()}] 📨 Balance Response: {response.get('msg_type')}")
            
            if response.get('msg_type') == 'balance':
                return {
                    "balance": response.get('balance', {}).get('balance', 0),
                    "currency": response.get('balance', {}).get('currency', 'USD'),
                    "loginid": response.get('balance', {}).get('loginid')
                }
            else:
                print(f"[{datetime.now()}] ⚠️ Unexpected response: {response.get('msg_type')}")
                return {"balance": 0, "currency": "USD", "error": "Invalid response"}
                
        except Exception as e:
            print(f"[{datetime.now()}] ❌ Balance error: {e}")
            return {"balance": 0, "currency": "USD", "error": str(e)}
    
    def get_accounts(self):
        """Get all accounts from cached data"""
        if not self.authorized:
            return []
        
        # Return cached accounts from authorization
        return self.current_accounts
    
    def send_request(self, request, wait_for_response=True):
        """Send custom request using existing connection"""
        if not self.authorized:
            return {"error": "Not authorized"}
        
        ws = self.get_connection()
        
        try:
            ws.send(json.dumps(request))
            print(f"[{datetime.now()}] 📤 Sent: {request.get('msg_type', 'custom')}")
            
            if wait_for_response:
                response = json.loads(ws.recv())
                print(f"[{datetime.now()}] 📥 Received: {response.get('msg_type')}")
                return response
            return {"status": "sent"}
            
        except Exception as e:
            print(f"[{datetime.now()}] ❌ Send error: {e}")
            return {"error": str(e)}
    
    def place_trade(self, trade_request):
        """Place a trade using existing connection"""
        return self.send_request(trade_request)
    
    def get_active_contracts(self):
        """Get active contracts"""
        request = {"portfolio": 1}
        return self.send_request(request)
    
    def get_trade_history(self, limit=50):
        """Get trade history"""
        request = {"profit_table": 1, "limit": limit}
        return self.send_request(request)
    
    def disconnect(self):
        """Close WebSocket connection"""
        if self.ws:
            try:
                self.ws.close()
                print(f"[{datetime.now()}] 🔌 WebSocket disconnected")
            except:
                pass
            finally:
                self.ws = None
                self.authorized = False
                self.current_token = None
                self.current_loginid = None
                self.current_balance = None
                self.current_accounts = []

# Create global singleton instance
deriv_ws = DerivWSManager()