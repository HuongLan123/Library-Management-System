import tkinter as tk
from tkinter import ttk
import sqlite3

# Kết nối cơ sở dữ liệu SQLite
conn = sqlite3.connect("library1.db")
cursor = conn.cursor()

# Tạo bảng nếu chưa tồn tại
cursor.execute('''CREATE TABLE IF NOT EXISTS books (
    isbn TEXT PRIMARY KEY,
    title TEXT,
    author TEXT,
    year INTEGER,
    quantity INTEGER,
    available_quantity INTEGER
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS readers (
    reader_id TEXT PRIMARY KEY,
    name TEXT,
    birth_date TEXT,
    address TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS loans (
    loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    reader_id TEXT,
    isbn TEXT,
    borrow_date TEXT,
    due_date TEXT,
    return_date TEXT,
    status TEXT
)''')

conn.commit()

# Import các module giao diện
from ui_books import create_book_tab
from ui_readers import create_reader_tab
from ui_loans import create_loan_tab
from ui_statistics import create_statistics_tab

# Giao diện chính
root = tk.Tk()
root.title("Hệ thống Quản lý Thư viện")
root.geometry("1100x750")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

# Tạo các tab giao diện
create_book_tab(notebook, conn)
create_reader_tab(notebook, conn)
create_loan_tab(notebook, conn)
create_statistics_tab(notebook, conn)

# Chạy chương trình
root.mainloop()

# Đóng kết nối khi thoát
conn.close()
