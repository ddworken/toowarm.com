# How to Get Your FREE NCEI Token

## Is it Free?

**YES - 100% FREE!** No credit card, no payment, no subscription required.

## What You Get for Free

- **10,000 API requests per day**
- **Unlimited historical weather data** (100+ years of records)
- **5 requests per second** rate limit
- **Instant activation** - token emailed immediately

This is more than enough for any personal project or even commercial applications.

## Step-by-Step Guide

### Method 1: Web Browser (Easiest - 2 minutes)

**Step 1:** Open this URL in your browser:
```
https://www.ncdc.noaa.gov/cdo-web/token
```

**Step 2:** You'll see a simple form asking for your email address.

**Step 3:** Enter your email address and click submit.

**Step 4:** Check your email inbox (usually arrives in < 1 minute).
- Subject: "NCDC Web Services Token"
- The email contains your token - a long string like: `AbCdEfGhIjKlMnOpQrStUvWxYz123456`

**Step 5:** Copy the token from the email.

**Step 6:** Set it as an environment variable:
```bash
export NCEI_TOKEN='your_token_here'
```

**Step 7:** Test it works:
```bash
python3 test_ncei_token.py
```

That's it! You're done.

### Method 2: Command Line

```bash
# Visit in browser (can't automate this part)
open https://www.ncdc.noaa.gov/cdo-web/token

# Enter your email, get token from email
# Then set it:
export NCEI_TOKEN='your_token_here'

# Make it permanent (optional):
echo "export NCEI_TOKEN='your_token_here'" >> ~/.bashrc
source ~/.bashrc
```

## What the Email Looks Like

```
From: noaa.services@noaa.gov
To: your@email.com
Subject: NCDC Web Services Token

Your NCDC Web Services token is:

AbCdEfGhIjKlMnOpQrStUvWxYz123456

This token is for use with the Climate Data Online Web Services.
API documentation: https://www.ncdc.noaa.gov/cdo-web/webservices/v2

Rate limits:
- 5 requests per second
- 10,000 requests per day
```

## Testing Your Token

Once you have your token set:

```bash
# Test 1: Check if token is set
./get_ncei_token.sh

# Test 2: Verify token works
python3 test_ncei_token.py

# Test 3: Get January 10, 2025 ice assessment
python3 test_january_10_2025.py
```

## Making the Token Permanent

To avoid setting it every time you open a new terminal:

**On Linux/Mac:**
```bash
echo "export NCEI_TOKEN='your_token_here'" >> ~/.bashrc
source ~/.bashrc
```

**On Mac (if using zsh):**
```bash
echo "export NCEI_TOKEN='your_token_here'" >> ~/.zshrc
source ~/.zshrc
```

## Troubleshooting

### "I didn't receive the email"

1. **Check spam/junk folder** - Sometimes it goes there
2. **Wait 5-10 minutes** - Usually instant, but can take a few minutes
3. **Try a different email** - Some email providers may block it
4. **Check the website works** - Visit https://www.ncdc.noaa.gov/cdo-web/ first

### "The website is down"

The token service is occasionally down for maintenance. If you get a 503 error:
1. Wait 10-30 minutes and try again
2. Try during US business hours (NOAA is a US government agency)
3. The service is usually very reliable

### "My token doesn't work"

```bash
# Check if it's set:
echo $NCEI_TOKEN

# Make sure there are no extra spaces:
export NCEI_TOKEN='your_token_here'  # No spaces before/after =

# Test it:
python3 test_ncei_token.py
```

## Why is it Free?

NCEI (National Centers for Environmental Information) is part of NOAA (National Oceanic and Atmospheric Administration), a US government agency. They provide this data as a **public service** to support:

- Climate research
- Weather applications
- Educational projects
- Commercial weather services
- Anyone who needs historical climate data

The data is collected using taxpayer money, so they make it freely available to everyone.

## What Can You Do With 10,000 Requests/Day?

That's a LOT. For context:

- **This ice climbing app**: ~10-50 requests/day typical usage
- **Analyzing entire winter** (90 days × 6 locations): 540 requests
- **10 years of daily data** (3,650 days): 3,650 requests
- **Real-time monitoring** (every hour for all locations): 144 requests/day

You'd be hard-pressed to hit the limit for personal use.

## Summary

✅ **Completely FREE** - No payment ever
✅ **Instant** - Token in email within minutes
✅ **No registration** - Just email address
✅ **No expiration** - Token works forever
✅ **High limits** - 10,000 requests/day
✅ **Production ready** - Used by major weather services

**Get your token:**
https://www.ncdc.noaa.gov/cdo-web/token

**Then run:**
```bash
export NCEI_TOKEN='your_token_here'
python3 test_january_10_2025.py
```

And you'll see the ice climbing conditions for January 10, 2025! 🎉
