# FixMyCSV

A CLI-based data cleaning assistant for small retail businesses. It helps identify data quality issues, get AI-powered cleaning suggestions, and clean CSV files with user approval.

## Features

- **CSV Inspection:** View columns, data types, missing values, and unique values.
- **Issue Detection:** Identify missing values, inconsistent formatting, duplicate rows, and negative numeric values.
- **AI Suggestions:** Get cleaning recommendations using Google Gemma.
- **Safe Cleaning:** Preview proposed changes and approve them before saving a cleaned copy.
- **Business Rules:** Store and retrieve business-specific cleaning rules using Backboard.
- **Cleaning History:** Track cleaning operations using SQLite.

## Tech Stack

Python, Pandas, Google Gemma, Backboard, SQLite, Rich, Questionary.

## Setup

```bash
git clone <https://github.com/me-hem/FixMyCSV>
cd FixMyCSV

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file with the API credentials required by your configuration. Do not commit this file.

```env
GEMMA_API_KEY=your_gemma_api_key
GEMMA_MODEL=your_gemma_model
BACKBOARD_API_KEY=your_backboard_api_key
BACKBOARD_ASSISTANT_ID=your_assistant_id
```

## Usage

Run the application:

```bash
python fixmycsv.py
```

Follow the interactive menu to inspect, analyze, preview, and clean CSV files.

