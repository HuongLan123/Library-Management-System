import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
from collections import Counter

def create_statistics_tab(notebook, conn):
    tab = ttk.Frame(notebook)
    notebook.add(tab, text="Báo cáo & Thống kê")

    output = tk.Text(tab, width=120, height=30)
    output.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

    def clear_output():
        output.delete("1.0", tk.END)

    def top_n_books():
        clear_output()
        n = 10
        cursor = conn.cursor()
        cursor.execute("SELECT isbn FROM loans")
        isbns = [row[0] for row in cursor.fetchall()]
        if not isbns:
            output.insert(tk.END, "Chưa có dữ liệu mượn sách.\n")
            return
        counter = Counter(isbns)
        top_books = counter.most_common(n)
        for i, (isbn, count) in enumerate(top_books, 1):
            cursor.execute("SELECT title FROM books WHERE isbn = ?", (isbn,))
            title = cursor.fetchone()
            title = title[0] if title else "[Không tìm thấy]"
            output.insert(tk.END, f"Hạng {i}: {title} (ISBN: {isbn}) - Số lượt mượn: {count}\n")

    def top_n_readers():
        clear_output()
        n = 10
        cursor = conn.cursor()
        cursor.execute("SELECT reader_id FROM loans")
        reader_ids = [row[0] for row in cursor.fetchall()]
        if not reader_ids:
            output.insert(tk.END, "Chưa có dữ liệu mượn sách.\n")
            return
        counter = Counter(reader_ids)
        top_readers = counter.most_common(n)
        for i, (reader_id, count) in enumerate(top_readers, 1):
            cursor.execute("SELECT name FROM readers WHERE reader_id = ?", (reader_id,))
            name = cursor.fetchone()
            name = name[0] if name else "[Không tìm thấy]"
            output.insert(tk.END, f"Hạng {i}: {name} (Mã: {reader_id}) - Số lượt mượn: {count}\n")

    def total_books():
        clear_output()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM books")
        num_titles = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(quantity) FROM books")
        total_copies = cursor.fetchone()[0] or 0
        output.insert(tk.END, f"Tổng số đầu sách trong thư viện: {num_titles}\n")
        output.insert(tk.END, f"Tổng số cuốn sách trong thư viện: {total_copies}\n")

    def total_readers():
        clear_output()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM readers")
        count = cursor.fetchone()[0]
        output.insert(tk.END, f"Tổng số bạn đọc đã đăng ký: {count}\n")

    def books_currently_loaned():
        clear_output()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM loans WHERE status IN ('Đang mượn', 'Quá hạn')")
        count = cursor.fetchone()[0]
        output.insert(tk.END, f"Tổng số sách hiện đang được mượn: {count}\n")

    def books_overdue():
        clear_output()
        today = datetime.datetime.now().date()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM loans WHERE status = 'Đang mượn' AND due_date < ?", (today,))
        count = cursor.fetchone()[0]
        output.insert(tk.END, f"Tổng số sách đã quá hạn trả: {count}\n")

    tk.Button(tab, text="Top sách được mượn nhiều", command=top_n_books).grid(row=1, column=0, sticky="ew", padx=5, pady=2)
    tk.Button(tab, text="Top bạn đọc mượn nhiều", command=top_n_readers).grid(row=2, column=0, sticky="ew", padx=5, pady=2)
    tk.Button(tab, text="Tổng số sách", command=total_books).grid(row=3, column=0, sticky="ew", padx=5, pady=2)
    tk.Button(tab, text="Tổng số bạn đọc", command=total_readers).grid(row=4, column=0, sticky="ew", padx=5, pady=2)
    tk.Button(tab, text="Sách đang được mượn", command=books_currently_loaned).grid(row=5, column=0, sticky="ew", padx=5, pady=2)
    tk.Button(tab, text="Sách quá hạn trả", command=books_overdue).grid(row=6, column=0, sticky="ew", padx=5, pady=2)
    tk.Button(tab, text="Xóa kết quả", command=clear_output).grid(row=7, column=0, sticky="ew", padx=5, pady=2)
