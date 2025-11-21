# 📊 Solar Energy App

Interactive web application built with Python + Streamlit to simulate the
daily energy balance of an off-grid solar system with battery storage.

The app reads two Excel files and automatically:
  - Summarize the daily energy consumption of all loads.
  - Reads the daily PV energy generation for a 1 kW panel and scales it to the real panel size.
  - Applies the overall system efficiency (PV · cabling · MPPT · battery).
  - Computes the daily demand including losses.
  - Calculates the daily energy balance (generation − demand).
  - Simulates the battery State of Charge (SoC) day by day.
  - Counts the days without supply.
  - Generates multiple interactive charts:
      - PV Generation vs Energy demand
      - Battery SoC evolution
      - Daily energy balance: surplus/deficit
      - System autonomy evolution: PV power vs battery capacity
---

## ▶️ How to Run the Application

### 1. Open VSCode terminal and clone the repository
```bash
git clone https://github.com/kerrifai/SolarTrackerApp.git

cd SolarTrackerApp
```

### 2. Create a virtual environment and activate it.
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Place the required excel files into the project.
Ensure the following files exist in the project root and verify that filenames remain exactly the same.
  - consumo_diario.xlsx
  - energia_generada.xlsx

### 5 .Run the Streamlit app
```bash
streamlit run app.py
```

