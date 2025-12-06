# Personal Schedule Assistant

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![SQLite](https://img.shields.io/badge/Database-SQLite3-orange)
![Underthesea](https://img.shields.io/badge/NLP-Underthesea-green)

Ứng dụng quản lý lịch trình cá nhân bằng Python, tích hợp **NLP xử lý tiếng Việt** để tự động trích xuất thông tin từ câu nhập liệu và hệ thống nhắc nhở thông minh.

---

## 1. Giới thiệu

**Personal Schedule Assistant** cho phép người dùng:

- Nhập các sự kiện lịch trình bằng câu tiếng Việt tự do.  
- Trích xuất thông tin về **thời gian, địa điểm, nhắc trước** thông qua **Module NLP**.  
- Lưu trữ sự kiện vào cơ sở dữ liệu **SQLite**.  
- Nhận thông báo **pop-up nhắc nhở** theo thời gian đã định.

Ứng dụng phù hợp để quản lý công việc, học tập, hoặc các sự kiện cá nhân mà không cần nhập dữ liệu theo định dạng cố định.

---

## 2. Yêu cầu hệ thống

- **Python**: 3.8 hoặc cao hơn  
- **Thư viện cần thiết**: cài đặt qua `pip`
  ```bash
  pip install underthesea python-dateutil plyer
