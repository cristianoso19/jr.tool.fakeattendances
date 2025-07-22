# Fake Attendance Generator

This project provides utilities to generate random attendance logs and export them to Excel. A small FastAPI app is included so the tool can be used from the browser.

## Usage

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the web application:

```bash
uvicorn app:app --reload
```

3. Open `http://localhost:8000` in your browser and fill in the form to generate an Excel report.

Environment variables `SUPABASE_URL` and `SUPABASE_KEY` can be provided in a `.env` file if uploading data to Supabase is required.
