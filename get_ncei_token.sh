#!/bin/bash
# Helper script to get and set NCEI CDO API token

echo "================================================================================"
echo "NCEI Climate Data Online (CDO) API Token Setup"
echo "================================================================================"
echo ""
echo "To access historical weather data beyond 7 days, you need a free NCEI token."
echo ""
echo "Step 1: Request a token"
echo "  Visit: https://www.ncdc.noaa.gov/cdo-web/token"
echo "  Enter your email address"
echo "  Token will be emailed to you instantly (check spam if needed)"
echo ""
echo "Step 2: Set the token as an environment variable"
echo "  Once you receive your token, run:"
echo "    export NCEI_TOKEN='your_token_here'"
echo ""
echo "Step 3: Test the token"
echo "  Run: python3 test_ncei_token.py"
echo ""
echo "Rate Limits:"
echo "  - 5 requests per second"
echo "  - 10,000 requests per day"
echo ""
echo "================================================================================"
echo ""

# Check if token is already set
if [ -z "$NCEI_TOKEN" ]; then
    echo "Status: NCEI_TOKEN is NOT set"
    echo ""
    echo "To set it now, run:"
    echo "  export NCEI_TOKEN='paste_your_token_here'"
else
    echo "Status: NCEI_TOKEN is set ✓"
    echo "Token: ${NCEI_TOKEN:0:10}... (first 10 characters)"
fi
