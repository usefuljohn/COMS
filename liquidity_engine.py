import json
import time
import uuid
from datetime import datetime, timedelta
from urllib.parse import quote
from decimal import Decimal
from websocket import create_connection

# --- CONFIGURATION ---
NODE_URL = "wss://[YOUR_NODE_URL]"
ACCOUNT_ID = "[YOUR_ACCOUNT_ID]"
ACCOUNT_NAME = "[YOUR_ACCOUNT_NAME]"
CREDIT_OFFER_ID = "[YOUR_CREDIT_OFFER_ID]"

# Pool Config: Map your LP Token (1.3.x) to the Pool ID (1.19.x)
LIQUIDITY_POOLS = {
    "[YOUR_LP_TOKEN_ID]": { 
        "pool_id": "[YOUR_POOL_ID]", 
        "asset_a_symbol": "[ASSET_A_SYMBOL]",
        "asset_b_symbol": "[ASSET_B_SYMBOL]"
    }
}

class LiquidityManager:
    def __init__(self, node_url):
        self.node_url = node_url
        self.ws = None
        self._request_id = 1

    def connect(self):
        """Establish websocket connection"""
        try:
            self.ws = create_connection(self.node_url, timeout=10)
            return True
        except Exception as e:
            print(f"[!] Connection Error: {e}")
            return False

    def close(self):
        """Close websocket connection"""
        if self.ws:
            self.ws.close()

    def _rpc_call(self, method, params):
        """Helper to make RPC calls over WebSocket"""
        if not self.ws:
            if not self.connect():
                return None

        payload = {
            "method": method,
            "params": params,
            "jsonrpc": "2.0",
            "id": self._request_id
        }
        self._request_id += 1
        
        try:
            self.ws.send(json.dumps(payload))
            response = json.loads(self.ws.recv())
            if 'error' in response:
                raise Exception(f"RPC Error: {response['error']}")
            return response['result']
        except Exception as e:
            print(f"[!] WebSocket Error: {e}")
            # Try to reconnect once
            if self.connect():
                try:
                    self.ws.send(json.dumps(payload))
                    response = json.loads(self.ws.recv())
                    return response.get('result')
                except:
                    pass
            return None

    def get_pool_stats(self, pool_id):
        """Fetches current balances and share supply for a pool"""
        objs = self._rpc_call("get_objects", [[pool_id]])
        if not objs or not objs[0]:
            return None
        
        pool_obj = objs[0]
        
        # Parse the dynamic asset data inside the pool
        balance_a = int(pool_obj["balance_a"])
        balance_b = int(pool_obj["balance_b"])
        asset_a_id = pool_obj["asset_a"]
        asset_b_id = pool_obj["asset_b"]
        share_asset_id = pool_obj["share_asset"]
        
        # Get total supply of the LP token (share asset)
        share_asset_objs = self._rpc_call("get_objects", [[share_asset_id]])
        if not share_asset_objs or not share_asset_objs[0]:
            return None
            
        share_asset_obj = share_asset_objs[0]
        
        # Correctly fetching dynamic data for current supply
        dyn_data_id = share_asset_obj["dynamic_asset_data_id"]
        dyn_objs = self._rpc_call("get_objects", [[dyn_data_id]])
        if not dyn_objs or not dyn_objs[0]:
            return None
            
        dyn_data = dyn_objs[0]
        current_share_supply = int(dyn_data["current_supply"])

        return {
            "pool_id": pool_id,
            "balance_a": balance_a,
            "balance_b": balance_b,
            "asset_a_id": asset_a_id,
            "asset_b_id": asset_b_id,
            "share_asset_id": share_asset_id,
            "total_supply": current_share_supply
        }

    def get_user_balance(self, account_id, asset_id):
        """Fetches the balance of a specific asset for an account"""
        balances = self._rpc_call("get_account_balances", [account_id, [asset_id]])
        if balances and len(balances) > 0:
            return int(balances[0]["amount"])
        return 0

    def calculate_withdrawal_from_shares(self, pool_stats, shares_to_burn):
        """
        Calculates the expected asset return when burning a specific number of shares.
        """
        if shares_to_burn <= 0:
            raise ValueError("Shares to burn must be greater than zero.")

        fraction = Decimal(shares_to_burn) / Decimal(pool_stats["total_supply"])
        
        expected_a = int(Decimal(pool_stats["balance_a"]) * fraction)
        expected_b = int(Decimal(pool_stats["balance_b"]) * fraction)

        # Apply 1% slippage tolerance
        min_a = int(expected_a * 0.99)
        min_b = int(expected_b * 0.99)

        return {
            "shares_to_withdraw": shares_to_burn,
            "min_a": min_a,
            "min_b": min_b,
            "expected_a": expected_a,
            "expected_b": expected_b
        }

    def create_withdrawal_op(self, withdrawal_data, pool_stats):
        """Creates the liquidity_pool_withdraw operation structure"""
        op_structure = {
            "fee": {
                "amount": "0", 
                "asset_id": "1.3.0"
            },
            "account": ACCOUNT_ID,
            "pool": pool_stats["pool_id"],
            "share_amount": {
                "amount": str(withdrawal_data["shares_to_withdraw"]),
                "asset_id": pool_stats["share_asset_id"]
            },
            "min_a": {
                "amount": str(withdrawal_data["min_a"]),
                "asset_id": pool_stats["asset_a_id"]
            },
            "min_b": {
                "amount": str(withdrawal_data["min_b"]),
                "asset_id": pool_stats["asset_b_id"]
            },
            "extensions": []
        }
        return [62, op_structure]

    def create_credit_offer_update_op(self, amount_atoms, asset_id):
        """Creates the credit_offer_update operation structure based on transaction.json"""
        op_structure = {
            "fee": {
                "amount": "15307", 
                "asset_id": "1.3.0"
            },
            "owner_account": ACCOUNT_ID,
            "offer_id": CREDIT_OFFER_ID,
            "delta_amount": {
                "amount": str(amount_atoms),
                "asset_id": asset_id
            },
            "fee_rate": 10000,
            "max_duration_seconds": 2592000,
            "min_deal_amount": "15000000",
            "enabled": True,
            "auto_disable_time": "[YYYY-MM-DDTHH:MM:SS]",
            "acceptable_collateral": [
                ["[COLLATERAL_ASSET_ID_1]", {"base": {"amount": "[AMOUNT]", "asset_id": asset_id}, "quote": {"amount": "[AMOUNT]", "asset_id": "[COLLATERAL_ASSET_ID_1]"}}],
                ["[COLLATERAL_ASSET_ID_2]", {"base": {"amount": "[AMOUNT]", "asset_id": asset_id}, "quote": {"amount": "[AMOUNT]", "asset_id": "[COLLATERAL_ASSET_ID_2]"}}]
            ],
            "acceptable_borrowers": [],
            "extensions": []
        }
        return [71, op_structure]

    def generate_json(self, operations):
        """Generates the Astro UI compatible JSON envelope for a list of operations"""
        
        payload = {
            "type": "api",
            "id": "gen-" + str(int(time.time())),
            "payload": {
                "method": "injectedCall",
                "params": [
                    "signAndBroadcast",
                    json.dumps({
                        "ref_block_num": 0,
                        "ref_block_prefix": 0,
                        "expiration": "[YYYY-MM-DDTHH:MM:SS]",
                        "operations": operations,
                        "extensions": [],
                        "signatures": []
                    }),
                    []
                ],
                "appName": "[YOUR_APP_NAME]",
                "chain": "BTS",
                "browser": "web browser",
                "origin": "localhost",
                "memo": False
            }
        }
        return json.dumps(payload, indent=4)

    def generate_deep_link(self, operations, chain_id="BTS"):
        """Generates a deep link for the Beet wallet"""
        # Fetch chain data for transaction parameters
        props = self._rpc_call("get_dynamic_global_properties", [])
        if not props:
            print("[!] Could not fetch dynamic global properties for Deep Link.")
            return None
            
        head_block_number = props["head_block_number"]
        head_block_id = props["head_block_id"]
        
        ref_block_num = head_block_number & 0xFFFF
        # block_id is hex string. bytes 4-8, little endian.
        ref_block_prefix = int.from_bytes(bytes.fromhex(head_block_id)[4:8], 'little')
        
        # Expiration: now + 2 hours
        # Bitshares nodes use UTC.
        # props["time"] format is "2025-..."
        chain_time = datetime.strptime(props["time"], "%Y-%m-%dT%H:%M:%S")
        expiration_time = chain_time + timedelta(hours=2)
        expiration_str = expiration_time.strftime("%Y-%m-%dT%H:%M:%S")
        
        tr_object = {
            "ref_block_num": ref_block_num,
            "ref_block_prefix": ref_block_prefix,
            "expiration": expiration_str,
            "operations": operations,
            "extensions": [],
            "signatures": []
        }
        
        request = {
            "type": "api",
            "id": str(uuid.uuid4()),
            "payload": {
                "method": "injectedCall",
                "params": [
                    "signAndBroadcast",
                    json.dumps(tr_object),
                    []
                ],
                "appName": "[YOUR_APP_NAME]",
                "chain": chain_id,
                "browser": "web browser",
                "origin": "localhost",
                "memo": False 
            }
        }
        
        encoded_payload = quote(json.dumps(request))
        scheme = "rawbeeteos://"
        return f"{scheme}api?chain={chain_id}&request={encoded_payload}"

# --- EXECUTION ---

if __name__ == "__main__":
    manager = LiquidityManager(NODE_URL)
    
    try:
        # Configuration for the run
        target_lp_token = "[YOUR_LP_TOKEN_ID]"
        
        print(f"[*] Connecting to {NODE_URL}...")
        if manager.connect():
            pool_info = LIQUIDITY_POOLS[target_lp_token]
            pool_id = pool_info["pool_id"]

            print(f"[*] Fetching stats for pool {pool_id}...")
            stats = manager.get_pool_stats(pool_id)
            
            if stats:
                # In this pool configuration:
                # Asset A: [ASSET_A_SYMBOL]
                # Asset B: [ASSET_B_SYMBOL]
                
                # We want to use [ASSET_B_SYMBOL] for the credit offer.
                # Assuming config matches pool asset order A/B or logic handles it.
                # Here we strictly follow the config map keys.
                target_asset_id = stats["asset_b_id"] 
                
                print(f"[*] Pool assets: A={stats['asset_a_id']} ([ASSET_A_SYMBOL]), B={stats['asset_b_id']} ([ASSET_B_SYMBOL])")
                
                # 1. Fetch User's LP Token Balance
                user_lp_balance = manager.get_user_balance(ACCOUNT_ID, target_lp_token)
                print(f"[*] User LP Balance ({target_lp_token}): {user_lp_balance}")
                
                if user_lp_balance > 0:
                    # 2. Calculate 10% of shares
                    shares_to_withdraw = int(Decimal(user_lp_balance) * Decimal("0.10"))
                    print(f"[*] Withdrawing 10% of holdings: {shares_to_withdraw} shares")
                    
                    try:
                        # 3. Calculate expected return
                        withdrawal_calc = manager.calculate_withdrawal_from_shares(stats, shares_to_withdraw)
                        
                        expected_asset_b = withdrawal_calc["expected_b"] 
                        min_asset_b = withdrawal_calc["min_b"]
                        
                        print(f"[*] Estimated Return: {expected_asset_b} [ASSET_B_SYMBOL] (Min: {min_asset_b})")
                        
                        # 4. Create Operations
                        ops = []
                        
                        # Op A: Withdraw Liquidity
                        ops.append(manager.create_withdrawal_op(withdrawal_calc, stats))
                        
                        # Op B: Update Credit Offer (Top-up)
                        # We pledge the minimum guaranteed amount (Asset B) to ensure the op doesn't fail due to slippage
                        ops.append(manager.create_credit_offer_update_op(min_asset_b, target_asset_id))
                        
                        # 5. Generate Combined JSON
                        final_json = manager.generate_json(ops)
                        
                        filename = "generated_bundle.json"
                        with open(filename, "w") as f:
                            f.write(final_json)
                        
                        print(f"[+] Success! Atomic transaction bundle saved to {filename}")
                        
                        # 6. Generate Deep Link
                        deep_link = manager.generate_deep_link(ops)
                        if deep_link:
                            print(f"\n[+] Deep Link Generated:")
                            print(deep_link)
                            
                            # Optional: Save to file for easy copying
                            with open("generated_deeplink.txt", "w") as f:
                                f.write(deep_link)
                            print(f"[+] Deep link saved to generated_deeplink.txt")
                        
                    except ValueError as e:
                        print(f"[!] Calculation Error: {e}")
                else:
                    print("[!] User has no balance of this LP token.")
            else:
                print("[!] Failed to fetch pool stats.")
            
            manager.close()
    except Exception as e:
        print(f"[!] Unexpected Error: {e}")
