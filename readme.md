# Cypress Warriorz Analytics Hub 🏏

**Live Application:** [https://cypress-warriorz-dashboard.streamlit.app/](https://cypress-warriorz-dashboard.streamlit.app/)

## Project Overview
The Cypress Warriorz Analytics Hub is an end-to-end data warehousing and machine learning platform designed to deliver real-time insights and predictive modeling for sports management. Built specifically for the Cypress Warriorz cricket organization, this command center connects a robust backend data pipeline to a secure Snowflake data warehouse. It leverages custom-built machine learning algorithms to project future player trajectories, calculate optimal match lineups, and optimize game-day strategy. 

Designed with a sleek, dark-mode Gold and Black UI, the application provides an intuitive interface for data-driven decision-making on the field.

---

## 🛠 Tech Stack & Architecture

*   **Frontend / UI:** Streamlit
*   **Data Warehouse:** Snowflake
*   **Machine Learning:** Scikit-Learn (Random Forests), PyTorch
*   **Data Processing & ETL:** Python, Pandas, NumPy, RegEx
*   **Model Serialization:** Joblib
*   **Business Intelligence:** Power BI

---

## 🧠 Key Features & Intelligence Modules

### 1. Automated ETL & Data Processing
*   **Raw Data Parsing:** Custom Python extraction scripts automatically parse unstructured raw CSV match logs to isolate batting, bowling, and fielding metrics.
*   **Data Cleaning:** Dynamically handles missing values, resolves player aliases to a master roster, and standardizes match metadata (e.g., Playoff Rounds, Forfeits, Regular Season).
*   **Fantasy Points Engine:** Quantifies game-by-game impact using a custom point system factoring in strike rates, economy rates, milestones (e.g., centuries, 5-wicket hauls), fielding catches, and MOTM bonuses.

### 2. Snowflake Data Warehouse
*   **Star Schema Architecture:** Deploys a highly relational database structure featuring a master `DIM_PLAYER` table connected to dimensional contexts (`DIM_TEAM_STATS`, `DIM_MOTM`) and core fact tables (`FACT_BATTING`, `FACT_BOWLING`, `FACT_FIELDING`, `FACT_FANTASY_POINTS`).
*   **Unified Analytics View:** Utilizes a massive aggregated view (`VW_ULTIMATE_PLAYER_DASHBOARD`) that compiles career, regular season, playoff, and practice league metrics alongside dynamic batting position splits.

### 3. Player Analysis Module
*   **Historical Trends:** Monitors how individual player statistics fluctuate across games and entire seasons.
*   **Comparative Metrics:** Instantly stacks individual athletes against team averages and baseline benchmarks.
*   **Strategic Indicators:** Visualizes scoring efficiency and defensive impact to optimize playing time.

### 4. AI Projections Engine & Lineup Solver
*   **Predictive Modeling:** A machine learning pipeline generates statistically rigorous projections (Points, Runs, Wickets) based on chronological form, career averages, and opponent difficulty.
*   **Pairwise Synergy:** Calculates historical duo synergies to understand which players perform best when rostered together.
*   **Combinatorial Lineup Optimization:** Features a high-speed solver that tests thousands of roster combinations to output the statistically optimal 11-man lineup and dynamically assigns the most efficient batting order.

---
