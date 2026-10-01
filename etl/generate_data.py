"""
generate_data.py — produces the three DELIBERATELY MESSY raw files.

This stands in for a real client's ugly data export. The defects here are
intentional — cleaning them is the actual job (see etl/clean.py).

Run:
    python etl/generate_data.py

Outputs:
    raw/orders.csv      ~15,000 delivery records, with mixed formats & dirt
    raw/drivers.xlsx    driver/vehicle info, junk header rows, inconsistent types
    raw/feedback.csv    free-text customer feedback, code-mixed languages

Everything is seeded, so re-running produces the same files.
"""

import os
import random
from datetime import datetime, timedelta

import pandas as pd

SEED = 42
random.seed(SEED)

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(os.path.dirname(HERE), "raw")
os.makedirs(RAW, exist_ok=True)

N_ORDERS = 15000
N_DRIVERS = 60
N_CUSTOMERS = 2500
START = datetime(2024, 1, 1)
END = datetime(2024, 12, 31)

# Hyderabad-ish zones (nod to the OMLVS domain)
ZONES = [
    "Gachibowli", "Madhapur", "HITEC City", "Kondapur", "Kukatpally",
    "Secunderabad", "Begumpet", "Banjara Hills", "Jubilee Hills", "Ameerpet",
    "LB Nagar", "Dilsukhnagar", "Uppal", "Miyapur", "Manikonda",
]

# A few routes are engineered to be money-losers (the "finding" the client pays for).
# High cost, low fee -> negative margin. clean.py / SQL should surface these.
LOSER_ROUTES = [
    ("Uppal", "Miyapur"),      # long cross-city
    ("LB Nagar", "Kukatpally"),
    ("Manikonda", "Secunderabad"),
]

# A couple of drivers are engineered to be unprofitable (slow, high cost).
LOSER_DRIVERS = {7, 23}


def _messy_date(dt: datetime) -> str:
    """Return the date in one of several inconsistent formats (or blank)."""
    r = random.random()
    if r < 0.03:
        return ""  # missing
    fmt = random.choice([
        "%Y-%m-%d",          # 2024-03-01
        "%d/%m/%Y",          # 01/03/2024
        "%B %d %Y",          # March 1 2024
        "%m-%d-%Y",          # 03-01-2024
        "%d-%b-%Y",          # 01-Mar-2024
    ])
    return dt.strftime(fmt)


def _messy_money(value: float) -> str:
    """Return a money value with inconsistent formatting; sometimes a bad negative."""
    r = random.random()
    if r < 0.02:
        # data-entry error: negative cost that makes no sense
        value = -abs(value)
    style = random.random()
    if style < 0.25:
        return f"Rs.{value:,.2f}"          # Rs.1,234.50
    if style < 0.45:
        return f"₹{value:.2f}"             # ₹1234.50
    if style < 0.60:
        return f"{value:,.0f}"             # 1,234
    return f"{value:.2f}"                  # 1234.50


def _messy_status() -> str:
    return random.choice([
        "Delivered", "delivered", "DELIVERED", "done", "complete",
        "Delivered", "delivered",  # weight toward delivered
        "cancelled", "Cancelled", "CANCELLED", "failed", "returned",
    ])


def _messy_distance(km: float) -> str:
    """Mixed units: mostly km, sometimes miles, unlabeled."""
    if random.random() < 0.15:
        miles = km * 0.621371
        return f"{miles:.1f}"  # unlabeled miles — a trap
    return f"{km:.1f}"


def build_orders() -> pd.DataFrame:
    rows = []
    span_days = (END - START).days
    for i in range(N_ORDERS):
        order_dt = START + timedelta(
            days=random.randint(0, span_days),
            minutes=random.randint(0, 1440),
        )
        pickup = random.choice(ZONES)
        drop = random.choice([z for z in ZONES if z != pickup])

        driver_id = random.randint(1, N_DRIVERS)
        customer_id = random.randint(1, N_CUSTOMERS)

        # base economics
        distance_km = round(random.uniform(1.5, 22.0), 1)
        base_fee = 25 + distance_km * random.uniform(6, 11)
        base_cost = 15 + distance_km * random.uniform(5, 9)

        # inject the engineered losers
        if (pickup, drop) in LOSER_ROUTES or (drop, pickup) in LOSER_ROUTES:
            base_cost *= random.uniform(1.6, 2.2)
            base_fee *= random.uniform(0.7, 0.9)
        if driver_id in LOSER_DRIVERS:
            base_cost *= random.uniform(1.3, 1.7)

        order_id = 100000 + i

        row = {
            "order_id": order_id,
            "order_date": _messy_date(order_dt),
            "pickup_zone": pickup,
            "drop_zone": drop,
            # ~5% missing driver
            "driver_id": "" if random.random() < 0.05 else driver_id,
            "customer_id": customer_id,
            "distance": _messy_distance(distance_km),
            "delivery_fee": _messy_money(base_fee),
            "cost": _messy_money(base_cost),
            "status": _messy_status(),
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # inject ~1.5% duplicate rows (same order logged twice)
    dupes = df.sample(frac=0.015, random_state=SEED)
    df = pd.concat([df, dupes], ignore_index=True)
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)  # shuffle
    return df


def build_drivers() -> pd.DataFrame:
    vehicle_variants = ["2-wheeler", "bike", "Motorcycle", "MC", "scooter", "Scooter"]
    names = [
        "Ravi", "Suresh", "Anil", "Kiran", "Vijay", "Mahesh", "Naveen", "Praveen",
        "Rajesh", "Sai", "Arjun", "Karthik", "Vamsi", "Teja", "Harsha", "Rohit",
    ]
    rows = []
    # Note: only create ~55 of 60 driver IDs -> some drivers in orders are MISSING here
    present_ids = sorted(random.sample(range(1, N_DRIVERS + 1), 55))
    for did in present_ids:
        rows.append({
            "driver_id": did,
            "driver_name": f"{random.choice(names)} {random.choice(['K','R','S','M','P'])}.",
            "vehicle_type": random.choice(vehicle_variants),
            "joined": (START - timedelta(days=random.randint(30, 900))).strftime(
                random.choice(["%Y-%m-%d", "%d/%m/%Y"])
            ),
            "home_zone": random.choice(ZONES),
        })
    return pd.DataFrame(rows)


def write_drivers_with_junk(df: pd.DataFrame, path: str):
    """Write xlsx with 3 junk rows on top so the header is NOT on row 1."""
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        # junk preamble (classic exported-report cruft)
        junk = pd.DataFrame({
            "A": ["Confidential - Internal Use Only", "", "Driver Master — exported 2025-01-03"],
        })
        junk.to_excel(writer, sheet_name="Sheet1", index=False, header=False, startrow=0)
        df.to_excel(writer, sheet_name="Sheet1", index=False, startrow=3)


FEEDBACK_TEMPLATES = [
    # english
    "Delivery was very late, waited almost an hour.",
    "Driver was rude on the phone.",
    "Food arrived cold and packaging was damaged.",
    "Great service, super fast delivery!",
    "Charged more than what was shown in the app.",
    "Order never arrived, had to cancel.",
    "Perfect, driver was polite and quick.",
    "Items were missing from my order.",
    # code-mixed telugu/hindi/english (nods to your resume)
    "Delivery chala late ayindi, 1 hour wait chesanu.",   # te
    "Bhaiya bahut late aaya, khana thanda ho gaya.",       # hi
    "Driver manchiga matladadu, thanks.",                   # te
    "Paisa zyada liya app se jyada, galat hai.",            # hi
    "Package damage ayindi, refund kavali.",                # te
    "Bahut accha service tha, fast delivery.",              # hi
    "Order raaledu, cancel cheyyal si vచ్చింది.",           # te (mixed script)
]


def build_feedback() -> pd.DataFrame:
    rows = []
    n = 1800
    for i in range(n):
        cust = random.randint(1, N_CUSTOMERS)
        text = random.choice(FEEDBACK_TEMPLATES)
        # some noise: trailing spaces, inconsistent casing
        if random.random() < 0.2:
            text = text.upper()
        if random.random() < 0.2:
            text = "  " + text + "   "
        rows.append({
            "feedback_id": 500000 + i,
            "customer_id": cust,
            "comment": text,
        })
    return pd.DataFrame(rows)


def main():
    print("Generating messy data into:", RAW)

    orders = build_orders()
    orders_path = os.path.join(RAW, "orders.csv")
    orders.to_csv(orders_path, index=False)
    print(f"  orders.csv    {len(orders):>6} rows")

    drivers = build_drivers()
    drivers_path = os.path.join(RAW, "drivers.xlsx")
    write_drivers_with_junk(drivers, drivers_path)
    print(f"  drivers.xlsx  {len(drivers):>6} rows (+3 junk header rows)")

    feedback = build_feedback()
    feedback_path = os.path.join(RAW, "feedback.csv")
    feedback.to_csv(feedback_path, index=False)
    print(f"  feedback.csv  {len(feedback):>6} rows")

    print("\nDone. These files are deliberately dirty — clean them in etl/clean.py.")


if __name__ == "__main__":
    main()
