import sqlite3
from typing import List, Dict, Any

class DatabaseManager:
    """Quản lý kết nối và các thao tác CRUD với SQLite."""
    def __init__(self, db_name='schedule.db'):
        # Cho phép sử dụng kết nối CSDL này chéo luồng (mặc dù ReminderThread không dùng trực tiếp)
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.init_db()

    def init_db(self):
        """Khởi tạo bảng events."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                event_name TEXT NOT NULL,
                start_time TEXT NOT NULL,  -- Lưu dưới dạng ISO string
                end_time TEXT,
                location TEXT,
                reminder_minutes INTEGER,
                is_reminded BOOLEAN DEFAULT FALSE
            )
        """)
        self.conn.commit()

    def add_event(self, data: Dict[str, Any]) -> int:
        """Thêm sự kiện mới vào CSDL."""
        sql = """
            INSERT INTO events (event_name, start_time, end_time, location, reminder_minutes)
            VALUES (?, ?, ?, ?, ?)
        """
        self.cursor.execute(sql, (
            data.get("event"),
            data.get("start-time"),
            data.get("end_time"),
            data.get("location"),
            data.get("reminder_minutes")
        ))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_all_events(self) -> List[Dict[str, Any]]:
        """Lấy tất cả sự kiện để hiển thị lịch."""
        self.cursor.execute("SELECT id, event_name, start_time, end_time, location, reminder_minutes FROM events ORDER BY start_time")
        rows = self.cursor.fetchall()
        
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    
    def delete_event(self, event_id: int):
        """Xóa sự kiện."""
        self.cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
        self.conn.commit()