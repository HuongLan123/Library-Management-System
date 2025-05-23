import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import csv

# =============================
# HashTable và Book Class để quản lý nội bộ
# =============================

class HashNode:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next = None

class LinkedListForHash:
    def __init__(self):
        self.head = None

    def insert(self, key, value):
        node = self.head
        while node:
            if node.key == key:
                node.value = value
                return
            node = node.next
        new_node = HashNode(key, value)
        new_node.next = self.head
        self.head = new_node

    def search(self, key):
        node = self.head
        while node:
            if node.key == key:
                return node.value
            node = node.next
        return None

    def delete(self, key):
        prev = None
        node = self.head
        while node:
            if node.key == key:
                if prev:
                    prev.next = node.next
                else:
                    self.head = node.next
                return
            prev = node
            node = node.next

    def get_all_key_value_pairs(self):
        result = []
        node = self.head
        while node:
            result.append((node.key, node.value))
            node = node.next
        return result

class HashTable:
    def __init__(self, capacity=100):
        self.capacity = capacity
        self.size = 0
        self.table = [LinkedListForHash() for _ in range(capacity)]

    def _hash_function(self, key):
        hash_value = 0
        for char in key:
            hash_value = (hash_value * 31 + ord(char)) % self.capacity
        return hash_value

    def insert(self, key, value):
        index = self._hash_function(key)
        if self.table[index].search(key) is None:
            self.size += 1
        self.table[index].insert(key, value)

    def search(self, key):
        index = self._hash_function(key)
        return self.table[index].search(key)

    def delete(self, key):
        index = self._hash_function(key)
        if self.table[index].search(key) is not None:
            self.size -= 1
        self.table[index].delete(key)

    def get_all_values(self):
        result = []
        for bucket in self.table:
            result.extend([value for _, value in bucket.get_all_key_value_pairs()])
        return result

# =============================
# Book class để lưu trong bảng băm
# =============================

class Book:
    def __init__(self, isbn, title, author, year, quantity):
        self.isbn = isbn
        self.title = title
        self.author = author
        self.year = year
        self.quantity = quantity
        self.available_quantity = quantity

    def __str__(self):
        return f"{self.isbn} | {self.title} | {self.author} | {self.year} | {self.quantity} | {self.available_quantity}"

    def __eq__(self, other):
        return isinstance(other, Book) and self.isbn == other.isbn

    def __hash__(self):
        return hash(self.isbn)

# =============================
# Giao diện quản lý sách
# =============================

def create_book_tab(notebook, conn):
    tab = ttk.Frame(notebook)
    notebook.add(tab, text="Quản lý Sách")

    book_table = HashTable()

    # Load sách từ CSDL vào bảng băm
    cursor = conn.cursor()
    for row in cursor.execute("SELECT * FROM books"):
        book = Book(*row[:5])
        book.available_quantity = row[5]
        book_table.insert(book.isbn, book)

    # Nhãn và ô nhập
    labels = ["ISBN", "Tiêu đề", "Tác giả", "Năm", "Số lượng"]
    entries = {}
    for i, label in enumerate(labels):
        tk.Label(tab, text=label).grid(row=i, column=0, padx=5, pady=5, sticky="e")
        entry = tk.Entry(tab)
        entry.grid(row=i, column=1, padx=5, pady=5, sticky="w")
        entries[label] = entry

    # Hiển thị danh sách sách
    tree = ttk.Treeview(tab, columns=("ISBN", "Tiêu đề", "Tác giả", "Năm", "SL", "Còn"), show="headings")
    for col in tree["columns"]:
        tree.heading(col, text=col)
    tree.grid(row=0, column=2, rowspan=10, padx=10, pady=5)

    def refresh_tree():
        for row in tree.get_children():
            tree.delete(row)
        for book in book_table.get_all_values():
            tree.insert("", "end", values=(book.isbn, book.title, book.author, book.year, book.quantity, book.available_quantity))

    def add_book():
        isbn = entries["ISBN"].get().strip()
        title = entries["Tiêu đề"].get().strip()
        author = entries["Tác giả"].get().strip()
        try:
            year = int(entries["Năm"].get().strip())
            quantity = int(entries["Số lượng"].get().strip())
        except ValueError:
            messagebox.showerror("Lỗi", "Năm và Số lượng phải là số nguyên")
            return

        if book_table.search(isbn):
            messagebox.showerror("Lỗi", "Sách đã tồn tại trong hệ thống")
            return

        book = Book(isbn, title, author, year, quantity)
        book_table.insert(isbn, book)

        cursor = conn.cursor()
        cursor.execute("INSERT INTO books VALUES (?, ?, ?, ?, ?, ?)",
                       (isbn, title, author, year, quantity, quantity))
        conn.commit()
        messagebox.showinfo("Thành công", "Đã thêm sách")
        refresh_tree()

    def delete_book():
        selected = tree.selection()
        if not selected:
            return
        isbn = tree.item(selected[0])["values"][0]
        if book_table.search(isbn):
            book_table.delete(isbn)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM books WHERE isbn = ?", (isbn,))
        conn.commit()
        refresh_tree()

    def update_book():
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Lỗi", "Chọn sách để cập nhật")
            return
        isbn = entries["ISBN"].get().strip()
        title = entries["Tiêu đề"].get().strip()
        author = entries["Tác giả"].get().strip()
        try:
            year = int(entries["Năm"].get().strip())
            quantity = int(entries["Số lượng"].get().strip())
        except ValueError:
            messagebox.showerror("Lỗi", "Năm và Số lượng phải là số")
            return

        book = book_table.search(isbn)
        if not book:
            messagebox.showerror("Lỗi", "Không tìm thấy sách để cập nhật")
            return

        diff = quantity - book.quantity
        book.title = title
        book.author = author
        book.year = year
        book.quantity = quantity
        book.available_quantity += diff
        book_table.insert(isbn, book)

        cursor = conn.cursor()
        cursor.execute("UPDATE books SET title=?, author=?, year=?, quantity=?, available_quantity=? WHERE isbn=?",
                       (title, author, year, quantity, book.available_quantity, isbn))
        conn.commit()
        refresh_tree()

    def load_selected_book(event):
        selected = tree.selection()
        if selected:
            values = tree.item(selected[0])["values"]
            for i, key in enumerate(labels):
                entries[key].delete(0, tk.END)
                entries[key].insert(0, values[i])

    def export_to_csv():
        with open("books_export.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ISBN", "Tiêu đề", "Tác giả", "Năm", "Số lượng", "Còn lại"])
            for book in book_table.get_all_values():
                writer.writerow([book.isbn, book.title, book.author, book.year, book.quantity, book.available_quantity])
        messagebox.showinfo("Xuất CSV", "Đã lưu file books_export.csv")

    # Nút chức năng
    tk.Button(tab, text="Thêm", command=add_book).grid(row=6, column=0, pady=10)
    tk.Button(tab, text="Xóa", command=delete_book).grid(row=6, column=1)
    tk.Button(tab, text="Cập nhật", command=update_book).grid(row=6, column=2)
    tk.Button(tab, text="Xuất CSV", command=export_to_csv).grid(row=7, column=0, columnspan=2)

    tree.bind("<ButtonRelease-1>", load_selected_book)

    refresh_tree()
