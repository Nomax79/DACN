import threading
import time
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox
import sqlite3 
from typing import Dict, Any, List

class ReminderThread(threading.Thread):
    """Luồng riêng chạy ngầm để kiểm tra nhắc nhở."""
    # Nhận tên DB thay vì đối tượng DBManager
    def __init__(self, db_name: str): 
        super().__init__()
        self.db_name = db_name 
        self._stop_event = threading.Event()

    def stop(self):
        """Dừng luồng nhắc nhở."""
        self._stop_event.set()

    def run(self):
        """Chạy kiểm tra định kỳ mỗi 60 giây."""
        while not self._stop_event.is_set():
            # Sử dụng wait(timeout) để thoát khỏi vòng lặp ngay khi có tín hiệu dừng
            if self._stop_event.wait(60): 
                break
            self.check_reminders()

    def check_reminders(self):
        """Truy vấn CSDL bằng kết nối cục bộ của luồng này (thread-safe)."""
        
        local_conn = None
        try:
            # TẠO KẾT NỐI MỚI CHO LUỒNG NÀY
            local_conn = sqlite3.connect(self.db_name)
            local_cursor = local_conn.cursor()
            
            events = self._get_events_for_reminder_local(local_cursor)
            
            now = datetime.now()
            
            for event in events:
                start_time = datetime.fromisoformat(event['start_time'])
                reminder_minutes = event['reminder_minutes']
                
                reminder_time = start_time - timedelta(minutes=reminder_minutes)
                
                if now >= reminder_time:
                    self.show_popup(event)
                    self._mark_as_reminded_local(local_cursor, local_conn, event['id']) 
        except Exception as e:
            # Bỏ qua lỗi trong luồng nhắc nhở để không làm treo ứng dụng chính
            pass 
        finally:
            if local_conn:
                local_conn.close() # Đảm bảo kết nối luôn được đóng

    def _get_events_for_reminder_local(self, cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
        """Lấy các sự kiện chưa được nhắc nhở bằng con trỏ cục bộ."""
        cursor.execute("SELECT id, event_name, start_time, reminder_minutes FROM events WHERE is_reminded = FALSE")
        rows = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    
    def _mark_as_reminded_local(self, cursor: sqlite3.Cursor, conn: sqlite3.Connection, event_id: int):
        """Đánh dấu sự kiện đã được nhắc nhở."""
        cursor.execute("UPDATE events SET is_reminded = TRUE WHERE id = ?", (event_id,))
        conn.commit()

    def show_popup(self, event: Dict[str, Any]):
        """Hiển thị cửa sổ pop-up thông báo."""
        
        title = "⏰ NHẮC NHỞ LỊCH TRÌNH!"
        start_dt = datetime.fromisoformat(event['start_time'])
        
        message = (
            f"Sự kiện: {event['event_name']}\n"
            f"Bắt đầu: {start_dt.strftime('%H:%M %d/%m/%Y')}\n"
            f"Nhắc trước: {event['reminder_minutes']} phút"
        )
        
        # Tạo và hủy đối tượng Tkinter trong luồng này
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(title, message)
        root.destroy()