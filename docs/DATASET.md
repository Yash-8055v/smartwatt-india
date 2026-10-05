# Dataset Specification

## Selected dataset — FINAL
**Dataset on Information Strategies for Energy Conservation: A Field Experiment in India**

### Official download/access page
https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/7MEXN4

### Dataset paper
https://pmc.ncbi.nlm.nih.gov/articles/PMC5735253/

### Why this dataset
- Collected in New Delhi, India.
- 19 residential apartments.
- August 1, 2013 to May 12, 2014.
- Electricity consumption is available in kWh per unit time.
- Multiple frequencies are available, including 15-minute, 30-minute, hourly and daily measurements.
- Weather data is included.
- Household/apartment characteristics are included.
- The source describes the data as suitable for electricity-use modeling.

### Raw format
The dataset is provided as Stata `.dta` files. The preprocessing script must convert only the selected time-series table(s) into CSV/Parquet for application use.

### Recommended modeling frequency
**Hourly** for the main model. Reasons:
- Much smaller than 15-minute data.
- Preserves daily/hourly patterns.
- Suitable for a 2–3 day project.
- Weather variables are hourly.

Daily data may be used for secondary summaries.

### Candidate features
- `apt`
- `timestamp`
- `energy`
- `hour`
- `dayofweek`
- `hour_temp`
- `mean_daily_temp`
- household static features where appropriate
- engineered: `is_weekend`, `rolling_mean_24`, `rolling_std_24`, `lag_1`, `lag_24`

### Target
`energy` = electricity consumption in kWh per recorded time unit. Confirm the selected source table's frequency before transforming/aggregating. Do not blindly sum a variable unless its semantics and frequency are verified.

### Preprocessing rules
1. Load `.dta` with pandas.
2. Parse timestamps.
3. Sort by apartment and timestamp.
4. Check duplicate timestamps.
5. Measure missingness.
6. Remove or flag impossible/negative values only after checking source semantics.
7. Align weather at hourly frequency.
8. Create engineered temporal features.
9. Build train/validation/test splits chronologically to prevent leakage.
10. Save processed data to `data/processed/hourly_energy.csv`.

### Important methodological warning
The dataset has only 19 apartments and a finite observation period. Do not describe the model as universally representative of Indian households. Do not claim appliance-level causes or electricity theft detection.
