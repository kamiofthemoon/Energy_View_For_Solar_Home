# Frontend - One Energy View

Streamlit interface for the PPC challenge "One energy view for solar homes".

Three pages:

- **Customer (app.py):** a short onboarding questionnaire, the current state (solar,
  home, battery, grid), recommendations with "Accept / Not today / Don't suggest
  again", the savings plan and tomorrow's battery plan.
- **Consumption analysis (pages/1_Consumption_analysis.py):** the 15-minute curve,
  expected vs. actual production, the hourly profile and energy per day - this is
  where you see why the customer gets the tips they get.
- **Installation monitoring (pages/2_Installation_monitoring.py):** the page for the
  operations and maintenance team: alerts sorted by what they cost (lei), the
  recommended action and the expected vs. actual chart per installation.

## Running it

```
cd frontend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Where the data comes from

The frontend picks its source on its own, in this order:

1. **The ML pipeline** - if `../ml_pipeline/out/` exists (generated with
   `cd ml_pipeline && python run_demo.py`). This is the preferred source: it has
   production, consumption, battery, grid, weather-expected production, alerts in
   lei and the personalised recommendations from `customer.json`.
2. **The FastAPI backend** - if it answers at `http://localhost:8000/health` and
   has data. To start it:

   ```
   cd backend
   pip install -r requirements.txt
   python ../frontend/tools/seed_db.py   # once: fills the database from the xlsx
   uvicorn app.main:app --reload --port 8000
   ```

3. **Simulated data** - if neither source above is available. A banner says when
   this happens, so the demo works no matter what.

Optional variables: `API_URL` (another host/port for the backend), `ML_OUT`
(another path to out/), `USE_MOCK=true` (forces simulated data).

## Prices

Every savings figure uses the tariff from `ml_pipeline/ml/tariffs.py`
(`RETAIL_LEI_KWH` and `FEED_IN_LEI_KWH`), so the questionnaire, the
recommendations and the ML results agree. If `ml_pipeline` is missing,
`config.py` falls back to the same values (1.30 and 0.30 lei/kWh).

## Look and feel

The theme lives in `components/theme.py` (fonts, cards, chart template) and the
colours in `config.py` (`COLORS` for the charts, `UI` for the interface).
Change a colour there and every page follows.

## Structure

```
frontend/
  app.py                            customer screen + questionnaire
  pages/
    1_Consumption_analysis.py       consumption and production charts
    2_Installation_monitoring.py    the maintenance team's page
  components/
    theme.py                        shared look: page setup, hero, KPI cards
    wizard.py                       onboarding questionnaire (5 steps)
    notifications.py                recommendation cards
    charts.py                       charts (plotly)
    kpi_cards.py                    number cards
  services/
    ml_source.py                    reads ml_pipeline/out/ (preferred source)
    api_client.py                   the FastAPI backend, with a mock fallback
    mock_data.py                    simulated data in the API format
  tools/seed_db.py                  fills the backend database from the PPC xlsx
  config.py                         API URL, solar window, prices, colours
```

## To discuss as a team

- The ML sites (S01-S08, simulated) and the backend sites (SITE-01/02, from the
  seed) are different lists; when both sources exist, the frontend shows the ML
  ones. Ideally the backend would also serve the ML results, so there is a single
  list.
