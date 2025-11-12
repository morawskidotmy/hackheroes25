# Supabase Authentication Setup

This guide will help you set up Supabase for social login (Google, GitHub) in the CO2 Bike Calculator.

## Step 1: Create a Supabase Account

1. Go to [supabase.com](https://supabase.com)
2. Click "Start your project for free"
3. Sign up with email or GitHub
4. Create a new project:
   - **Project name**: co2-bike-calculator (or any name)
   - **Database password**: Create a strong password
   - **Region**: Choose closest to you (e.g., Europe - Frankfurt)
   - Click "Create new project"

## Step 2: Get Your Credentials

1. Once the project is created, go to **Settings** > **API**
2. Copy these values:
   - **Project URL** → `SUPABASE_URL`
   - **anon public** → `SUPABASE_ANON_KEY`

## Step 3: Enable Google OAuth

1. In Supabase, go to **Authentication** > **Providers**
2. Find **Google** and click to enable it
3. You'll need Google OAuth credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project
   - Enable the Google+ API
   - Create OAuth 2.0 credentials (Web application)
   - Authorized redirect URIs: `https://YOUR_PROJECT_ID.supabase.co/auth/v1/callback`
   - Copy Client ID and Client Secret to Supabase
4. Click **Save**

## Step 4: Enable GitHub OAuth (Optional)

1. In Supabase, go to **Authentication** > **Providers**
2. Find **GitHub** and click to enable it
3. Go to GitHub Settings > Developer settings > OAuth Apps
4. Create a new OAuth App:
   - **Authorization callback URL**: `https://YOUR_PROJECT_ID.supabase.co/auth/v1/callback`
   - Copy Client ID and Client Secret to Supabase
5. Click **Save**

## Step 5: Add Credentials to index.html

Open `index.html` and find these lines at the top of the `<script>` section:

```javascript
const SUPABASE_URL = 'YOUR_SUPABASE_URL';
const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY';
```

Replace with your actual values:

```javascript
const SUPABASE_URL = 'https://xxxxx.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGc...xxxxx';
```

## Step 6: Configure Redirect URL

1. In Supabase, go to **Authentication** > **URL Configuration**
2. Set **Redirect URLs** to include:
   - `http://localhost:8080`
   - Your production URL (if deployed)

## Step 7: Test It!

1. Run the app:
   ```bash
   python3 app.py
   ```

2. Open http://localhost:8080

3. You should see a login modal with Google and GitHub buttons

4. Click to login and test!

## Troubleshooting

**"Auth modal not showing"**
- Check that SUPABASE_URL and SUPABASE_ANON_KEY are set correctly
- Check browser console for errors (F12)

**"Redirect URI mismatch"**
- Make sure your redirect URL in Supabase matches your app URL
- Include the full URL with protocol (http:// or https://)

**"Client ID/Secret invalid"**
- Double-check you copied them correctly from Google/GitHub
- Make sure they're in the right Supabase provider

## Disabling Auth

If you don't want to use authentication, the app will still work without it:
- Leave the credentials as `YOUR_SUPABASE_URL` and `YOUR_SUPABASE_ANON_KEY`
- The auth modal will be hidden and everyone can use the calculator
- This is useful for local testing or internal deployments

## Environment Variables (Optional)

Instead of hardcoding credentials in HTML, you can pass them from the server:

In `app.py`:
```python
@app.route('/')
def index():
    with open('index.html', 'r') as f:
        content = f.read()
    content = content.replace('YOUR_SUPABASE_URL', os.getenv('SUPABASE_URL', ''))
    content = content.replace('YOUR_SUPABASE_ANON_KEY', os.getenv('SUPABASE_ANON_KEY', ''))
    return content
```

Then set environment variables:
```bash
SUPABASE_URL="https://xxxxx.supabase.co" \
SUPABASE_ANON_KEY="eyJhbGc..." \
python3 app.py
```
