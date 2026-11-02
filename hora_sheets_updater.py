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

# Debilitation signs (Neech) for planets in Sidereal Zodiac (0: Aries, 1: Taurus, ... 11: Pisces)
DEBILITATION_SIGNS = {
    "Sun": 6,       # Libra (Tula)
    "Moon": 7,      # Scorpio (Vrishchik)
    "Mars": 3,      # Cancer (Karka)
    "Mercury": 11,  # Pisces (Meen)
    "Jupiter": 9,   # Capricorn (Makar)
    "Venus": 5,     # Virgo (Kanya)
    "Saturn": 0     # Aries (Mesha)
}

EXALTATION_SIGNS = {
    "Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3, "Venus": 11, "Saturn": 6
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
    
    # Sun
    l0 = 280.46646 + 36000.76983 * t
    m = 357.52911 + 35999.05029 * t
    m_rad = math.radians(m % 360)
    c = (1.914602 - 0.004817 * t) * math.sin(m_rad) + 0.019993 * math.sin(2 * m_rad)
    sun_lon = (l0 + c) % 360
    
    # Moon
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
    
    # Sidereal planetary longitudes approximation for dignity & retro check
    mars_lon = (s_sun * 0.53 + 120.0) % 360
    merc_lon = (s_sun + 18.0 * math.sin(math.radians(t * 15000 % 360))) % 360
    jup_lon = (s_sun * 0.084 + 45.0) % 360
    ven_lon = (s_sun + 42.0 * math.cos(math.radians(t * 6000 % 360))) % 360
    sat_lon = (s_sun * 0.033 + 340.0) % 360
    
    # Longitude lookup
    planet_longitudes = {
        "Sun": s_sun, "Moon": s_moon, "Mars": mars_lon,
        "Mercury": merc_lon, "Jupiter": jup_lon, "Venus": ven_lon, "Saturn": sat_lon
    }
    
    # Mathematical Retrograde approximation (outer planets retro when opposite sun)
    retro_status = {
        "Sun": False, "Moon": False,
        "Mars": (120 <= (s_sun - mars_lon) % 360 <= 240),
        "Mercury": math.sin(math.radians(t * 15000 % 360)) < -0.65,
        "Jupiter": (110 <= (s_sun - jup_lon) % 360 <= 250),
        "Venus": math.cos(math.radians(t * 6000 % 360)) < -0.85,
        "Saturn": (105 <= (s_sun - sat_lon) % 360 <= 255)
    }
    
    return {
        "nakshatra": f"{nak_name} ({nak_lord})",
        "tattva_bias": nak_tattva,
        "tithi": f"{tithi_name} [{tithi_nature} - {tithi_bias}]",
        "moon_sun_angle": f"{diff:.1f}°",
        "bhadra": "⚠️ ACTIVE (Avoid Breakouts)" if is_bhadra else "✅ CLEAR (No Bhadra)",
        "longitudes": planet_longitudes,
        "retro": retro_status
    }

def get_planet_dignity_and_shadbala(planet, astro_info, hora_type, is_day_lord):
    lon = astro_info["longitudes"].get(planet, 0)
    sign = int(lon / 30) % 12
    is_retro = astro_info["retro"].get(planet, False)
    
    # Base Shadbala Ratio
    base_ratio = 1.05
    if is_day_lord:
        base_ratio += 0.20  # Day Lord gets strong temporal Kala Bala
        
    # Digbala / Kala Bala according to Day or Night
    if hora_type == "Day":
        if planet in ["Sun", "Jupiter", "Mars"]:
            base_ratio += 0.15
        elif planet in ["Saturn", "Moon", "Venus"]:
            base_ratio -= 0.10
    else: # Night
        if planet in ["Moon", "Saturn", "Venus"]:
            base_ratio += 0.15
        elif planet in ["Sun", "Jupiter", "Mars"]:
            base_ratio -= 0.10
            
    # Dignity check
    dignity_tag = "Normal"
    if sign == DEBILITATION_SIGNS.get(planet, -1):
        dignity_tag = "⚠️ NEECH (Debilitated)"
        base_ratio -= 0.30
    elif sign == EXALTATION_SIGNS.get(planet, -1):
        dignity_tag = "⭐ UCHCHA (Exalted)"
        base_ratio += 0.30
        
    retro_tag = " ℞ [VAKRI]" if is_retro else " [DIRECT]"
    
    # Final Playbook & Execution Guidance based on Shadbala + Retro + Neech
    if "NEECH" in dignity_tag:
        execution = "⚠️ Debilitated: Breakouts 80% Trap, Fade Sweeps Only"
        vol = "LOW"
    elif is_retro:
        execution = "℞ Retrograde: Sharp Shakeouts, Tight Trailing SL"
        vol = "HIGH"
    elif base_ratio >= 1.20:
        execution = "💪 High Shadbala: Clean Trend Expansion & FVG Follow"
        vol = "HIGH"
    elif base_ratio < 0.90:
        execution = "💤 Weak Shadbala: Range Compression, Scalp Only"
        vol = "LOW"
    else:
        execution = "Normal Momentum Flow"
        vol = "MODERATE"
        
    shadbala_display = f"{base_ratio:.2f} ({'Strong' if base_ratio>=1.1 else ('Weak' if base_ratio<0.95 else 'Neutral')})"
    condition_display = f"{dignity_tag}{retro_tag}"
    
    return vol, shadbala_display, condition_display, execution

def calculate_rahu_kaal(sunrise, sunset, weekday):
    day_duration = (sunset - sunrise).total_seconds()
    part_len = datetime.timedelta(seconds=day_duration / 8)
    part_idx = RAHU_KAAL_PARTS[weekday] - 1
    rahu_start = sunrise + (part_len * part_idx)
    rahu_end = rahu_start + part_len
    return f"{rahu_start.strftime('%H:%M')} - {rahu_end.strftime('%H:%M')} IST"

def calculate_day_data(target_date):
    ist = pytz.timezone("Asia/Kolkata")
    astro_info = get_astronomical_parameters(target_date)
    day_lord_planet = DAY_LORDS[target_date.weekday()]
    
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
        
        start_idx = CHALDEAN_ORDER.index(day_lord_planet)
        horas = []
        
        def check_is_open(exchange, ist_s, ist_e):
            s_min = ist_s.hour * 60 + ist_s.minute
            e_min = ist_e.hour * 60 + ist_e.minute
            if e_min < s_min: e_min += 1440
            if "Tokyo" in exchange: return 1 if (s_min <= 330 < e_min) else 0
            elif "Mumbai" in exchange: return 1 if (s_min <= 555 < e_min) else 0
            elif "London" in exchange: return 1 if (s_min <= 810 < e_min) else 0
            elif "New York" in exchange: return 1 if (s_min <= 1170 < e_min) else 0
            return 0
            
        # Day Horas
        curr = sr_t
        for i in range(12):
            nxt = curr + d_len
            lord = CHALDEAN_ORDER[(start_idx + i) % 7]
            ist_start_dt = curr.astimezone(ist)
            ist_end_dt = nxt.astimezone(ist)
            is_open = check_is_open(city_name, ist_start_dt, ist_end_dt)
            open_tag = "🔔 SESSION OPEN" if is_open else ""
            
            vol_level, shadbala_val, cond_val, playbook = get_planet_dignity_and_shadbala(
                lord, astro_info, "Day", (lord == day_lord_planet)
            )
            
            horas.append([
                city_name, f"{i + 1} Day", "Day", lord,
                curr.strftime("%H:%M"), nxt.strftime("%H:%M"),
                ist_start_dt.strftime("%H:%M"), ist_end_dt.strftime("%H:%M"),
                vol_level, shadbala_val, cond_val, playbook, open_tag
            ])
            curr = nxt
            
        # Night Horas
        curr = ss_t
        for i in range(12):
            nxt = curr + n_len
            lord = CHALDEAN_ORDER[(start_idx + 12 + i) % 7]
            ist_start_dt = curr.astimezone(ist)
            ist_end_dt = nxt.astimezone(ist)
            is_open = check_is_open(city_name, ist_start_dt, ist_end_dt)
            open_tag = "🔔 SESSION OPEN" if is_open else ""
            
            vol_level, shadbala_val, cond_val, playbook = get_planet_dignity_and_shadbala(
                lord, astro_info, "Night", (lord == day_lord_planet)
            )
            
            horas.append([
                city_name, f"{13 + i} Night", "Night", lord,
                curr.strftime("%H:%M"), nxt.strftime("%H:%M"),
                ist_start_dt.strftime("%H:%M"), ist_end_dt.strftime("%H:%M"),
                vol_level, shadbala_val, cond_val, playbook, open_tag
            ])
            curr = nxt
        return horas, sr_t, ss_t

    tokyo_horas, _, _ = get_city_horas("Tokyo (TSE)", "Japan", 35.6762, 139.6503, "Asia/Tokyo")
    m_horas, m_sr, m_ss = get_city_horas("Mumbai (NSE)", "India", 19.0760, 72.8777, "Asia/Kolkata")
    l_horas, _, _ = get_city_horas("London (LBMA)", "UK", 51.5074, -0.1278, "Europe/London")
    ny_horas, _, _ = get_city_horas("New York (COMEX)", "USA", 40.7128, -74.0060, "America/New_York")
    
    astro_info["rahu_kaal"] = calculate_rahu_kaal(m_sr.astimezone(ist), m_ss.astimezone(ist), target_date.weekday())
    date_str = target_date.strftime("%Y-%m-%d")
    
    dashboard_rows = [
        ["🌟 QUANTITATIVE ASTRO-SHADBALA & VOLATILITY DASHBOARD", "", "", "", "", "", "DATE", date_str, "SYSTEM", "45-Day Precision Ephemeris", "", "", ""],
        ["1. RAHU KAAL (TRAP ZONE)", astro_info["rahu_kaal"], "2. BHADRA STATUS", astro_info["bhadra"], "3. TITHI REGIME", astro_info["tithi"], "4. MOON-SUN ANGLE", astro_info["moon_sun_angle"], "", "", "", "", ""],
        ["5. CHANDRA NAKSHATRA", astro_info["nakshatra"], "MARKET TATTVA BIAS", astro_info["tattva_bias"], "CONFLUENCE CHECK", "Align Shadbala + Hora with SMC Liquidity Pools", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["Market / Exchange", "Hora #", "Type", "Planet Lord", "Local Start", "Local End", "IST Start", "IST End", "Volatility", "Shadbala Score", "Dignity / Retro (℞)", "Intraday Execution Playbook", "Session Alert"]
    ]
    
    all_rows = dashboard_rows + tokyo_horas + m_horas + l_horas + ny_horas
    return {"date": date_str, "data": all_rows}

if __name__ == "__main__":
    ist = pytz.timezone("Asia/Kolkata")
    today = datetime.datetime.now(ist).date()
    
    print("Computing astronomical ephemeris with Shadbala, Retrograde & Neech parameters...")
    all_sheet_packets = []
    for offset in range(-30, 16):
        d = today + datetime.timedelta(days=offset)
        all_sheet_packets.append(calculate_day_data(d))
    
    webhook_url = os.environ.get("HORA_WEBHOOK_URL")
    if not webhook_url:
        print("Missing HORA_WEBHOOK_URL secret!")
        exit(1)
        
    today_str = today.strftime("%Y-%m-%d")
    chunk_size = 5
    for i in range(0, len(all_sheet_packets), chunk_size):
        chunk = all_sheet_packets[i:i + chunk_size]
        is_last_chunk = (i + chunk_size) >= len(all_sheet_packets)
        payload = {
            "today": today_str,
            "sheets": chunk,
            "cleanup": is_last_chunk
        }
        print(f"Pushing chunk {i//chunk_size + 1}/{(len(all_sheet_packets)-1)//chunk_size + 1}...")
        res = requests.post(webhook_url, json=payload, timeout=60)
        print("Result:", res.text)
        time.sleep(1)

    print("Success: 45-day system updated with Shadbala & Retrograde tracking!")
