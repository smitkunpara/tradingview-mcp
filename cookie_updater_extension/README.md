# TV Cookie Sync Extension

## Install in Chrome
1. Open `chrome://extensions/` in Chrome.
2. Enable **Developer mode** (top-right toggle).
3. Click **Load unpacked** and select the `cookie_updater_extension` folder.
4. The "TV Cookie Sync" extension will appear in the toolbar.

## Usage
- **First run**: Open extension popup → Setup screen.
  - Enter backend URL (e.g., `https://your-app.vercel.app`), API key, and password.
  - Extension verifies backend with GET request, encrypts credentials, and stores in local storage.
- **Sync cookies**: Open popup → Click **Update** → Enter password.
  - Extension reads TradingView cookies, sends POST to `{backendUrl}/update-cookies` with `X-Admin-Key` header.

## Permissions
- `cookies`: Read TradingView cookies.
- `storage`: Store encrypted credentials.

## Notes
- Ensure logged into TradingView; no cookies = no sync.
- For custom backends, deploy `vercel/index.py` to Vercel.