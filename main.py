import tkinter as tk
from tkinter import ttk, messagebox
from database_manager import DatabaseManager
from nlp_processor import NLPProcessor
from reminder_service import ReminderThread
from event_utils import export_to_json, export_to_ics
from datetime import datetime

class ScheduleApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ứng Dụng Quản Lý Lịch Trình (Python + NLP)")
        self.geometry("800x600")

        self.db_manager = DatabaseManager()
        self.nlp_processor = NLPProcessor()
        
        # Khởi động luồng nhắc nhở (FIX: Pass tên file DB)
        self.reminder_thread = ReminderThread(db_name='schedule.db')
        self.reminder_thread.daemon = True 
        self.reminder_thread.start()
        
        self.create_widgets()
        self.update_schedule_display()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # Khung nhập liệu (Input Frame)
        input_frame = tk.Frame(self, padx=10, pady=10)
        input_frame.pack(fill='x')

        tk.Label(input_frame, text="Nhập liệu Ngôn ngữ Tự nhiên:").pack(anchor='w')
        # Ô nhập văn bản tự do
        self.text_input = tk.Text(input_frame, height=3, width=70)
        self.text_input.pack(fill='x', pady=5)

        # Nút "Thêm sự kiện"
        add_btn = tk.Button(input_frame, text="✅ Thêm Sự Kiện", command=self.add_event_from_text)
        add_btn.pack(pady=5)

        # Khung hiển thị lịch (Schedule Frame)
        schedule_frame = tk.Frame(self, padx=10, pady=10)
        schedule_frame.pack(fill='both', expand=True)

        tk.Label(schedule_frame, text="📅 Danh Sách Lịch Trình:").pack(anchor='w')
        
        # Bảng lịch (dạng lưới)
        self.schedule_tree = ttk.Treeview(schedule_frame, columns=('Tên', 'Bắt đầu', 'Địa điểm', 'Nhắc trước'), show='headings')
        self.schedule_tree.heading('Tên', text='Tên Sự Kiện')
        self.schedule_tree.heading('Bắt đầu', text='Thời Gian Bắt Đầu')
        self.schedule_tree.heading('Địa điểm', text='Địa Điểm')
        self.schedule_tree.heading('Nhắc trước', text='Nhắc trước (Phút)')
        self.schedule_tree.pack(fill='both', expand=True, pady=5)
        
        # Nút Sửa/Xóa/Tìm kiếm
        action_frame = tk.Frame(self)
        action_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(action_frame, text="🗑️ Xóa Sự Kiện", command=self.delete_selected_event).pack(side='left', padx=5)
        ttk.Button(action_frame, text="✍️ Sửa Sự Kiện").pack(side='left', padx=5)
        ttk.Button(action_frame, text="🔎 Tìm Kiếm").pack(side='left', padx=5)
        ttk.Button(action_frame, text="⬇️ Xuất JSON", command=lambda: self.export_data('json')).pack(side='right', padx=5)
        ttk.Button(action_frame, text="⬇️ Xuất ICS", command=lambda: self.export_data('ics')).pack(side='right', padx=5)

    def add_event_from_text(self):
        """Xử lý đầu vào ngôn ngữ tự nhiên và lưu vào CSDL."""
        user_input = self.text_input.get("1.0", tk.END).strip()
        if not user_input:
            messagebox.showwarning("Lỗi", "Vui lòng nhập câu lệnh sự kiện.")
            return

        try:
            extracted_data = self.nlp_processor.process_text(user_input)
            
            self.db_manager.add_event(extracted_data)
            messagebox.showinfo("Thành công", f"Đã thêm sự kiện: {extracted_data['event']}\nThời gian: {datetime.fromisoformat(extracted_data['start-time']).strftime('%H:%M %d/%m/%Y')}")
            
            self.text_input.delete("1.0", tk.END) 
            self.update_schedule_display()
            
        except ValueError as e:
            messagebox.showerror("Lỗi NLP", str(e))
        except Exception as e:
            messagebox.showerror("Lỗi hệ thống", f"Lỗi không xác định: {e}")

    def update_schedule_display(self):
        """Cập nhật dữ liệu trên bảng lịch."""
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
            
        events = self.db_manager.get_all_events()
        
        for event in events:
            start_time_display = datetime.fromisoformat(event['start_time']).strftime('%H:%M %d/%m/%Y')
            
            self.schedule_tree.insert('', tk.END, iid=event['id'], values=(
                event['event_name'],
                start_time_display,
                event['location'] or 'N/A',
                event['reminder_minutes']
            ))

    def delete_selected_event(self):
        """Xóa sự kiện được chọn trên bảng lịch."""
        selected_item = self.schedule_tree.focus()
        if not selected_item:
            messagebox.showwarning("Lỗi", "Vui lòng chọn sự kiện muốn xóa.")
            return
            
        event_id = int(selected_item)
        if messagebox.askyesno("Xác nhận Xóa", "Bạn có chắc chắn muốn xóa sự kiện này?"):
            self.db_manager.delete_event(event_id)
            self.update_schedule_display()
            messagebox.showinfo("Thành công", "Đã xóa sự kiện.")

    def export_data(self, format_type: str):
        """Xuất dữ liệu lịch trình."""
        events = self.db_manager.get_all_events()
        if not events:
            messagebox.showwarning("Lỗi", "Không có dữ liệu để xuất.")
            return

        if format_type == 'json':
            filename = "schedule_export.json"
            export_to_json(events, filename)
            messagebox.showinfo("Thành công", f"Đã xuất dữ liệu ra file {filename}")
        elif format_type == 'ics':
            filename = "schedule_export.ics"
            export_to_ics(events, filename)
            messagebox.showinfo("Thành công", f"Đã xuất dữ liệu ra file {filename}")
            
    def on_closing(self):
        """Xử lý khi đóng ứng dụng."""
        self.reminder_thread.stop()
        self.destroy()

if __name__ == "__main__":
    app = ScheduleApp()
    app.mainloop()