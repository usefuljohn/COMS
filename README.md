# BitShares Liquidity & Credit Manager

This project consists of a Python automation script designed to manage DeFi operations on the BitShares blockchain. Specifically, it streamlines the process of withdrawing liquidity from a liquidity pool and immediately utilizing those funds to update (top-up) a credit offer in a single, atomic transaction bundle.

The generated output is a JSON file compatible with the **Beet Wallet**, allowing for secure signing and broadcasting via local application.

## Features

*   **Pool Statistics Monitoring:** Connects to a BitShares WebSocket node to fetch real-time statistics for specific Liquidity Pools (e.g., XBTSX.USDT / XBTSX.XAUT).
*   **Automated Calculations:** Determines the exact amount of assets (Asset A and Asset B) to be received upon withdrawing a percentage of LP tokens, including slippage tolerance calculations.
*   **Atomic Transaction Bundling:** Creates a transaction that performs two actions simultaneously:
    1.  **Liquidity Withdrawal:** Withdraws a specified portion (default 10%) of LP tokens.
    2.  **Credit Offer Update:** Updates an existing credit offer with the withdrawn funds (specifically the USDT portion).
*   **Astro UI Compatibility:** Outputs the transaction in a standard JSON format ready for injection into the BitShares Astro UI for user signature.

## Prerequisites

*   Python 3.x
*   `websocket-client` library

```bash
pip install websocket-client
```

## Configuration

Before running the script, you must configure your account details in `liquidity_engine.py`. Open the file and update the following placeholders:

```python
# liquidity_engine.py

ACCOUNT_ID = "YOUR_ACCOUNT_ID"          # e.g., "1.2.x"
ACCOUNT_NAME = "YOUR_ACCOUNT_NAME"      # e.g., "your-account-name"
CREDIT_OFFER_ID = "YOUR_CREDIT_OFFER_ID" # e.g., "1.21.x"
```

You can also adjust the target Liquidity Pool and withdrawal percentage within the `__main__` block if necessary.

## Usage

Run the script from your terminal:

```bash
python liquidity_engine.py
```

### Output

Upon successful execution, the script will generate a file named `generated_bundle.json`.

1.  Open your Beet Wallet.
2.  Upload JSON via local option.
3.  Review the operations.
4.  Sign and broadcast the transaction.

## File Structure

*   `liquidity_engine.py`: The main Python script containing the logic for connecting to the node, calculating amounts, and generating the transaction.
*   `generated_bundle.json`: The output file containing the unsigned transaction.
*   `transaction.json`: A template or reference file for credit offer operations.

## Disclaimer

This software is for educational and experimental purposes. Always verify transaction details before signing. The authors are not responsible for any financial losses incurred through the use of this software.
