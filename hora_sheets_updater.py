import os
import math
import datetime
import pytz
import requests
from astral import LocationInfo
from astral.sun import sun

CHALDEAN_ORDER = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]
DAY_LORDS = {0: "Moon", 1: "Mars", 2: "Mercury", 3: "Jupiter", 4: "Venus", 5: "Saturn", 6: "Sun"}
RAHU_KAAL_PARTS = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}

NAKSHATRAS = [
    ("Ashwini", "Ketu", "Agni / Sudden Spikes"),
    ("Bharani", "Venus", "Ugra / Aggressive Traps"),
    ("Krittika", "Sun", "Agni / Institutional Volatility"),
    ("Rohini", "Moon", "Prithvi / Smooth Trending"),
    ("Mrigashira", "Mars", "Vayu / Mid-day Rapid Swings"),
    ("Ardra", "Rahu", "Tikshna / High Risk & Whipsaws"),
    ("Punarvasu", "Jupiter", "Chara / Trend Resumption"),
    ("Pushya", "Saturn", "Sthira / Institutional Accumulation"),
    ("Ashlesha", "Mercury", "Tikshna / Heavy Algo Games"),
    ("Magha", "Ketu", "Ugra / Aggressive Liquidation"),
    ("Purva Phalguni", "Venus", "Bhaga / Profit Booking Retrace"),
    ("Uttara Phalguni", "Sun", "Dhruva / Strong Momentum Expansion"),
    ("Hasta", "Moon", "Kshipra / Fast Scalping Flow"),
    ("Chitra", "Mars", "Mridu / Sharp Technical Moves"),
    ("Swati", "Rahu", "Chara / Big Range Expansions"),
    ("Vishakha", "Jupiter", "Mishra / Swing Reversal Trials"),
    ("Anuradha", "Saturn", "Mridu / Controlled Order Flow"),
    ("Jyeshtha", "Mercury", "Tikshna / Stop Hunt & Shakeouts"),
    ("Mula", "Ketu", "Tikshna / Sudden Heavy Drops"),
    ("Purva Ashadha", "Venus", "Ugra / Breakout Failures"),
    ("Uttara Ashadha", "Sun", "Dhruva / Strong Trend Days"),
    ("Shravana", "Moon", "Chara / High Volume Follow-through"),
    ("Dhanishta", "Mars", "Chara / Fast Momentum Runs"),
    ("Shatabhisha", "Rahu", "Chara / Deceptive Price Action"),
    ("Purva Bhadrapada", "Jupiter", "Ugra / Extreme Volatility"),
    ("Uttara Bhadrapada", "Saturn", "Dhruva / Slow Solid Base"),
    ("Revati", "Mercury", "Mridu / Range Closing & Balance")
]

TITHIS = [
    "Shukla Pratipada", "Shukla Dwitiya", "Shukla Tritiya", "Shukla Chaturthi",
    "Shukla Panchami", "Shukla Shashthi", "Shukla Saptami", "Shukla Ashtami",
    "Shukla Navami", "Shukla Dashami", "Shukla Ekadashi", "Shukla Dwadashi",
    "Shukla Trayodashi", "Shukla Chaturdashi", "Purnima",
    "Krishna Pratipada", "Krishna Dwitiya", "Krishna Tritiya", "Krishna Chaturthi",
    "Krishna Panchami", "Krishna Shashthi", "Krishna Saptami", "Krishna Ashtami",
    "Krishna Navami", "Krishna Dashami", "Krishna Ekadashi", "Krishna Dwadashi",
    "Krishna Trayodashi", "Krishna Chaturdashi", "Amavasya"
]

def julian_day(year, month, day, hour=0, minute=0):
    if month <= 2:
        year -= 1
        month += 12
    A = math.floor(year / 100)
    B = 2 - A + math.floor(A / 4)
    day_fraction = (hour + minute / 60.0) / 24.0
    return math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + day_fraction + B - 1524.5

def get_astronomical_parameters(target_date):
    jd = julian_day(target_date.year, target_date.month, target_date.day, 4, 0)
    T = (jd - 2451545.0) / 36525.0
    
    L0 = 280.46646 + 36000.76983 * T
    M = 357.52911 + 35999.05029 * T
    M_rad = math.radians(M % 360)
    C = (1.914602 - 0.004817 * T) * math.sin(M_rad) + 0.019993 * math.sin(2 * M_rad)
    sun_lon = (L0 + C) % 360
    
    L_m = 218.3164477 + 481267.88123421 * T
    D = 297.8501921 + 445267.1114034 * T
    M_s = 357.5291092 + 35999.0502909 * T
    M_m = 134.9633964 + 477198.8675055 * T
    F = 93.2720950 + 483202.0175233 * T
    
    D_r, Ms_r, Mm_r, F_r = map(math.radians, [D % 360, M_s % 360, M_m % 360, F % 360])
    moon_lon = L_m + 6.288774 * math.sin(Mm_r) + 1.274027 * math.sin(2*D_r - Mm_r) + 0.658314 * math.sin(2*D_r) + 0.213618 * math.sin(2*Mm_r) - 0.185116 * math.sin(Ms_r) - 0.114332 * math.sin(2*F_r)
    moon_lon = moon_lon % 360
    
    ayanamsha = 24.233
    s_sun = (sun_lon - ayanamsha) % 360
    s_moon = (moon_lon - ayanamsha) % 360
    
    diff = (s_moon - s_sun) % 360
    tithi_idx = math.floor(diff / 12)
    nak_idx = math.floor(s_moon / (360 / 27))
    
    karana_idx = math.floor(diff / 6) + 1
    vishti_karanas = [8, 15, 21, 28, 35, 42, 49, 56]
    is_bhadra = karana_idx in vishti_karanas
    
    nak_name, nak_lord, nak_tattva = NAKSHATRAS[nak_idx]
    tithi_name = TITHIS[tithi_idx]
    
    # Gold Drivers Analysis
    weekday = target_date.weekday()
    day_ruler = DAY_LORDS[weekday]
    gold_driver = f"{day_ruler} (Day Ruler) + Jupiter (Natural Gold Karaka)"
    transit_event = f"Moon transit in Taurus (Vrishabha) -> Shifts to Mrigashira (Mars) mid-day"
    
    return {
        "nakshatra": f"{nak_name} ({nak_lord})",
        "tattva_bias": nak_tattva,
        "tithi": tithi_name,
        "moon_sun_angle": f"{diff:.1f}°",
        "bhadra": "⚠️ ACTIVE (Avoid Breakouts)" if is_bhadra else "✅ CLEAR (No Bhadra)",
        "gold_driver": gold_driver,
        "transit_event": transit_event
    }

def calculate_rahu_kaal(sunrise, sunset, weekday):
    day_duration = (sunset - sunrise).total_seconds()
    part_len = datetime.timedelta(seconds=day_duration / 8)
    part_idx = RAHU_KAAL_PARTS[weekday] - 1
    rahu_start = sunrise + (part_len * part_idx)
    rahu_end = rahu_start + part_len
    return f"{rahu_start.strftime('%H:%M')} - {rahu_end.strftime('%H:%M')} IST"

def calculate_24_horas(city_name, region, lat, lon, tz_str, target_date):
    tz = pytz.timezone(tz_str)
    ist = pytz.timezone("Asia/Kolkata")
    loc = LocationInfo(city_name, region, tz_str, lat, lon)
    
    s_today = sun(loc.observer, date=target_date, tzinfo=tz)
    s_tomorrow = sun(loc.observer, date=target_date + datetime.timedelta(days=1), tzinfo=tz)
    
    sunrise_today = s_today['sunrise']
    sunset_today = s_today['sunset']
    sunrise_tomorrow = s_tomorrow['sunrise']
    
    day_duration = (sunset_today - sunrise_today).total_seconds()
    night_duration = (sunrise_tomorrow - sunset_today).total_seconds()
    
    day_hora_len = datetime.timedelta(seconds=day_duration / 12)
    night_hora_len = datetime.timedelta(seconds=night_duration / 12)
    
    day_of_week = target_date.weekday()
    start_idx = CHALDEAN_ORDER.index(DAY_LORDS[day_of_week])
    
    horas = []
    curr_start = sunrise_today
    for i in range(12):
        curr_end = curr_start + day_hora_len
        horas.append([
            city_name, i + 1, "Day", CHALDEAN_ORDER[(start_idx + i) % 7],
            curr_start.strftime("%H:%M"), curr_end.strftime("%H:%M"),
            curr_start.astimezone(ist).strftime("%H:%M"), curr_end.astimezone(ist).strftime("%H:%M")
        ])
        curr_start = curr_end
        
    curr_start = sunset_today
    for i in range(12):
        curr_end = curr_start + night_hora_len
        horas.append([
            city_name, 13 + i, "Night", CHALDEAN_ORDER[(start_idx + 12 + i) % 7],
            curr_start.strftime("%H:%M"), curr_end.strftime("%H:%M"),
            curr_start.astimezone(ist).strftime("%H:%M"), curr_end.astimezone(ist).strftime("%H:%M")
        ])
        curr_start = curr_end
        
    return horas, sunrise_today, sunset_today

def push_to_sheets(date_str, astro_data, payload):
    webhook_url = os.environ.get("HORA_WEBHOOK_URL")
    if not webhook_url:
        exit(1)
        
    dashboard_rows = [
        ["🌟 GOLD & MARKET ASTRO INTELLIGENCE DASHBOARD", "", "", "", "", "DATE", date_str, ""],
        ["🥇 GOLD PRIMARY DRIVER", astro_data["gold_driver"], "🪐 INGRESS / TRANSIT", astro_data["transit_event"], "BHADRA STATUS", astro_data["bhadra"], "", ""],
        ["1. RAHU KAAL (TRAP ZONE)", astro_data["rahu_kaal"], "2. CHANDRA NAKSHATRA", astro_data["nakshatra"], "3. TATTVA / BIAS", astro_data["tattva_bias"], "4. MOON-SUN ANGLE", astro_data["moon_sun_angle"]],
        ["5. TITHI", astro_data["tithi"], "STRATEGY CONFLUENCE", "Align Mars/Sun Horas with 1m/5m SMC Order Blocks & Sweeps", "", "", "", ""],
        ["", "", "", "", "", "", "", ""],
        ["Market / Exchange", "Hora #", "Type", "Planet Lord", "Local Start", "Local End", "IST Start", "IST End"]
    ]
    
    all_rows = dashboard_rows + payload
    packet = {"date": date_str, "data": all_rows}
    
    print(f"Syncing master astro data for {date_str}...")
    response = requests.post(webhook_url, json=packet, timeout=30)
    print("Apps Script Response:", response.text)

if __name__ == "__main__":
    ist = pytz.timezone("Asia/Kolkata")
    today = datetime.datetime.now(ist).date()
    today_str = today.strftime("%Y-%m-%d")
    
    mumbai_horas, m_sr, m_ss = calculate_24_horas("Mumbai (NSE)", "India", 19.0760, 72.8777, "Asia/Kolkata", today)
    london_horas, _, _ = calculate_24_horas("London (LBMA)", "UK", 51.5074, -0.1278, "Europe/London", today)
    ny_horas, _, _ = calculate_24_horas("New York (COMEX)", "USA", 40.7128, -74.0060, "America/New_York", today)
    
    astro_info = get_astronomical_parameters(today)
    astro_info["rahu_kaal"] = calculate_rahu_kaal(m_sr.astimezone(ist), m_ss.astimezone(ist), today.weekday())
    
    push_to_sheets(today_str, astro_info, mumbai_horas + london_horas + ny_horas)
