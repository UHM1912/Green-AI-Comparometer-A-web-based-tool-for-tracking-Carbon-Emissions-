# EcoRefactor

**EcoRefactor** is a unified platform to measure, compare, and reduce the carbon footprint of ML/DL code using multiple local carbon tracking tools.

It analyzes your Python code or Jupyter Notebooks, queries the Gemini API for performance-focused, eco-friendly refactoring suggestions, and runs both versions in a local sandboxed environment to compare resource consumption and estimated CO2 emissions.

---

## Key Features

* **LLM-Powered Refactoring**: Connects to the Gemini API (`gemini-2.5-flash`) to generate structured code optimization suggestions.
* **Offline Sandbox Benchmarking**: Runs both original and optimized code in a sandboxed subprocess environment using:
  * **eco2AI**: Configured to run offline (preset ISO codes) to track local CPU power and carbon footprint.
  * **CodeCarbon**: Configured using `OfflineEmissionsTracker` to calculate RAM/CPU energy consumption.
* **Granular Metrics**: Compares median runtime, CPU execution time, peak memory usage, and energy proxy consumption (kWh).
* **Adoption Guidance**: Simulates yearly impact (hours saved, kWh saved, cost proxy) based on your custom runs-per-day and deployment environments.
* **Interactive Dashboard**: Modern Angular-based frontend with login, job history, and side-by-side code reviews.
* **PDF Reports**: Composes and downloads a styled PDF comparing performance metrics and environmental savings.

---

## Tech Stack

* **Frontend**: Angular 22, Vanilla CSS
* **Backend**: FastAPI, SQLite, Pydantic, ReportLab (for PDF generation)
* **Carbon Tracking**: `eco2ai`, `codecarbon` (running offline)
* **LLM Engine**: Google GenAI SDK (Gemini)

---

## Getting Started

### Prerequisites
* Python 3.13 or newer
* Node.js (v18+) and npm

---

### 1. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a configuration `.env` file at `backend/app/core/.env` containing your Gemini API key:
   ```env
   GEMINI_API_KEY=your-gemini-api-key-here
   ```

3. Setup a virtual environment and install dependencies:
   ```bash
   # Using uv (recommended)
   uv venv
   uv pip install -r pyproject.toml

   # Or standard pip
   python -m venv .venv
   .venv/Scripts/activate
   pip install -e .
   ```

4. Start the FastAPI server:
   ```bash
   uv run uvicorn main:app --reload
   # Or
   python main.py
   ```
   The backend API will run at `http://127.0.0.1:8000`.

---

### 2. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Angular development server:
   ```bash
   npm run start
   ```
   Open your browser and navigate to `http://localhost:4200/`.

---

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/            # Authentication and Refactoring routers
│   │   ├── core/           # Config loading, security, and logging
│   │   ├── db/             # SQLite database helper functions
│   │   ├── runners/        # Sandbox subprocess code running logic
│   │   └── services/       # Gemini LLM and PDF Report generation logic
│   ├── main.py             # FastAPI App entrypoint
│   └── pyproject.toml      # Backend python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/ # Login, Workspace, and History pages
│   │   │   └── services/   # AuthService and ApiService (HTTP clients)
│   │   └── main.ts         # Angular client bootstrap
└── README.md               # Root documentation (this file)
```

---

## 📄 License

This project is licensed under the MIT License.
