#!/usr/bin/env python3
"""
Smart Fyers MCP Server with Complete Trading Tools
"""

import os
import sys
import logging
import urllib.parse
import webbrowser
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional

# Disable logging
logging.disable(logging.CRITICAL)
import warnings
warnings.filterwarnings("ignore")

def load_env_file():
    """Load environment variables from .env file."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
        except Exception as e:
            print(f"Warning: Could not load .env file: {e}")

load_env_file()

try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("fyers-mcp-complete")
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "mcp"])
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("fyers-mcp-complete")

# Global variables for OAuth flow
auth_result = {}
auth_server = None
fyers_client = None

class OAuthHandler(BaseHTTPRequestHandler):
    """Handle OAuth redirect from Fyers."""
    
    def do_GET(self):
        global auth_result
        
        # Parse query parameters
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        auth_code = query_params.get('auth_code', [None])[0] or query_params.get('code', [None])[0]
        
        if auth_code:
            auth_result['auth_code'] = auth_code
            auth_result['status'] = 'success'
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html_response = '''
            <html><body>
            <h2>Authentication Successful!</h2>
            <p>You can close this browser window.</p>
            <p>Return to Claude to continue.</p>
            </body></html>
            '''
            self.wfile.write(html_response.encode('utf-8'))
        else:
            auth_result['status'] = 'error'
            auth_result['error'] = 'No auth code received'
            
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html_error = '''
            <html><body>
            <h2>Authentication Failed</h2>
            <p>No authorization code received.</p>
            </body></html>
            '''
            self.wfile.write(html_error.encode('utf-8'))
    
    def log_message(self, format, *args):
        # Suppress server logs
        pass

def start_auth_server():
    """Start local server to capture OAuth redirect."""
    global auth_server
    
    try:
        auth_server = HTTPServer(('localhost', 8080), OAuthHandler)
        auth_server.timeout = 60  # 1 minute timeout
        auth_server.handle_request()  # Handle single request
    except Exception as e:
        print(f"Server error: {e}")

def get_fyers_client():
    """Initialize and return Fyers client."""
    global fyers_client
    if fyers_client is None:
        try:
            from fyers_apiv3 import fyersModel
            
            client_id = os.getenv("FYERS_CLIENT_ID")
            access_token = os.getenv("FYERS_ACCESS_TOKEN")
            
            if not client_id or not access_token:
                return None
            
            fyers_client = fyersModel.FyersModel(
                client_id=client_id,
                is_async=False,
                token=access_token,
                log_path=""
            )
            
        except Exception as e:
            print(f"Error initializing Fyers client: {e}")
            return None
    
    return fyers_client

@mcp.tool()
def authenticate() -> str:
    """Smart OAuth authentication - opens browser and captures redirect automatically."""
    global auth_result
    
    client_id = os.getenv("FYERS_CLIENT_ID")
    secret_key = os.getenv("FYERS_SECRET_KEY")
    redirect_uri = "http://localhost:8080/"
    
    if not client_id or not secret_key:
        return "❌ Missing FYERS_CLIENT_ID or FYERS_SECRET_KEY in environment"
    
    # Reset auth result
    auth_result = {}
    
    # Generate auth URL
    auth_url = f"https://api-t1.fyers.in/api/v3/generate-authcode?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&state=sample_state"
    
    try:
        # Start server in background
        server_thread = threading.Thread(target=start_auth_server, daemon=True)
        server_thread.start()
        
        # Give server time to start
        time.sleep(1)
        
        # Open browser
        webbrowser.open(auth_url)
        
        # Wait for response (max 60 seconds)
        for _ in range(60):
            if auth_result:
                break
            time.sleep(1)
        
        if not auth_result:
            return "❌ Authentication timeout. Please try again."
        
        if auth_result.get('status') != 'success':
            return f"❌ Authentication failed: {auth_result.get('error', 'Unknown error')}"
        
        # Exchange auth code for token
        auth_code = auth_result['auth_code']
        
        from fyers_apiv3 import fyersModel
        
        session = fyersModel.SessionModel(
            client_id=client_id,
            secret_key=secret_key,
            redirect_uri=redirect_uri,
            grant_type="authorization_code"
        )
        
        session.set_token(auth_code)
        response = session.generate_token()
        
        if response.get("code") == 200:
            access_token = response["access_token"]
            
            # Save token to .env file (not just environment)
            env_path = os.path.join(os.path.dirname(__file__), ".env")
            
            # Read current .env
            env_lines = []
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    env_lines = f.readlines()
            
            # Update or add token
            token_found = False
            for i, line in enumerate(env_lines):
                if line.startswith('FYERS_ACCESS_TOKEN='):
                    env_lines[i] = f'FYERS_ACCESS_TOKEN={access_token}\n'
                    token_found = True
                    break
            
            if not token_found:
                env_lines.append(f'FYERS_ACCESS_TOKEN={access_token}\n')
            
            # Write back to .env
            with open(env_path, 'w') as f:
                f.writelines(env_lines)
            
            # Also set in current environment
            os.environ["FYERS_ACCESS_TOKEN"] = access_token
            
            # Reset global client
            global fyers_client
            fyers_client = None
            
            return "✅ Authentication successful! All trading functions are now available."
        else:
            return f"❌ Token generation failed: {response}"
            
    except Exception as e:
        return f"❌ Authentication error: {str(e)}"

@mcp.tool()
def check_auth_status() -> str:
    """Check current authentication status."""
    access_token = os.getenv("FYERS_ACCESS_TOKEN")
    
    if access_token:
        try:
            client = get_fyers_client()
            if client:
                response = client.get_profile()
                if response.get("code") == 200:
                    name = response["data"].get("name", "User")
                    return f"✅ Authenticated as: {name}"
                else:
                    return "❌ Token expired or invalid"
            else:
                return "❌ Client initialization failed"
        except Exception as e:
            return f"❌ Auth check failed: {str(e)}"
    else:
        return "❌ Not authenticated. Use 'authenticate' tool."

@mcp.tool()
def get_profile() -> str:
    """Get user profile information."""
    try:
        client = get_fyers_client()
        if not client:
            return "❌ Not authenticated. Use 'authenticate' tool first."
        
        response = client.get_profile()
        
        if response.get("code") == 200:
            data = response["data"]
            return f"""✅ Profile Information:
Name: {data.get('name', 'N/A')}
Email: {data.get('email_id', 'N/A')}
Mobile: {data.get('mobile_number', 'N/A')}
Client ID: {data.get('fy_id', 'N/A')}
"""
        else:
            return f"❌ Failed to get profile: {response}"
            
    except Exception as e:
        return f"❌ Error getting profile: {str(e)}"

@mcp.tool()
def get_funds() -> str:
    """Get account funds information."""
    try:
        client = get_fyers_client()
        if not client:
            return "❌ Not authenticated. Use 'authenticate' tool first."
        
        response = client.funds()
        
        if response.get("code") == 200:
            # Handle both dict and list response formats
            if isinstance(response.get("fund_limit"), list) and response["fund_limit"]:
                fund_data = response["fund_limit"][0]
            else:
                fund_data = response.get("fund_limit", {})
            
            return f"""✅ Account Funds:
Equity Available: ₹{fund_data.get('equityAmount', 0):,.2f}
Commodity Available: ₹{fund_data.get('commodityAmount', 0):,.2f}
Used Margin: ₹{fund_data.get('utilisedAmount', 0):,.2f}
Total Balance: ₹{fund_data.get('total_balance', 0):,.2f}
"""
        else:
            return f"❌ Failed to get funds: {response}"
            
    except Exception as e:
        return f"❌ Error getting funds: {str(e)}"

@mcp.tool()
def get_holdings() -> str:
    """Get portfolio holdings."""
    try:
        client = get_fyers_client()
        if not client:
            return "❌ Not authenticated. Use 'authenticate' tool first."
        
        response = client.holdings()
        
        if response.get("code") == 200:
            holdings = response.get("holdings", [])
            
            if not holdings:
                return "📊 No holdings found"
            
            result = "📊 Portfolio Holdings:\n\n"
            total_value = 0
            total_pnl = 0
            
            for holding in holdings:
                symbol = holding.get("symbol", "N/A")
                qty = holding.get("quantity", holding.get("qty", 0))
                ltp = holding.get("ltp", 0)
                avg_price = holding.get("costPrice", 0)
                current_value = qty * ltp
                pnl = current_value - (qty * avg_price)
                pnl_pct = (pnl / (qty * avg_price) * 100) if avg_price > 0 else 0
                
                total_value += current_value
                total_pnl += pnl
                
                result += f"""📈 {symbol}
Qty: {qty} | LTP: ₹{ltp:.2f} | Avg: ₹{avg_price:.2f}
Current Value: ₹{current_value:,.2f}
P&L: ₹{pnl:,.2f} ({pnl_pct:+.2f}%)

"""
            
            result += f"""💰 Summary:
Total Value: ₹{total_value:,.2f}
Total P&L: ₹{total_pnl:,.2f}"""
            return result
        else:
            return f"❌ Failed to get holdings: {response}"
            
    except Exception as e:
        return f"❌ Error getting holdings: {str(e)}"

@mcp.tool()
def get_positions() -> str:
    """Get current trading positions."""
    try:
        client = get_fyers_client()
        if not client:
            return "❌ Not authenticated. Use 'authenticate' tool first."
        
        response = client.positions()
        
        if response.get("code") == 200:
            positions = response.get("netPositions", [])
            
            if not positions:
                return "📊 No open positions"
            
            result = "📊 Current Positions:\n\n"
            total_pnl = 0
            
            for pos in positions:
                symbol = pos.get("symbol", "N/A")
                qty = pos.get("qty", 0)
                side = pos.get("side", 0)
                avg_price = pos.get("avgPrice", 0)
                ltp = pos.get("ltp", 0)
                pnl = pos.get("pl", 0)
                
                side_text = "LONG" if side > 0 else "SHORT"
                total_pnl += pnl
                
                result += f"""📈 {symbol} ({side_text})
Qty: {abs(qty)} | Avg: ₹{avg_price:.2f} | LTP: ₹{ltp:.2f}
P&L: ₹{pnl:,.2f}

"""
            
            result += f"💰 Total P&L: ₹{total_pnl:,.2f}"
            return result
        else:
            return f"❌ Failed to get positions: {response}"
            
    except Exception as e:
        return f"❌ Error getting positions: {str(e)}"

@mcp.tool()
def get_orders() -> str:
    """Get order history."""
    try:
        client = get_fyers_client()
        if not client:
            return "❌ Not authenticated. Use 'authenticate' tool first."
        
        response = client.orderbook()
        
        if response.get("code") == 200:
            orders = response.get("orderBook", [])
            
            if not orders:
                return "📊 No orders found"
            
            result = "📊 Recent Orders:\n\n"
            
            for order in orders[-10:]:
                symbol = order.get("symbol", "N/A")
                side = order.get("side", 0)
                qty = order.get("qty", 0)
                price = order.get("limitPrice", 0)
                status = order.get("status", "N/A")
                order_type = order.get("type", "N/A")
                
                side_text = "BUY" if side > 0 else "SELL"
                
                result += f"""📋 {symbol} - {side_text}
Qty: {qty} | Price: ₹{price:.2f}
Type: {order_type} | Status: {status}

"""
            
            return result
        else:
            return f"❌ Failed to get orders: {response}"
            
    except Exception as e:
        return f"❌ Error getting orders: {str(e)}"

@mcp.tool()
def get_quotes(symbols: str) -> str:
    """Get live quotes for symbols.
    
    Args:
        symbols: Comma-separated symbols (e.g., "NSE:SBIN-EQ,NSE:RELIANCE-EQ")
    """
    try:
        client = get_fyers_client()
        if not client:
            return "❌ Not authenticated. Use 'authenticate' tool first."
        
        symbol_list = [s.strip() for s in symbols.split(",")]
        
        response = client.quotes({"symbols": symbol_list})
        
        if response.get("code") == 200:
            quotes_data = response.get("d", [])
            if isinstance(quotes_data, list):
                quotes = {item.get('n', 'Unknown'): item for item in quotes_data}
            else:
                quotes = quotes_data
            
            result = "📊 Live Quotes:\n\n"
            
            for symbol_name, data in quotes.items():
                if isinstance(data, dict):
                    quote = data.get('v', data)
                    ltp = quote.get('lp', quote.get('c', 0))
                    change = quote.get('ch', quote.get('change', 0))
                    change_pct = quote.get('chp', quote.get('changePer', 0))
                    volume = quote.get('volume', quote.get('vol', 0))
                    
                    result += f"""📈 {symbol_name}
LTP: ₹{ltp:.2f}
Change: ₹{change:+.2f} ({change_pct:+.2f}%)
Volume: {volume:,}

"""
            
            return result
        else:
            return f"❌ Failed to get quotes: {response}"
            
    except Exception as e:
        return f"❌ Error getting quotes: {str(e)}"

@mcp.tool()
def place_order(symbol: str, quantity: int, order_type: str, side: str, product_type: str = "MARGIN", limit_price: float = 0, stop_price: float = 0, validity: str = "DAY") -> str:
    """Place a new order.
    
    Args:
        symbol: Trading symbol (e.g., "NSE:SBIN-EQ")
        quantity: Number of shares
        order_type: Order type ("MARKET", "LIMIT", "STOP", "STOPLIMIT")
        side: Order side ("BUY" or "SELL")
        product_type: Product type ("MARGIN", "INTRADAY", "CNC", "BO", "CO")
        limit_price: Limit price (for LIMIT orders)
        stop_price: Stop price (for STOP orders)
        validity: Order validity ("DAY", "IOC", "GTD")
    """
    try:
        client = get_fyers_client()
        if not client:
            return "❌ Not authenticated. Use 'authenticate' tool first."
        
        # Map string values to API constants
        type_map = {"MARKET": 1, "LIMIT": 2, "STOP": 3, "STOPLIMIT": 4}
        side_map = {"BUY": 1, "SELL": -1}
        
        order_data = {
            "symbol": symbol,
            "qty": quantity,
            "type": type_map.get(order_type.upper(), 2),
            "side": side_map.get(side.upper(), 1),
            "productType": product_type,
            "limitPrice": limit_price,
            "stopPrice": stop_price,
            "validity": validity,
            "disclosedQty": 0,
            "offlineOrder": False
        }
        
        response = client.place_order(order_data)
        
        if response.get("code") == 201:
            order_id = response.get("id", "Unknown")
            return f"✅ Order placed successfully!\nOrder ID: {order_id}\nSymbol: {symbol}\nQty: {quantity} {side}\nType: {order_type}"
        else:
            return f"❌ Order placement failed: {response.get('message', 'Unknown error')}"
            
    except Exception as e:
        return f"❌ Error placing order: {str(e)}"

@mcp.tool()
def modify_order(order_id: str, quantity: Optional[int] = None, limit_price: Optional[float] = None, stop_price: Optional[float] = None) -> str:
    """Modify an existing order.
    
    Args:
        order_id: Order ID to modify
        quantity: New quantity (optional)
        limit_price: New limit price (optional)
        stop_price: New stop price (optional)
    """
    try:
        client = get_fyers_client()
        if not client:
            return "❌ Not authenticated. Use 'authenticate' tool first."
        
        modify_data = {"id": order_id}
        
        if quantity is not None:
            modify_data["qty"] = quantity
        if limit_price is not None:
            modify_data["limitPrice"] = limit_price
        if stop_price is not None:
            modify_data["stopPrice"] = stop_price
        
        response = client.modify_order(modify_data)
        
        if response.get("code") == 200:
            return f"✅ Order modified successfully!\nOrder ID: {order_id}"
        else:
            return f"❌ Order modification failed: {response.get('message', 'Unknown error')}"
            
    except Exception as e:
        return f"❌ Error modifying order: {str(e)}"

@mcp.tool()
def cancel_order(order_id: str) -> str:
    """Cancel an existing order.
    
    Args:
        order_id: Order ID to cancel
    """
    try:
        client = get_fyers_client()
        if not client:
            return "❌ Not authenticated. Use 'authenticate' tool first."
        
        cancel_data = {"id": order_id}
        
        response = client.cancel_order(cancel_data)
        
        if response.get("code") == 200:
            return f"✅ Order cancelled successfully!\nOrder ID: {order_id}"
        else:
            return f"❌ Order cancellation failed: {response.get('message', 'Unknown error')}"
            
    except Exception as e:
        return f"❌ Error cancelling order: {str(e)}"

if __name__ == "__main__":
    print("🚀 Starting Smart Fyers MCP Server...")
    try:
        mcp.run(transport="stdio")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)