import json
from datetime import datetime
from typing import List, Dict, Any

# Cần thư viện icalendar (pip install icalendar) cho file .ics
# from icalendar import Calendar, Event

def export_to_json(events: List[Dict[str, Any]], filename: str):
    """Xuất danh sách sự kiện ra file JSON."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=4)

def export_to_ics(events: List[Dict[str, Any]], filename: str):
    """Xuất danh sách sự kiện ra file .ics (Cần thư viện icalendar)."""
    # Khung sườn, cần cài đặt icalendar
    # cal = Calendar()
    # for event_data in events:
    #     event = Event()
    #     event.add('summary', event_data['event_name'])
    #     event.add('dtstart', datetime.fromisoformat(event_data['start_time']))
    #     # ... thêm location, description, ...
    #     cal.add_component(event)
    # 
    # with open(filename, 'wb') as f:
    #     f.write(cal.to_ical())
    print(f"Đã xuất ra {filename} (cần thư viện icalendar).")