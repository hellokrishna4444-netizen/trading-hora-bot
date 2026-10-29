import os
import datetime
import pytz
import requests
from astral import LocationInfo
from astral.sun import sun

CHALDEAN_ORDER = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]

DAY_LORDS = {
    0: "Moon",     # Monday
    1: "Mars",     # Tuesday
    2: "Mercury",  # Wednesday
    3: "Jupiter",  # Thursday
    4: "Venus",    # Friday
    5: "Saturn",   # Saturday
    6: "Sun"       # Sunday
}

def calculate_24_horas(city_name, region, lat, lon, tz_str, target_date):
    tz = pytz.timezone(tz_str)
    ist = pytz.timezone("Asia/Kolkata")
    loc = LocationInfo(city_name, region, tz_str, lat, lon)
    
    s_today = sun(loc.observer, date=target_date, tzinfo=tz)
    s_tomorrow = sun(loc.observer, date=target_date + datetime.timedelta(days=1), tzinfo=tz)
    
    sunrise_today = s_today['sunrise']
    sunset_today = s_today['sunset']
    sunrise_tomorrow = s_tomorrow['sunrise']
    
    # दिनमान (Day duration) और रात्रिमान (Night duration)
    day_duration = (sunset_today - sunrise_today).total_seconds()
    night_duration = (sunrise_tomorrow - sunset_today).total_seconds()
    
    day_hora_len = datetime.timedelta(seconds=day_duration / 12)
    night_hora_len = datetime.timedelta(seconds=night_duration / 12)
    
    day_of_week = target_date.weekday()
    first_lord = DAY_LORDS[day_of_week]
    start_idx = CHALDEAN_ORDER.index(first_lord)
    
    horas = []
    
    # दिन की 12 होरा
    curr_start = sunrise_today
    for i in range(12):
        curr_end = curr_start + day_hora_len
        lord = CHALDEAN_ORDER[(start_idx + i) % 7]
        horas.append([
            city_name, i + 1, "Day", lord,
            curr_start.strftime("%H:%M"), curr_end.strftime("%H:%M"),
            curr_start.astimezone(ist).strftime("%H:%M"), curr_end.astimezone(ist).strftime("%H:%M")
        ])
        curr_start = curr_end
        
    # रात की 12 होरा
    curr_start = sunset_today
    for i in range(12):
        curr_end = curr_start + night_hora_len
        lord = CHALDEAN_ORDER[(start_idx + 12 + i) % 7]
        horas.append([
            city_name, 13 + i, "Night", lord,
            curr_start.strftime("%H:%M"), curr_end.strftime("%H:%M"),
            curr_start.astimezone(ist).strftime("%H:%M"), curr_end.astimezone(ist).strftime("%H:%M")
        ])
        curr_start = curr_end
        
    return horas

def push_to_sheets(payload):
    webhook_url = os.environ.get("HORA_WEBHOOK_URL")
    if not webhook_url:
        print("CRITICAL: HORA_WEBHOOK_URL environment variable is missing or empty!")
        exit(1)
        
    headers = ["Market / Exchange", "Hora #", "Type", "Planet Lord", "Local Start", "Local End", "IST Start", "IST End"]
    all_rows = [headers] + payload
    
    print(f"Sending {len(all_rows)} rows to Google Sheets...")
    response = requests.post(webhook_url, json=all_rows, timeout=30)
    print("Apps Script Response:", response.text)
    if response.status_code != 200:
        print(f"Failed with status code: {response.status_code}")
        exit(1)

if __name__ == "__main__":
    ist = pytz.timezone("Asia/Kolkata")
    today = datetime.datetime.now(ist).date()
    
    mumbai = calculate_24_horas("Mumbai (NSE)", "India", 19.0760, 72.8777, "Asia/Kolkata", today)
    london = calculate_24_horas("London (LBMA)", "UK", 51.5074, -0.1278, "Europe/London", today)
    ny = calculate_24_horas("New York (COMEX)", "USA", 40.7128, -74.0060, "America/New_York", today)
    
    combined_horas = mumbai + london + ny
    push_to_sheets(combined_horas)
