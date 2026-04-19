import requests
import csv
from datetime import date, timedelta
import time

def scrape_full_timetable():
    # Base URLs for the two different endpoints
    PRAYER_URL = "https://www.meteo.tn/horaire_gouvernorat/{}/359/632"
    SUNRISE_URL = "https://www.meteo.tn/lever_coucher_gouvernorat/{}/359/632"
    
    start_date = date(2026, 1, 1)
    end_date = date(2026, 12, 31)
    
    filename = "prayer_times_sfax_2026.csv"
    columns = ["DATE", "FAJR", "SUNRISE", "DHUHR", "ASR", "MAGHRIB", "ISHA"]
    
    print(f"Starting scrape for 2026... output file: {filename}")
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            row = {"DATE": date_str}
            
            try:
                # Get Prayer Times
                p_resp = requests.get(PRAYER_URL.format(date_str), timeout=10)
                if p_resp.status_code == 200:
                    p_data = p_resp.json().get("data", {})
                    row["FAJR"] = p_data.get("sobh", "")
                    row["DHUHR"] = p_data.get("dhohr", "")
                    row["ASR"] = p_data.get("aser", "")
                    row["MAGHRIB"] = p_data.get("magreb", "")
                    row["ISHA"] = p_data.get("isha", "")
                
                # Get Sunrise
                s_resp = requests.get(SUNRISE_URL.format(date_str), timeout=10)
                if s_resp.status_code == 200:
                    s_data = s_resp.json().get("data", {})
                    row["SUNRISE"] = s_data.get("lever", "")
                
                writer.writerow(row)
                print(f"Saved: {date_str}")
                
            except Exception as e:
                print(f"Failed to fetch {date_str}: {e}")
            
            # Sleep briefly to be respectful to the server
            time.sleep(0.2)
            current_date += timedelta(days=1)
    
    print("Done!")

if __name__ == "__main__":
    scrape_full_timetable()