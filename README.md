# Amazon Price Tracker

An automated price tracking tool that monitors Amazon product prices and sends email notifications when prices drop below your target.

## Features

- 🔍 Real-time price monitoring
- 📧 Email notifications for price drops
- 🔄 Continuous monitoring with customizable intervals
- 🛡️ Anti-detection measures
- 💱 Robust price extraction
- 🎯 Multiple fallback methods for reliable scraping

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your email configuration:
   ```properties
   EMAIL_ADDRESS=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   SMTP_ADDRESS=smtp.gmail.com
   ```

## Usage

1. Configure your target price and product URL in `price_tracker.py`
2. Run the script:
   ```bash
   python price_tracker.py
   ```

## Email Configuration

1. Enable 2-Step Verification in your Google Account
2. Generate an App Password:
   - Go to Google Account Settings
   - Security → 2-Step Verification → App Passwords
   - Generate a new password for "Mail"
3. Use this App Password in your `.env` file

## Note

- The script uses random delays and proper headers to avoid being blocked
- Price checks are performed at regular intervals (default: 30 minutes)
- Press Ctrl+C to stop monitoring
