import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta

# ============================
# Cấu trúc dữ liệu cho phiếu mượn sách
# ============================

class LoanRecord:
    def __init__(self, loan_id, reader_id, isbn, borrow_date, due_date, return_date=None, status="Đang mượn"):
        self.loan_id = loan_id
        self.reader_id = reader_id
        self.isbn = isbn
        self.borrow_date = borrow_date
        self.due_date = due_date
        self.return_date = return_date
        self.status = status

class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LoanList:
    def __init__(self):
        self.head = None

    def insert(self, loan_record):
        new_node = Node(loan_record)
        if not self.head:
            self.head = new_node
        else:
            cur = self.head
            while cur.next:
                cur = cur.next
            cur.next = new_node

    def get_all(self):
        result = []
        cur = self.head
        while cur:
            result.append(cur.data)
            cur = cur.next
        return result

    def update_status(self):
        today = datetime.now().date()
        for record in self.get_all():
            if record.return_date:
                record.status = "Đã trả"
            elif record.due_date < today:
                record.status = "Quá hạn"
            else:
                record.status = "Đang mượn"

# ============================
# Giao diện quản lý mượn - trả
# ============================

def create_loan_tab(notebook, conn):
    tab = ttk.Frame(notebook)
    notebook.add(tab, text="Mượn - Trả Sách")

    loan_list = LoanList()

    # Load dữ liệu từ SQLite
    cursor = conn.cursor()
    for row in cursor.execute("SELECT * FROM loans"):
        loan = LoanRecord(row[0], row[1], row[2], datetime.strptime(row[3], "%Y-%m-%d").date(), datetime.strptime(row[4], "%Y-%m-%d").date(), datetime.strptime(row[5], "%Y-%m-%d").date() if row[5] else None, row[6])
        loan_list.insert(loan)
    loan_list.update_status()

    # UI
    labels = ["Mã bạn đọc", "ISBN", "Số ngày mượn"]
    entries = {}
    for i, label in enumerate(labels):
        tk.Label(tab, text=label).grid(row=i, column=0, padx=5, pady=5, sticky="e")
        entry = tk.Entry(tab)
        entry.grid(row=i, column=1, padx=5, pady=5, sticky="w")
        entries[label] = entry

    tree = ttk.Treeview(tab, columns=("ID", "Reader", "ISBN", "Mượn", "Hạn", "Trả", "Trạng thái"), show="headings")
    for col in tree["columns"]:
        tree.heading(col, text=col)
    tree.grid(row=0, column=2, rowspan=10, padx=10, pady=5)

    def refresh_tree():
        loan_list.update_status()
        for row in tree.get_children():
            tree.delete(row)
        for loan in loan_list.get_all():
            tree.insert("", "end", values=(loan.loan_id, loan.reader_id, loan.isbn, loan.borrow_date, loan.due_date, loan.return_date or "", loan.status))

    def create_loan():
        try:
            reader_id = entries["Mã bạn đọc"].get().strip()
            isbn = entries["ISBN"].get().strip()
            days = int(entries["Số ngày mượn"].get().strip()) if entries["Số ngày mượn"].get() else 30
            borrow_date = datetime.now().date()
            due_date = borrow_date + timedelta(days=days)

            cursor.execute("INSERT INTO loans (reader_id, isbn, borrow_date, due_date, return_date, status) VALUES (?, ?, ?, ?, ?, ?)",
                           (reader_id, isbn, borrow_date, due_date, None, "Đang mượn"))
            conn.commit()

            loan_id = cursor.lastrowid
            loan = LoanRecord(loan_id, reader_id, isbn, borrow_date, due_date)
            loan_list.insert(loan)
            messagebox.showinfo("Thành công", f"Đã tạo phiếu mượn #{loan_id}")
            refresh_tree()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tạo phiếu: {e}")

    def return_book():
        selected = tree.selection()
        if not selected:
            return
        loan_id = tree.item(selected[0])["values"][0]
        for loan in loan_list.get_all():
            if loan.loan_id == loan_id and loan.status == "Đang mượn":
                loan.return_date = datetime.now().date()
                loan.status = "Đã trả"
                cursor.execute("UPDATE loans SET return_date=?, status=? WHERE loan_id=?",
                               (loan.return_date, loan.status, loan.loan_id))
                conn.commit()
                messagebox.showinfo("Trả sách", f"Phiếu #{loan.loan_id} đã trả sách")
                refresh_tree()
                return
        messagebox.showwarning("Thông báo", "Không có phiếu hợp lệ để trả")

    tk.Button(tab, text="Tạo phiếu mượn", command=create_loan).grid(row=4, column=0, pady=10)
    tk.Button(tab, text="Trả sách", command=return_book).grid(row=4, column=1)

    refresh_tree()
