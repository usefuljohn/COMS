# BitShares Liquidity Engine

A Python tool to automate liquidity withdrawals and credit offer updates in a single atomic transaction.

## Features
- **Atomic Bundling:** Withdraws liquidity and tops up a credit offer in one transaction.
- **Deep Link Generation:** Creates `rawbeeteos://` links for easy signing in Beet/BeetEOS wallets.
- **Astro UI Support:** Outputs `generated_bundle.json` for manual injection if preferred.

## Setup

```bash
pip install websocket-client
```

## Usage

1. **Configure:** Edit `liquidity_engine.py` to set your `ACCOUNT_ID`, `CREDIT_OFFER_ID`, and `LIQUIDITY_POOLS`.
2. **Run:**
   ```bash
   python liquidity_engine.py
   ```
3. **Result:**
   - **`generated_deeplink.txt`**: Open this link to sign the transaction immediately.
   - **`generated_bundle.json`**: Use this file with Astro UI or compatible interfaces.

## Configuration
All settings (Node URL, Account details, Pool IDs) are located at the top of `liquidity_engine.py`.