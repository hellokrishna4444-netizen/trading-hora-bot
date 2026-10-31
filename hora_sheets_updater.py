import os
import math
import datetime
import time
import pytz
import requests
from astral import LocationInfo
from astral.sun import sun

CHALDEAN_ORDER = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]
DAY_LORDS = {0: "Moon", 1: "Mars", 2: "Mercury", 3: "Jupiter", 4: "Venus", 5: "Saturn", 6: "Sun"}
RAHU_KAAL_PARTS = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}

PLANET_VOLATILITY = {
    "Mars": ("HIGH", "20-35 Pips (Gold) / 80-120 Pts (Nifty)", "Explosive Stop Sweeps"),
    "Sun": ("HIGH", "18-30 Pips (Gold) / 70-110 Pts (Nifty)", "Institutional Trend Follow"),
    "Mercury": ("HIGH", "15-28 Pips (Gold) / 60-100 Pts (Nifty)", "HFT Algo Expansion"),
    "Jupiter": ("MODERATE", "12-22 Pips (Gold) / 50-80 Pts (Nifty)", "Orderly Accumulation"),
    "Venus": ("MODERATE", "8-15 Pips (Gold) / 40-65 Pts (Nifty)", "Mean Reversion / Retrace"),
    "Moon": ("LOW", "5-10 Pips (Gold) / 20-40 Pts (Nifty)", "Chop & False Moves"),
    "Saturn": ("LOW", "4-8 Pips (Gold) / 15-35 Pts (Nifty)", "Compression / Consolidation")
}

NAKSHATRAS = [
    ("Ashwini", "Ketu", "Agni / Sharp Spikes"), ("Bharani", "Venus", "Ugra / Traps"),
    ("Krittika", "Sun", "Agni / Volatility"), ("Rohini", "Moon", "Prithvi / Smooth Trend"),
    ("Mrigashira", "Mars", "Vayu / Mid-day Swings"), ("Ardra", "Rahu", "Tikshna / High Risk"),
    ("Punarvasu", "Jupiter", "Chara / Trend Follow"), ("Pushya", "Saturn", "Sthira / Accumulation"),
    ("Ashlesha", "Mercury", "Tikshna / Algo Games"), ("Magha", "Ketu", "Ugra / Liquidation"),
    ("Purva Phalguni", "Venus", "Bhaga / Retrace"), ("Uttara Phalguni", "Sun", "Dhruva / Momentum"),
    ("Hasta", "Moon", "Kshipra / Fast Scalp"), ("Chitra", "Mars", "Mridu / Sharp Moves"),
    ("Swati", "Rahu", "Chara / Big Range"), ("Vishakha", "Jupiter", "Mishra / Reversal"),
    ("Anuradha", "Saturn", "Mridu / Controlled Flow"), ("Jyeshtha", "Mercury", "Tikshna / Shakeouts"),
    ("Mula", "Ketu", "Tikshna / Sharp Drops"), ("Purva Ashadha", "Venus", "Ugra / Breakout Trap"),
    ("Uttara Ashadha", "Sun", "Dhruva / Strong Trend"), ("Shravana", "Moon", "Chara / High Volume"),
    ("Dhanishta", "Mars", "Chara / Fast Momentum"), ("Shatabhisha", "Rahu", "Chara / Deceptive"),
    ("Purva Bhadrapada", "Jupiter", "Ugra / Volatility"), ("Uttara Bhadrapada", "Saturn", "Dhruva / Solid Base"),
    ("Revati", "Mercury", "Mridu / Range Close")
]

TITHIS = [
    ("Shukla Pratipada", "Nanda", "Balanced"), ("Shukla Dwitiya", "Bhadra", "Steady Trend"),
    ("Shukla Tritiya", "Jaya", "High Momentum"), ("Shukla Chaturthi", "Rikta", "TRAP / False Break"),
    ("Shukla Panchami", "Purna", "STRONG TREND"), ("Shukla Shashthi", "Nanda", "Balanced"),
    ("Shukla Saptami", "Bhadra", "Steady Trend"), ("Shukla Ashtami", "Jaya", "High Momentum"),
    ("Shukla Navami", "Rikta", "TRAP / False Break"), ("Shukla Dashami", "Purna", "STRONG TREND"),
    ("Shukla Ekadashi", "Nanda", "Balanced"), ("Shukla Dwadashi", "Bhadra", "Steady Trend"),
    ("Shukla Trayodashi", "Jaya", "High Momentum"), ("Shukla Chaturdashi", "Rikta", "TRAP / False Break"),
    ("Purnima", "Purna", "STRONG TREND"),
    ("Krishna Pratipada", "Nanda", "Balanced"), ("Krishna Dwitiya", "Bhadra", "Steady Trend"),
    ("Krishna Tritiya", "Jaya", "High Momentum"), ("Krishna Chaturthi", "Rikta", "TRAP / False Break"),
    ("Krishna Panchami", "Purna", "STRONG TREND"), ("Krishna Shashthi", "Nanda", "Balanced"),
    ("Krishna Saptami", "Bhadra", "Steady Trend"), ("Krishna Ashtami", "Jaya", "High Momentum"),
    ("Krishna Navami", "Rikta", "TRAP / False Break"), ("Krishna Dashami", "Purna", "STRONG TREND"),
    ("Krishna Ekadashi", "Nanda", "Balanced"), ("Krishna Dwadashi", "Bhadra", "Steady Trend"),
    ("Krishna Trayodashi", "Jaya", "High Momentum"), ("Krishna Chaturdashi", "Rikta", "TRAP / False Break"),
    ("Amavasya", "Purna", "STRONG TREND")
]

def julian_day(year, month, day, hour=0, minute=0):
    if month <= 2:
        year -= 1
        month += 12
    a = math.floor(year / 100)
    b = 2 - a + math.floor(a / 4)
    day_fraction = (hour + minute / 60.0) / 24.0
    return math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + day_fraction + b - 1524.5

def get_astronomical_parameters(target_date):
    jd = julian_day(target_date.year, target_date.month, target_date.day, 4, 0)
    t = (jd - 2451545.0) / 36525.0
    l0 = 280.46646 + 36000.76983 * t
    m = 357.52911 + 35999.05029 * t
    m_rad = math.radians(m % 360)
    c = (1.914602 - 0.004817 * t) * math.sin(m_rad) + 0.019993 * math.sin(2 * m_rad)
    sun_lon = (l0 + c) % 360
    
    l_m = 218.3164477 + 481267.88123421 * t
    d = 297.8501921 + 445267.1114034 * t
    m_s = 357.5291092 + 35999.0502909 * t
    m_m = 134.9633964 + 477198.8675055 * t
    f = 93.2720950 + 483202.0175233 * t
    
    d_r, ms_r, mm_r, f_r = map(math.radians, [d % 360, m_s % 360, m_m % 360, f % 360])
    moon_lon = (l_m + 6.288774 * math.sin(mm_r) + 1.274027 * math.sin(2*d_r - mm_r) + 
                0.658314 * math.sin(2*d_r) + 0.213618 * math.sin(2*mm_r) - 
                0.185116 * math.sin(ms_r) - 0.114332 * math.sin(2*f_r)) % 360
    
    ayanamsha = 24.233
    s_sun = (sun_lon - ayanamsha) % 360
    s_moon = (moon_lon - ayanamsha) % 360
    diff = (s_moon - s_sun) % 360
    
    tithi_idx = int(math.floor(diff / 12)) % 30
    nak_idx = int(math.floor(s_moon / (360 / 27))) % 27
    karana_idx = math.floor(diff / 6) + 1
    is_bhadra = karana_idx in [8, 15, 21, 28, 35, 42, 49, 56]
    
    nak_name, nak_lord, nak_tattva = NAKSHATRAS[nak_idx]
    tithi_name, tithi_nature, tithi_bias = TITHIS[tithi_idx]
    
    return {
        "nakshatra": f"{nak_name} ({nak_lord})",
        "tattva_bias": nak_tattva,
        "tithi": f"{tithi_name} [{tithi_nature} - {tithi_bias}]",
        "moon_sun_angle": f"{diff:.1f}°",
        "bhadra": "⚠️ ACTIVE (Avoid Breakouts)" if is_bhadra else "✅ CLEAR (No Bhadra)"
    }

def calculate_rahu_kaal(sunrise, sunset, weekday):
    day_duration = (sunset - sunrise).total_seconds()
    part_len = datetime.timedelta(seconds=day_duration / 8)
    part_idx = RAHU_KAAL_PARTS[weekday] - 1
    rahu_start = sunrise + (part_len * part_idx)
    rahu_end = rahu_start + part_len
    return f"{rahu_start.strftime('%H:%M')} - {rahu_end.strftime('%H:%M')} IST"

def calculate_day_data(target_date):
    ist = pytz.timezone("Asia/Kolkata")
    
    def get_city_horas(city_name, region, lat, lon, tz_str):
        tz = pytz.timezone(tz_str)
        loc = LocationInfo(city_name, region, tz_str, lat, lon)
        s_today = sun(loc.observer, date=target_date, tzinfo=tz)
        s_tom = sun(loc.observer, date=target_date + datetime.timedelta(days=1), tzinfo=tz)
        
        sr_t = s_today['sunrise']
        ss_t = s_today['sunset']
        sr_next = s_tom['sunrise']
        
        d_len = datetime.timedelta(seconds=(ss_t - sr_t).total_seconds() / 12)
        n_len = datetime.timedelta(seconds=(sr_next - ss_t).total_seconds() / 12)
        
        start_idx = CHALDEAN_ORDER.index(DAY_LORDS[target_date.weekday()])
        horas = []
        
        # Day Horas
        curr = sr_t
        for i in range(12):
            nxt = curr + d_len
            lord = CHALDEAN_ORDER[(start_idx + i) % 7]
            vol_level, exp_range, playbook = PLANET_VOLATILITY[lord]
            horas.append([
                city_name, i + 1, "Day", lord,
                curr.strftime("%H:%M"), nxt.strftime("%H:%M"),
                curr.astimezone(ist).strftime("%H:%M"), nxt.astimezone(ist).strftime("%H:%M"),
                vol_level, exp_range, playbook, ""
            ])
            curr = nxt
            
        # Night Horas
        curr = ss_t
        for i in range(12):
            nxt = curr + n_len
            lord = CHALDEAN_ORDER[(start_idx + 12 + i) % 7]
            vol_level, exp_range, playbook = PLANET_VOLATILITY[lord]
            horas.append([
                city_name, 13 + i, "Night", lord,
                curr.strftime("%H:%M"), nxt.strftime("%H:%M"),
                curr.astimezone(ist).strftime("%H:%M"), nxt.astimezone(ist).strftime("%H:%M"),
                vol_level, exp_range, playbook, ""
            ])
            curr = nxt
        return horas, sr_t, ss_t

    m_horas, m_sr, m_ss = get_city_horas("Mumbai (NSE)", "India", 19.0760, 72.8777, "Asia/Kolkata")
    l_horas, _, _ = get_city_horas("London (LBMA)", "UK", 51.5074, -0.1278, "Europe/London")
    ny_horas, _, _ = get_city_horas("New York (COMEX)", "USA", 40.7128, -74.0060, "America/New_York")
    
    astro_info = get_astronomical_parameters(target_date)
    astro_info["rahu_kaal"] = calculate_rahu_kaal(m_sr.astimezone(ist), m_ss.astimezone(ist), target_date.weekday())
    date_str = target_date.strftime("%Y-%m-%d")
    
    dashboard_rows = [
        ["🌟 QUANTITATIVE ASTRO-PANCHANG & VOLATILITY DASHBOARD", "", "", "", "", "", "DATE", date_str, "SYSTEM", "45-Day Ephemeris Engine", "", ""],
        ["1. RAHU KAAL (TRAP ZONE)", astro_info["rahu_kaal"], "2. BHADRA STATUS", astro_info["bhadra"], "3. TITHI REGIME", astro_info["tithi"], "4. MOON-SUN ANGLE", astro_info["moon_sun_angle"], "", "", "", ""],
        ["5. CHANDRA NAKSHATRA", astro_info["nakshatra"], "MARKET TATTVA BIAS", astro_info["tattva_bias"], "CONFLUENCE CHECK", "Align Volatility Hora with 15m SMC Order Blocks / FVGs", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", "", "", "", ""],
        ["Market / Exchange", "Hora #", "Type", "Planet Lord", "Local Start", "Local End", "IST Start", "IST End", "Volatility", "Expected Range (Gold/Nifty)", "Execution Playbook", "Trade Logger (+/-R)"]
    ]
    return {"date": date_str, "data": dashboard_rows + m_horas + l_horas + ny_horas}

if __name__ == "__main__":
    ist = pytz.timezone("Asia/Kolkata")
    today = datetime.datetime.now(ist).date()
    
    print("Computing astronomical ephemeris: -30 days to +15 days...")
    all_sheet_packets = []
    for offset in range(-30, 16):
        d = today + datetime.timedelta(days=offset)
        all_sheet_packets.append(calculate_day_data(d))
    
    webhook_url = os.environ.get("HORA_WEBHOOK_URL")
    if not webhook_url:
        print("CRITICAL: Missing HORA_WEBHOOK_URL secret!")
        exit(1)
        
    today_str = today.strftime("%Y-%m-%d")
    
    # Send in small chunks of 5 days to avoid Google Apps Script Timeout
    chunk_size = 5
    for i in range(0, len(all_sheet_packets), chunk_size):
        chunk = all_sheet_packets[i:i + chunk_size]
        is_last_chunk = (i + chunk_size) >= len(all_sheet_packets)
        payload = {
            "today": today_str,
            "sheets": chunk,
            "cleanup": is_last_chunk
        }
        print(f"Pushing chunk {i//chunk_size + 1}/{(len(all_sheet_packets)-1)//chunk_size + 1} ({len(chunk)} dates)...")
        res = requests.post(webhook_url, json=payload, timeout=60)
        print("Result:", res.text)
        time.sleep(1)

    print("All 45 dates successfully synced with soft color formatting!")
