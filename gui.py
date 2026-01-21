import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import json
import os

BUNDLE_FILE = "generated_bundle.json"
SCRIPT_NAME = "liquidity_engine.py"

def run_liquidity_engine():
    """Runs the liquidity_engine.py script and updates the display."""
    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, f"Running {SCRIPT_NAME}...\n")
    window.update()

    try:
        # Run the script
        result = subprocess.run(
            ["python", SCRIPT_NAME], 
            capture_output=True, 
            text=True,
            cwd=os.getcwd()
        )
        
        output_text.insert(tk.END, "--- STDOUT ---\n")
        output_text.insert(tk.END, result.stdout + "\n")
        
        if result.stderr:
            output_text.insert(tk.END, "--- STDERR ---\n")
            output_text.insert(tk.END, result.stderr + "\n")

        output_text.insert(tk.END, "-" * 20 + "\n")
        
        if result.returncode == 0:
            load_and_display_offer_info()
        else:
            output_text.insert(tk.END, "Error running script.\n")

    except Exception as e:
        output_text.insert(tk.END, f"Failed to execute script: {e}\n")

def load_and_display_offer_info():
    """Reads the generated bundle JSON and displays credit offer info."""
    if not os.path.exists(BUNDLE_FILE):
        output_text.insert(tk.END, f"{BUNDLE_FILE} not found.\n")
        return

    try:
        with open(BUNDLE_FILE, 'r') as f:
            data = json.load(f)

        # Navigate to the inner JSON string
        # Structure: root -> payload -> params -> [1] (string) -> operations
        
        params = data.get("payload", {}).get("params", [])
        if len(params) < 2:
            output_text.insert(tk.END, "Invalid JSON structure: 'params' too short.\n")
            return

        inner_json_str = params[1]
        inner_data = json.loads(inner_json_str)
        
        operations = inner_data.get("operations", [])
        
        found_offer = False
        output_text.insert(tk.END, "\n=== CREDIT OFFER INFORMATION ===\n")
        
        for op in operations:
            op_code = op[0]
            op_data = op[1]
            
            # Opcode 71 is usually credit_offer_update
            if "offer_id" in op_data and "fee_rate" in op_data:
                found_offer = True
                
                output_text.insert(tk.END, f"Offer ID: {op_data.get('offer_id')}\n")
                
                delta = op_data.get('delta_amount', {})
                output_text.insert(tk.END, f"Delta Amount: {delta.get('amount')} (Asset ID: {delta.get('asset_id')})\n")
                
                output_text.insert(tk.END, f"Fee Rate: {op_data.get('fee_rate')}\n")
                output_text.insert(tk.END, f"Max Duration (sec): {op_data.get('max_duration_seconds')}\n")
                output_text.insert(tk.END, f"Min Deal Amount: {op_data.get('min_deal_amount')}\n")
                output_text.insert(tk.END, f"Enabled: {op_data.get('enabled')}\n")
                output_text.insert(tk.END, f"Auto Disable Time: {op_data.get('auto_disable_time')}\n")
                
                collateral = op_data.get('acceptable_collateral', [])
                output_text.insert(tk.END, "Acceptable Collateral:\n")
                for c in collateral:
                    # c structure: [asset_id, {base:..., quote:...}]
                    asset_id = c[0]
                    output_text.insert(tk.END, f"  - Asset: {asset_id}\n")
                
                output_text.insert(tk.END, "-" * 20 + "\n")

        if not found_offer:
            output_text.insert(tk.END, "No Credit Offer operations found in generated bundle.\n")

    except json.JSONDecodeError as e:
        output_text.insert(tk.END, f"Error parsing JSON: {e}\n")
    except Exception as e:
        output_text.insert(tk.END, f"An error occurred reading info: {e}\n")

# --- GUI Setup ---
window = tk.Tk()
window.title("BTWTY Wallet - Liquidity Manager")
window.geometry("700x600")

# Header
header_label = tk.Label(window, text="Liquidity Engine Control", font=("Helvetica", 16, "bold"))
header_label.pack(pady=10)

# Run Button
run_btn = tk.Button(window, text="Run Liquidity Engine", command=run_liquidity_engine, 
                    bg="#4CAF50", fg="white", font=("Helvetica", 12), height=2, width=20)
run_btn.pack(pady=10)

# Output Area
output_label = tk.Label(window, text="Output & Offer Details:", font=("Helvetica", 10))
output_label.pack(anchor="w", padx=10)

output_text = scrolledtext.ScrolledText(window, width=80, height=30, font=("Consolas", 10))
output_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

# Initial Load
output_text.insert(tk.END, "Press 'Run Liquidity Engine' to generate and view data.\n")
# Optionally try to load existing data on startup
if os.path.exists(BUNDLE_FILE):
    output_text.insert(tk.END, "\n(Loading existing data...)\n")
    load_and_display_offer_info()

window.mainloop()