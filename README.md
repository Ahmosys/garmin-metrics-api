# 📊 Garmin Metrics API

A lightweight FastAPI server that exposes selected Garmin Connect health metrics via HTTP endpoints. Useful for daily automation or integration with tools like iOS Shortcuts.

---

## 🚀 Features

- Retrieve **VO2Max**, **HRV (Heart Rate Variability)**, **SpO2 (Blood Oxygen)**, and **Respiratory Rate**.
- Automatically filters respiratory rate by **time of day** to avoid duplicates.
- Designed to support **two data imports per day**.
- Works perfectly with **cron jobs**, **iOS Shortcuts**, or external automation tools.

---

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone https://github.com/ahmosys/garmin-metrics-api.git
cd garmin-metrics-api
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install fastapi uvicorn garth requests python-dotenv
```

### 3. Create `.env` file

```
GARMIN_EMAIL=your@email.com
GARMIN_PASS=yourpassword
```

### 4. Run the server

```bash
fastapi dev api.py
```

API will be available at: `http://localhost:8000`

---

## 📌 Endpoints and When to Call

| Endpoint              | Description                             | When to Call           |
|-----------------------|-----------------------------------------|------------------------|
| `/vo2max`             | VO2Max from **yesterday post-activity**               | 🕙 **10:00 AM** daily  |
| `/hrv`                | HRV (VFC) from **yesterday night**            | 🕙 **10:00 AM** daily  |
| `/spo2`               | SpO2 (oxygen level) from **yesterday night**  | 🕙 **10:00 AM** daily  |
| `/respiratory_rate`   | Today's respiratory rate<br>Filtered:<br>• 00:00–12:00 → Call at 12PM<br>• 12:00–23:59 → Call at 10PM | 🕛 **12:00 PM** and 🕙 **10:00 PM** |

---

## 📱 iOS Shortcut Integration

You can call any route via `GET` request using the **"Get Contents of URL"** action.

### Example URL (local):
```
http://192.168.1.100:8000/vo2max
```

Use Automations in iOS Shortcuts to schedule:
- Morning: `vo2max`, `hrv`, `spo2`
- Midday and evening: `respiratory_rate`

---

## 📂 Project Structure

```
main.py           # FastAPI server
.env              # Garmin credentials (not tracked)
requirements.txt  # Python dependencies
```

---

## 🔐 Security Note

**Never share your `.env` file or credentials**. For production, consider using OAuth tokens or secure secrets management.

---

## ✅ To Do

- [ ] Add additional metrics (sleep, stress, hydration)

---

## 📄 License

MIT
