from underthesea import word_tokenize, ner
from datetime import datetime, timedelta
import re
import unicodedata
from typing import Dict, Any, List

# Hàm loại bỏ dấu tiếng Việt (Hỗ trợ cho việc so sánh)
def remove_accents(input_str):
    if not input_str: return ""
    s = unicodedata.normalize('NFD', str(input_str))
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')

class NLPProcessor:
    """
    Module xử lý Ngôn ngữ tự nhiên tiếng Việt (Hybrid Architecture).
    Tích hợp và cải tiến logic để xử lý hiệu quả văn bản có dấu và không dấu, 
    và phân tích ngày giờ/địa điểm/sự kiện chính xác.
    """
    
    def __init__(self):
        # 1. KHỞI TẠO TỪ ĐIỂN VÀ MẪU CHUNG
        
        # Mẫu cho Nhắc nhở (Bao gồm 'p' cho phút)
        self.reminder_pattern = re.compile(r'(nhắc trước|trước|nhac truoc)\s*(\d+)\s*(phút|giờ|ngày|\'|p|h|gio|ngay)', re.IGNORECASE)
        # Mẫu cho Thời gian (hỗ trợ h, g, giờ, gio, :, am, pm)
        self.time_pattern = re.compile(r'(\d{1,2}\s*(h|gio|g|:\d{2}|giờ|phút|phut|am|pm))', re.IGNORECASE)
        # Mẫu cho Địa điểm (dựa trên giới từ)
        self.location_pattern_base = r'(ở|o|tại|tai|trong|trong|vị trí|vi tri|tuyến)\s+([\w\s,./-]+)'
        self.location_pattern = re.compile(self.location_pattern_base, re.IGNORECASE)
        
        # Ánh xạ ngày trong tuần (ưu tiên từ có dấu / đầy đủ trước để tránh match nhầm)
        self.day_map = {
            'chủ nhật': 6, 'chu nhat': 6, 'nhật': 6, 'cn': 6,
            'thứ hai': 0, 'thứ 2': 0, 'hai': 0, '2': 0, 't2': 0,
            'thứ ba': 1, 'thứ 3': 1, 'ba': 1, '3': 1, 't3': 1,
            'thứ tư': 2, 'thứ 4': 2, 'tư': 2, 'tu': 2, '4': 2, 't4': 2,
            'thứ năm': 3, 'thứ 5': 3, 'năm': 3, 'nam': 3, '5': 3, 't5': 3,
            'thứ sáu': 4, 'thứ 6': 4, 'sáu': 4, 'sau': 4, '6': 4, 't6': 4,
            'thứ bảy': 5, 'thứ 7': 5, 'bảy': 5, 'bay': 5, '7': 5, 't7': 5,
        }

        # Tạo danh sách key đã sort theo độ dài giảm dần để match chuỗi dài trước (tránh trùng trong từ khác)
        self.sorted_day_keys = sorted(self.day_map.keys(), key=lambda x: -len(x))

        # 2. ÁNH XẠ CHUẨN HÓA (Dùng cho Component 0)
        self.accent_map = {
            r"\bt2\b": "thứ 2", r"\bt3\b": "thứ 3", r"\bt4\b": "thứ 4",
            r"\bt5\b": "thứ 5", r"\bt6\b": "thứ 6", r"\bt7\b": "thứ 7",
            r"\bcn\b": "chủ nhật", r"\bchunhat\b": "chủ nhật",
            r"\bhom nay\b": "hôm nay", r"\bngay mai\b": "ngày mai",
            r"\btuan sau\b": "tuần sau", r"\bcuoi tuan\b": "cuối tuần",
            r"\bphut\b": "phút", r"\bgio\b": "giờ", r"\bh\b": "giờ",
            r"\bsang\b": "sáng", r"\btrua\b": "trưa", r"\bchieu\b": "chiều", r"\btoi\b": "tối"
        }

    # -------------------------------------------------------------
    # COMPONENT 0: CHUẨN HÓA VĂN BẢN 
    # -------------------------------------------------------------
    def _component_0_normalize_text(self, text: str) -> str:
        if not text: return ""

        text = text.lower()
        for pattern, replacement in self.accent_map.items():
            text = re.sub(pattern, replacement, text)

        text = re.sub(r'[",\'.?!]', ' ', text).strip()
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    # -------------------------------------------------------------
    # COMPONENT 1: PHÂN ĐOẠN TỪ 
    # -------------------------------------------------------------
    def _component_1_preprocessing(self, text: str) -> List[str]:
        tokens = word_tokenize(text, format="text")
        return tokens.split()

    # -------------------------------------------------------------
    # COMPONENT 2: TRÍCH XUẤT THỰC THỂ 
    # -------------------------------------------------------------
    def _component_2_ner_extraction(self, text: str) -> Dict[str, str]:
        ners = ner(text)
        extracted = {"TIME": [], "LOCATION": []}
        location_str = ""
        
        # --- 2a. Trích xuất Model-based ---
        for item in ners:
            word, tag = item[0], item[-1]
            if tag in ["B-LOC", "I-LOC"]:
                extracted["LOCATION"].append(word)
            elif tag in ["B-TIME", "I-TIME"]:
                extracted["TIME"].append(word)
        
        location_str = " ".join(extracted["LOCATION"]).strip()

        # --- 2b. Trích xuất Rule-based (Fallback cho Location) ---
        match = self.location_pattern.search(text)
        if match:
            rule_loc = match.group(2).strip()
            if not location_str or len(rule_loc.split()) > len(location_str.split()):
                location_str = rule_loc

        # --- 2c. Tinh chỉnh Location ---
        if location_str:
            # Loại bỏ các cụm nhắc nhở
            location_str = re.sub(r'(nhắc trước|trước)\s*\d+\s*(phút|giờ|ngày|\'|p)', '', location_str, flags=re.IGNORECASE).strip()
            
            # Loại bỏ các cụm liên quan đến thời gian/liên kết thừa
            location_str = re.sub(r'(vào lúc|lúc)\s*(\d{1,2}\s*(h|giờ|gio|g|:\d{2}|am|pm))', '', location_str, flags=re.IGNORECASE).strip()
            location_str = re.sub(r'(\d{1,2}\s*(h|giờ|gio|g|:\d{2}|am|pm))', '', location_str, flags=re.IGNORECASE).strip()
            location_str = re.sub(r'\b(lúc)\b', '', location_str, flags=re.IGNORECASE).strip()

            # Loại bỏ các cụm ngày trong tuần
            day_keywords = '|'.join(self.sorted_day_keys)
            day_removal_pattern = re.compile(
                r'(hôm nay|ngày mai|hom nay|ngay mai|sáng mai|chiều mai|cuối tuần|cuoi tuan|'
                r'((thứ|t)\s*|thứ\s*)?\s*(' + day_keywords + r')\s*(tuần này|tuan nay|tuần sau|tuan sau)?)', 
                flags=re.IGNORECASE 
            )
            location_str = day_removal_pattern.sub(" ", location_str).strip()

            # Dọn dẹp cuối cùng
            location_str = re.sub(r'\s+', ' ', location_str).strip()

        return {
            "time_str": " ".join(extracted["TIME"]),
            "location": location_str if location_str else None
        }

    # -------------------------------------------------------------
    # COMPONENT 3: TRÍCH XUẤT LUẬT & TIÊU ĐỀ 
    # -------------------------------------------------------------
    def _component_3_rule_extraction(self, text: str, location_str: str) -> Dict[str, Any]:
        results = {"event": None, "reminder_minutes": None}
        
        # 3a. Trích xuất thời gian nhắc nhở 
        match = self.reminder_pattern.search(text)
        if match:
            amount = int(match.group(2))
            unit = match.group(3).lower()
            
            if any(u in unit for u in ['phút', 'phut', '\'', 'p']):
                results["reminder_minutes"] = amount
            elif any(u in unit for u in ['giờ', 'h', 'gio', 'tieng']): 
                results["reminder_minutes"] = amount * 60 
            elif any(u in unit for u in ['ngày', 'ngay']): 
                results["reminder_minutes"] = amount * 24 * 60
            
            # Loại bỏ cụm nhắc nhở khỏi văn bản
            text = self.reminder_pattern.sub(" ", text).strip()
        
        # 3b. Trích xuất tên sự kiện 
        
        # Loại bỏ Địa điểm (đã tinh chỉnh) khỏi văn bản trước
        if location_str:
             text = re.sub(re.escape(location_str), " ", text, flags=re.IGNORECASE).strip()

        # Mẫu loại bỏ tăng cường cho Tiêu đề
        day_keywords = '|'.join(self.sorted_day_keys)
        removal_pattern = re.compile(
            r'(nhắc tôi|add|tôi muốn|vào lúc|lúc|ở|tại|trong|về|của|cho tôi|giùm|'
            r'ngày mai|hôm nay|sáng mai|chiều|sáng|tối|cuối tuần|'
            r'((thứ|t)\s*|thứ\s*)?\s*(' + day_keywords + r')\s*(tuần này|tuần sau)?|' 
            r'\d{1,2}\s*(h|giờ|gio|g|:\d{2}|am|pm)|' 
            r'\b(phòng|c02|p\d+|vị trí|chỗ|nhắc trước|phút|giờ|ngày|\'|lên lịch|ghi chú|thêm sự kiện|đặt lịch|nhắc nhở)\b|'
            r'\b(tôi|sự kiện|buổi|một|về|vào|của|tại|với|đi|đến|về|qua)\b)', 
            flags=re.IGNORECASE 
        )
        
        event_name = removal_pattern.sub(" ", text).strip()
        
        # Dọn dẹp cuối cùng
        event_name = re.sub(r'\s+', ' ', event_name).strip()
        event_name = re.sub(r'[",\'.?!-]', '', event_name).strip() 
        
        if not event_name:
             results["event"] = "Sự kiện mới"
        else:
             results["event"] = event_name.strip().capitalize()
             
        return results

    # -------------------------------------------------------------
    # COMPONENT 4: PHÂN TÍCH THỜI GIAN 
    # -------------------------------------------------------------
    def _component_4_time_parsing(self, time_str: str, original_text: str) -> Dict[str, str]:
        current_time = datetime.now()
        dt_absolute = current_time.replace(second=0, microsecond=0)
        
        normalized_text = original_text.lower() 
        time_explicitly_found = False
        date_explicitly_found = False

        # --- 4a. Xử lý Ngày Tương đối ---
        relative_keywords = ['ngày mai', 'ngay mai', 'sáng mai', 'chiều mai', 'hôm sau', 'hom sau', 'hôm nay', 'hom nay']
        for kw in relative_keywords:
            if kw in normalized_text:
                if 'mai' in kw and 'ngày mai' in kw:
                    # general day later handled same
                    pass
                if 'ngày mai' in kw or 'mai' in kw and 'ngày' in normalized_text:
                    dt_absolute = current_time + timedelta(days=1)
                    date_explicitly_found = True
                    break
                if 'hôm nay' in kw or 'hom nay' in kw:
                    dt_absolute = current_time
                    date_explicitly_found = True
                    break

        # cụm 'cuối tuần' xử lý riêng
        if not date_explicitly_found and any(keyword in normalized_text for keyword in ['cuối tuần', 'cuoi tuan']):
            # tìm ngày chủ nhật gần nhất
            days_until_sunday = (6 - current_time.weekday() + 7) % 7
            days_until_sunday = days_until_sunday or 7
            dt_absolute = current_time + timedelta(days=days_until_sunday)
            date_explicitly_found = True

        # --- Xử lý các ngày trong tuần (FIX CHUẨN, tránh override nếu chỉ có "ngày mai"...) ---
        for day_name in self.sorted_day_keys:
            # escape key for regex
            key_escaped = re.escape(day_name)
            # chỉ match từ nguyên vẹn
            day_match_pattern = re.compile(r'\b((thứ|t)\s*)?' + key_escaped + r'\b(\s*(tuần này|tuan nay|tuần sau|tuan sau))?', flags=re.IGNORECASE)

            match = day_match_pattern.search(normalized_text)
            if not match:
                continue

            # Nếu đã tìm thấy "ngày mai" hoặc tương tự mà trong câu KHÔNG có tiền tố 'thứ'/'t'/'tuần',
            # thì không override (tránh "sáng" hoặc "mai" bị hiểu nhầm thành một từ trong day_map).
            if date_explicitly_found:
                if not re.search(r'\b(thứ|t|tuần|tuan)\b', match.group(0), flags=re.IGNORECASE):
                    continue

            group = match.group(0)
            is_next_week = bool(re.search(r'\b(tuần sau|tuan sau)\b', group, flags=re.IGNORECASE))
            is_this_week = bool(re.search(r'\b(tuần này|tuan nay)\b', group, flags=re.IGNORECASE))

            current_day_index = current_time.weekday()
            day_index = self.day_map.get(day_name)
            if day_index is None:
                # Try fallback without accents/norm
                day_index = self.day_map.get(remove_accents(day_name), None)
            if day_index is None:
                continue

            # (1) Base: số ngày đến thứ được nhắc (0..6)
            base = (day_index - current_day_index) % 7

            # (2) Xử lý rõ ràng tuần này/tuần sau
            if is_this_week:
                # nếu là tuần này và base==0 -> hôm nay
                # giữ nguyên base
                pass
            else:
                # nếu không rõ là tuần này mà base == 0 -> hiểu là tuần sau
                if base == 0:
                    base = 7

            # (3) Nếu có "tuần sau" thì luôn +7
            if is_next_week:
                base += 7

            dt_absolute = current_time + timedelta(days=base)
            date_explicitly_found = True
            break


        # --- 4b. Xử lý Thời gian Tuyệt đối ---
        time_match = self.time_pattern.search(time_str) 
        
        if time_match:
            time_explicitly_found = True
            time_part = time_match.group(0).lower() 
            
            is_pm = 'pm' in time_part
            is_am = 'am' in time_part
            
            # Chuẩn hóa h/g/giờ/gio thành ':' 
            time_str_clean = time_part.replace('h', ':').replace('g', ':').replace('giờ', ':').replace('gio', ':')
            # Loại bỏ các ký tự không phải số hoặc ':'
            time_str_clean = re.sub(r'[^\d:]', '', time_str_clean).strip() 

            try:
                if ':' in time_str_clean:
                    # Đảm bảo chỉ lấy 2 phần tử đầu tiên
                    parts = [int(p) for p in time_str_clean.split(':') if p][:2]
                    hour = parts[0]
                    minute = parts[1] if len(parts) > 1 else 0
                else:
                    hour = int(time_str_clean)
                    minute = 0
                
                # Chuyển đổi AM/PM
                if is_pm and hour < 12: hour += 12
                elif is_am and hour == 12: hour = 0

                dt_absolute = dt_absolute.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            except ValueError:
                time_explicitly_found = False 
        
        # --- 4c. Logic Ngày/Giờ Cuối Cùng ---
        
        if time_explicitly_found:
            # Nếu tìm thấy giờ, ngày mặc định là hôm nay, và giờ đã qua, thì chuyển sang ngày mai
            is_today = (dt_absolute.date() == current_time.date())
            if not date_explicitly_found and is_today and dt_absolute <= datetime.now(): 
                 dt_absolute = dt_absolute + timedelta(days=1)
                 
        elif not time_explicitly_found and not date_explicitly_found:
             # Mặc định: 9h sáng ngày mai
             dt_absolute = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
             dt_absolute = dt_absolute + timedelta(days=1)
             
        elif date_explicitly_found and not time_explicitly_found:
             # Ngày tương đối được tìm thấy, nhưng giờ không có -> mặc định 9h sáng ngày đó
             dt_absolute = dt_absolute.replace(hour=9, minute=0, second=0, microsecond=0)

        return {
            "start-time": dt_absolute.isoformat(), 
            "end_time": None 
        }

    # -------------------------------------------------------------
    # HÀM CHÍNH
    # -------------------------------------------------------------
    def process_text(self, text: str) -> Dict[str, Any]:
        """Hàm chính thực hiện quy trình NLP hoàn chỉnh."""
        
        # 0. Chuẩn hóa
        normalized_text = self._component_0_normalize_text(text)
        
        # 1. Phân đoạn
        self._component_1_preprocessing(normalized_text) 
        
        # 2. Trích xuất Thực thể
        ner_results = self._component_2_ner_extraction(normalized_text)
        
        # 3. Trích xuất Luật & Tiêu đề
        rule_results = self._component_3_rule_extraction(normalized_text, ner_results["location"]) 
        
        # 4. Phân tích Thời gian
        time_str_for_parse = ner_results.get("time_str") or normalized_text 
        time_results = self._component_4_time_parsing(time_str_for_parse, normalized_text)

        # 5. Hợp nhất
        output = {
            "event": rule_results["event"],
            "start-time": time_results["start-time"],
            "end_time": time_results["end_time"],
            "location": ner_results["location"] if ner_results["location"] else None,
            "reminder_minutes": rule_results["reminder_minutes"] if rule_results["reminder_minutes"] is not None else 15 
        }
        
        return output
