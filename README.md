# 📚 HỆ THỐNG QUẢN LÝ THƯ VIỆN BẰNG PYTHON & TKINTER

---

## 1. 🧾 TỔNG QUÁT HỆ THỐNG

### 1.1 🎯 Chức năng của hệ thống

Hệ thống hỗ trợ các chức năng quản lý thư viện cơ bản:

* Quản lý sách: thêm, xóa, sửa, tìm kiếm, sắp xếp, xuất CSV
* Quản lý bạn đọc: thêm, xóa, sửa, tìm kiếm, sắp xếp, xuất CSV
* Quản lý phiếu mượn/trả sách: tạo phiếu mượn, trả sách, xem lịch sử, thống kê lượt mượn
* Báo cáo thống kê: top sách/bạn đọc mượn nhiều nhất, tổng số sách, sách đang mượn/quá hạn...

> Giao diện hoàn toàn bằng tiếng Việt, dễ sử dụng, trực quan. Hệ thống sử dụng SQLite nên không cần cài đặt máy chủ cơ sở dữ liệu.

---

### 1.2 📁 Cấu trúc thư mục của hệ thống

<details>
<summary><strong>Click để mở cây thư mục</strong></summary>

```plaintext
project/
├── Home.py.py             # Chạy chính để khởi động giao diện
├── ui_books.py            # Giao diện và xử lý quản lý sách (dùng HashTable)
├── ui_readers.py          # Giao diện và xử lý bạn đọc (dùng HashTable)
├── ui_loans.py            # Giao diện và xử lý phiếu mượn (dùng AVL Tree)
├── ui_statistics.py       # Thống kê và báo cáo (dùng HashTable + thuật toán tự cài)
├── test1.py               # Kiểm tra, đánh giá hiệu năng hệ thống
├── library4.db            # CSDL SQLite (tự tạo sau lần chạy đầu tiên)
└── README.md              # File hướng dẫn (chính là file này)
```

</details>

---

### 1.3 🧠 Các cấu trúc dữ liệu sử dụng

| Tính năng               | Cấu trúc dữ liệu sử dụng          |
| ----------------------- | --------------------------------- |
| Quản lý sách và bạn đọc | Hash Table (chaining)             |
| Quản lý phiếu mượn      | Cây AVL (LoanBST tự cài)          |
| Sắp xếp danh sách       | Merge Sort tự cài                 |
| Thống kê tần suất       | Tự cài đếm số lượng qua HashTable |

---

## 2. 📦 CÁC THƯ VIỆN CẦN CÀI ĐẶT

### 📌 Yêu cầu:

* Python >= 3.8
* Hệ điều hành: Windows / macOS / Linux (Ubuntu/Debian...)

### ✅ Cài đặt thư viện:

```bash
pip install pillow
```

### 🧰 Thư viện chuẩn sẵn trong Python:

| Thư viện       | Mục đích                                    |
| -------------- | ------------------------------------------- |
| `tkinter`      | Giao diện người dùng (UI)                   |
| `tkinter.font` | Tùy chỉnh font, size trong UI               |
| `tkinter.ttk`  | Các widget như Notebook, Combobox, Treeview |
| `sqlite3`      | Kết nối cơ sở dữ liệu SQLite                |
| `csv`          | Ghi dữ liệu ra file CSV                     |
| `datetime`     | Xử lý thời gian, hạn trả                    |
| `sys`, `io`    | Ghi Unicode ra console (Windows)            |

> 💡 Ghi chú: Tất cả thư viện trên (trừ `pillow`) đều có sẵn trong Python chuẩn.

### 🐧 Nếu dùng Linux (Ubuntu/Debian) và thiếu tkinter:

```bash
sudo apt update
sudo apt install python3-tk
```

### 🔍 Kiểm tra tkinter đã cài:

```bash
python -m tkinter
```

---

## 3. ▶️ CÁCH CHẠY CHƯƠNG TRÌNH

Từ thư mục chứa mã nguồn, chạy lệnh sau:

```bash
python Home.py.py
```

Cửa sổ giao diện sẽ hiển thị với các tab:

* 📚 Quản lý Sách
* 👥 Quản lý Bạn đọc
* 📬 Quản lý Mượn/Trả
* 📊 Thống kê

---

## 4. 🧭 HƯỚNG DẪN SỬ DỤNG GIAO DIỆN

### 📚 Tab "Quản lý Sách"

* Thêm sách: Nhập thông tin → Nhấn **Thêm**
* Xóa sách: Chọn sách → Nhấn **Xóa** (không xóa được nếu đang được mượn)
* Cập nhật: Chọn sách trên bảng giao diện → Sửa thông tin → Nhấn **Cập nhật**
* Xuất CSV: Lưu danh sách thành `books_export.csv`
* Tìm kiếm: Nhập từ khóa + chọn tiêu chí → Nhấn **Tìm**
* Sắp xếp: Chọn tiêu chí → Nhấn **Sắp xếp**

### 👥 Tab "Quản lý Bạn đọc"

* Thêm bạn đọc: Nhập thông tin → Nhấn **Thêm**
* Xóa bạn đọc: Chọn bạn đọc → Nhấn **Xóa** (nếu đang mượn sách sẽ bị từ chối)
* Cập nhật: Chọn bạn đọc → Sửa thông tin → Nhấn **Cập nhật**
* Xuất CSV: Lưu danh sách thành `readers_export.csv`
* Tìm kiếm và sắp xếp: giống như phần sách

### 📬 Tab "Quản lý Mượn/Trả"

* Tạo phiếu mượn: Nhập Mã bạn đọc + ISBN → Nhấn **Tạo phiếu mượn**
* Trả sách: Nhập ID phiếu mượn → Nhấn **Trả sách**
* Xem lịch sử phiếu: Nhập mã bạn đọc hoặc ISBN → Nhấn **Lịch sử**
* Xóa phiếu đã trả: Chọn phiếu → Nhấn **Xóa**
* Thống kê lượt mượn theo sách: Nhấn **Thống kê sách mượn**

### 📊 Tab "Thống kê"

1. Nhấn **🔄 Làm mới dữ liệu thống kê từ CSDL**
2. Thực hiện các thống kê:

   * 📈 Top 10 sách được mượn nhiều nhất
   * 👤 Top 10 bạn đọc mượn nhiều nhất
   * 📊 Tổng số đầu sách và số bản còn lại
   * 📚 Số lượng sách đang được mượn
   * 🕒 Số sách đã quá hạn trả

---

## 5. 📊 KIỂM TRA ĐÁNH GIÁ HIỆU NĂNG

Chạy file `test1.py` để đánh giá hiệu năng thao tác với Hash Table và AVL Tree:

```bash
python test1.py
```

Kết quả sẽ hiển thị thời gian và bộ nhớ sử dụng:

```
Insert 1000 books to HashTable        | Time: 0.0032 s | Peak Mem: 8.5 KB
Search 1000 readers in HashTable      | Time: 0.0021 s | Peak Mem: 6.2 KB
...
```

---

## ✅ Ghi chú

* CSDL `library4.db` được tạo tự động sau lần chạy đầu tiên
* Không thể xóa sách/bạn đọc nếu có phiếu mượn chưa trả
* Giao diện hỗ trợ Unicode và tiếng Việt đầy đủ

📌 Mọi đóng góp hoặc đề xuất cải tiến xin vui lòng mở **issue** hoặc gửi **pull request**!
