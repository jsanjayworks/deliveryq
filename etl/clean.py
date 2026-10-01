"""
clean.py — turn the messy raw/ files into clean, analysis-ready data.

THIS IS YOUR CODE TO WRITE. Each function below has a docstring describing
exactly what it must do and hints for the tricky parts. Fill in the TODOs.
Run it as you go:  python etl/clean.py

Goal: produce three clean DataFrames (and optionally write them to
raw/clean/) that etl/load.py will later push into Postgres:
    - clean orders   (typed dates, numeric money, canonical status, deduped)
    - clean drivers  (real header, canonical vehicle_type)
    - clean feedback (trimmed text)

Plus a small "data quality report" printed at the end — in FDE work, telling
the client *what was wrong with their data* is half the value.

------------------------------------------------------------------------------
DEFECT CHECKLIST (everything you must handle):
  orders.csv
    [ ] order_date   -> 5 mixed formats + some blanks   (parse_dates)
    [ ] delivery_fee -> Rs. / ₹ / commas / bare numbers (parse_money)
    [ ] cost         -> same, plus some bad NEGATIVES    (parse_money + policy)
    [ ] status       -> free-typed casing + synonyms     (normalize_status)
    [ ] distance     -> mixed km/miles, UNLABELED        (parse_distance — read note)
    [ ] driver_id    -> ~5% blank                        (policy decision)
    [ ] duplicate order_id rows                          (dedupe)
  drivers.xlsx
    [ ] header is NOT on row 1 (3 junk rows on top)      (clean_drivers)
    [ ] vehicle_type inconsistent                        (normalize_vehicle)
    [ ] some drivers in orders are MISSING here          (flag_unmatched_drivers)
  feedback.csv
    [ ] leading/trailing whitespace, random UPPERCASE    (clean_feedback)
    (theme/sentiment is the LLM step later, NOT here)
------------------------------------------------------------------------------
"""

import os
import re

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(os.path.dirname(HERE), "raw")
CLEAN_DIR = os.path.join(RAW, "clean")


# ---------------------------------------------------------------------------
# Small field-level cleaners
# ---------------------------------------------------------------------------

def parse_money(series: pd.Series) -> pd.Series:
    """Convert messy money strings to float.

    Examples of input: 'Rs.124.69', '₹58.36', '1,234', '72', '47.80'
    Return: a float Series (NaN where unparseable).

    HINT: strip every char that isn't a digit, dot, or minus sign, then
          cast to float. A regex like re.sub(r'[^0-9.\\-]', '', s) per value
          works; or use series.str.replace(..., regex=True) then pd.to_numeric
          with errors='coerce'.

    NOTE on negatives: a negative COST is a data-entry error, not real.
    Decide a policy (drop the row? take abs()? set NaN and flag?) — you'll
    apply it in clean_orders(), not here. Here, just parse faithfully so a
    '-119.41' becomes -119.41 and the policy layer can see it.
    """
    # TODO: implement
    raise NotImplementedError


def parse_dates(series: pd.Series) -> pd.Series:
    """Parse the 5 mixed date formats (and blanks) into real datetimes.

    HINT: pd.to_datetime(series, errors='coerce') handles a lot. For truly
          mixed formats, pandas supports format='mixed'. Blanks become NaT.

    JUDGMENT CALL (write a comment about this — interviewers love it):
      '09/12/2024' is ambiguous — 9 Dec or 12 Sep? You cannot know from the
      data alone. State your assumption (this dataset uses day/month/year,
      so dayfirst=True) and move on. Documenting the assumption is the
      professional move; silently guessing is not.
    """
    # TODO: implement
    raise NotImplementedError


def normalize_status(series: pd.Series) -> pd.Series:
    """Collapse free-typed status into a small canonical set.

    Map everything to one of: 'delivered', 'cancelled', 'failed', 'returned'.
      'Delivered'/'delivered'/'DELIVERED'/'done'/'complete' -> 'delivered'
      'cancelled'/'Cancelled'/'CANCELLED'                   -> 'cancelled'
      'failed'                                              -> 'failed'
      'returned'                                            -> 'returned'

    HINT: lowercase + strip first, then map with a dict. Anything unexpected
          -> keep as-is or set 'unknown' (your call, but be consistent).
    """
    # TODO: implement
    raise NotImplementedError


def normalize_vehicle(series: pd.Series) -> pd.Series:
    """Collapse vehicle_type variants into canonical values.

    Inputs seen: '2-wheeler', 'bike', 'Motorcycle', 'MC', 'scooter', 'Scooter'
    These are all two-wheelers here -> map them all to 'two_wheeler'.
    HINT: lowercase + strip, then a dict/map.
    """
    # TODO: implement
    raise NotImplementedError


def parse_distance(series: pd.Series) -> pd.Series:
    """Parse distance to a float (km).

    THE HONEST ANSWER: ~15% of these values are in MILES but UNLABELED, and
    there is NO reliable way to tell which from the data alone. This is a
    real FDE lesson: some dirty data cannot be 'cleaned', only flagged.

    For now: just parse the number to float and treat it as km. Add a code
    comment noting the known unit-ambiguity risk and that you'd confirm the
    export's unit convention with the client. (Don't over-engineer a guess.)
    """
    # TODO: implement
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Table-level cleaners
# ---------------------------------------------------------------------------

def clean_orders(path: str) -> pd.DataFrame:
    """Load raw orders.csv and return a clean, typed DataFrame.

    Steps (use the helpers above):
      1. read_csv
      2. parse order_date, delivery_fee, cost, distance, status
      3. dedupe on order_id (keep first) — some rows are exact duplicates
      4. driver_id policy: blanks -> a sentinel (e.g. pd.NA / -1 'unassigned').
         Decide and be consistent; profitability-by-driver needs a bucket for these.
      5. cost negative policy: apply what you decided in parse_money's note.
      6. add a computed column: margin = delivery_fee - cost
    Return the cleaned DataFrame.
    """
    # TODO: implement
    raise NotImplementedError


def clean_drivers(path: str) -> pd.DataFrame:
    """Load raw drivers.xlsx (header is NOT on row 1) and return clean data.

    HINT: the file has 3 junk rows before the real header. Use
          pd.read_excel(path, skiprows=3) or header=3. Verify the columns
          look right (driver_id, driver_name, vehicle_type, joined, home_zone).
    Then normalize vehicle_type with normalize_vehicle().
    """
    # TODO: implement
    raise NotImplementedError


def clean_feedback(path: str) -> pd.DataFrame:
    """Load raw feedback.csv and return clean data.

    Just normalize the text here: strip whitespace. (Keep original casing OR
    lowercase — your call, but note the LLM step later does theme/sentiment,
    so don't destroy meaning.) Do NOT translate or classify here.
    """
    # TODO: implement
    raise NotImplementedError


def flag_unmatched_drivers(orders: pd.DataFrame, drivers: pd.DataFrame) -> pd.Series:
    """Return a boolean Series over `orders`: True where the order's driver_id
    does NOT exist in the drivers table (the ~5 missing drivers).

    HINT: orders['driver_id'].isin(drivers['driver_id']) inverted, being
          careful about the 'unassigned'/blank sentinel you chose.
    This feeds the data-quality report.
    """
    # TODO: implement
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Orchestration + data-quality report
# ---------------------------------------------------------------------------

def main():
    os.makedirs(CLEAN_DIR, exist_ok=True)

    orders = clean_orders(os.path.join(RAW, "orders.csv"))
    drivers = clean_drivers(os.path.join(RAW, "drivers.xlsx"))
    feedback = clean_feedback(os.path.join(RAW, "feedback.csv"))

    # ---- data quality report (print this; it's a client deliverable) ----
    # TODO: compute and print things like:
    #   - rows before/after dedupe (how many duplicates removed)
    #   - % of orders with missing/unparseable dates
    #   - count of negative-cost rows found
    #   - count of orders whose driver is unmatched in drivers.xlsx
    # These numbers go straight into FINDINGS.md later.

    # ---- write clean outputs for the load step ----
    orders.to_csv(os.path.join(CLEAN_DIR, "orders.csv"), index=False)
    drivers.to_csv(os.path.join(CLEAN_DIR, "drivers.csv"), index=False)
    feedback.to_csv(os.path.join(CLEAN_DIR, "feedback.csv"), index=False)
    print("\nClean files written to raw/clean/")


if __name__ == "__main__":
    main()
