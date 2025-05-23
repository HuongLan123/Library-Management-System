import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import csv

class Reader:
    def __init__(self, reader_id, name, birth_date, address):
        self.reader_id = reader_id
        self.name = name
        self.birth_date = birth_date
        self.address = address

    def __str__(self):
        return f"{self.reader_id} | {self.name} | {self.birth_date} | {self.address}"

class ReaderManager:
    def __init__(self):
        self.readers = HashTable()

    def add_reader(self, reader_id, name, birth_date, address):
        if self.readers.search(reader_id):
            return False
        self.readers.insert(reader_id, Reader(reader_id, name, birth_date, address))
        return True

    def delete_reader(self, reader_id):
        if not self.readers.search(reader_id):
            return False
        self.readers.delete(reader_id)
        return True

    def update_reader(self, reader_id, name, birth_date, address):
        r = self.readers.search(reader_id)
        if not r:
            return False
        r.name = name
        r.birth_date = birth_date
        r.address = address
        self.readers.insert(reader_id, r)
        return True

    def get_all(self):
        return self.readers.get_all_values()

# Dùng lại HashTable
from ui_books import HashTable

def create_reader_tab(notebook, conn):
    tab = ttk.Frame(notebook)
    notebook.add(tab, text="Quản lý Bạn đọc")

    manager = ReaderManager()

    cursor = conn.cursor()
    for row in cursor.execute("SELECT * FROM readers"):
        manager.add_reader(*row)

    labels = ["Mã bạn đọc", "Họ tên", "Ngày sinh", "Địa chỉ"]
    entries = {}
    for i, label in enumerate(labels):
        tk.Label(tab, text=label).grid(row=i, column=0, padx=5, pady=5, sticky="e")
        entry = tk.Entry(tab)
        entry.grid(row=i, column=1, padx=5, pady=5, sticky="w")
        entries[label] = entry

    tree = ttk.Treeview(tab, columns=labels, show="headings")
    for col in labels:
        tree.heading(col, text=col)
    tree.grid(row=0, column=2, rowspan=10, padx=10, pady=5)

    def refresh_tree():
        for row in tree.get_children():
            tree.delete(row)
        for r in manager.get_all():
            tree.insert("", "end", values=(r.reader_id, r.name, r.birth_date, r.address))

    def add():
        reader_id = entries["Mã bạn đọc"].get().strip()
        name = entries["Họ tên"].get().strip()
        birth_date = entries["Ngày sinh"].get().strip()
        address = entries["Địa chỉ"].get().strip()
        if not manager.add_reader(reader_id, name, birth_date, address):
            messagebox.showerror("Lỗi", "Mã bạn đọc đã tồn tại")
            return
        cursor.execute("INSERT INTO readers VALUES (?, ?, ?, ?)", (reader_id, name, birth_date, address))
        conn.commit()
        refresh_tree()

    def delete():
        selected = tree.selection()
        if not selected:
            return
        reader_id = tree.item(selected[0])["values"][0]
        manager.delete_reader(reader_id)
        cursor.execute("DELETE FROM readers WHERE reader_id = ?", (reader_id,))
        conn.commit()
        refresh_tree()

    def update():
        reader_id = entries["Mã bạn đọc"].get().strip()
        name = entries["Họ tên"].get().strip()
        birth_date = entries["Ngày sinh"].get().strip()
        address = entries["Địa chỉ"].get().strip()
        if not manager.update_reader(reader_id, name, birth_date, address):
            messagebox.showerror("Lỗi", "Không tìm thấy bạn đọc")
            return
        cursor.execute("UPDATE readers SET name=?, birth_date=?, address=? WHERE reader_id=?",
                       (name, birth_date, address, reader_id))
        conn.commit()
        refresh_tree()

    def load_selected(event):
        selected = tree.selection()
        if selected:
            values = tree.item(selected[0])["values"]
            for i, key in enumerate(labels):
                entries[key].delete(0, tk.END)
                entries[key].insert(0, values[i])

    def export_csv():
        with open("readers_export.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(labels)
            for r in manager.get_all():
                writer.writerow([r.reader_id, r.name, r.birth_date, r.address])
        messagebox.showinfo("Xuất CSV", "Đã lưu file readers_export.csv")

    tk.Button(tab, text="Thêm", command=add).grid(row=6, column=0, pady=10)
    tk.Button(tab, text="Xóa", command=delete).grid(row=6, column=1)
    tk.Button(tab, text="Cập nhật", command=update).grid(row=6, column=2)
    tk.Button(tab, text="Xuất CSV", command=export_csv).grid(row=7, column=0, columnspan=2)

    tree.bind("<ButtonRelease-1>", load_selected)
    refresh_tree()
