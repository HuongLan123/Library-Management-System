import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font
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

class Book:
    def __init__(self, isbn, title, genre, author, year, quantity):
        self.isbn = isbn
        self.title = title
        self.genre = genre
        self.author = author
        self.year = year
        self.quantity = quantity
        self.available_quantity = quantity

    def __str__(self):
        return f"{self.isbn} | {self.title} | {self.genre}| {self.author} | {self.year} | {self.quantity} | {self.available_quantity}"

    def __eq__(self, other):
        return isinstance(other, Book) and self.isbn == other.isbn

    def __hash__(self):
        return hash(self.isbn)

# =============================
# Giao diện quản lý sách
# =============================

def create_book_tab(notebook, conn):
    tab = ttk.Frame(notebook)
    notebook.add(tab, text="📚 Quản lý Sách")

    book_table = HashTable()

    cursor = conn.cursor()
    for row in cursor.execute("SELECT * FROM books"):
        book = Book(row[0], row[1], row[2], row[3], row[4], row[5])
        book.available_quantity = row[6]
        book_table.insert(book.isbn, book)

    labels = ["ISBN", "Tiêu đề", "Thể loại","Tác giả", "Năm", "Số lượng"]
    entries = {}
    for i, label in enumerate(labels):
        tk.Label(tab, text=label).grid(row=i, column=0, padx=5, pady=5, sticky="e")
        entry = tk.Entry(tab)
        entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew") # Changed sticky to "ew" for entries
        entries[label] = entry
        if i == 2:
            genres = ["Khoa học", "Văn học", "Thiếu nhi", "Giáo trình", "Tiểu thuyết", "Lịch sử", "Tâm lý", "Khác"]
            tk.Label(tab, text="Thể loại").grid(row=2, column=0, padx=5, pady=5, sticky="e")
            genre_combobox = ttk.Combobox(tab, values=genres, state="readonly")
            genre_combobox.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
            entries["Thể loại"] = genre_combobox


    tree = ttk.Treeview(tab, columns=("ISBN", "Tiêu đề","Thể loại", "Tác giả", "Năm", "SL", "Còn"), show="headings")
    for col in tree["columns"]:
        tree.heading(col, text=col, anchor="center")
        # Set a minimum width for columns to prevent them from becoming too narrow
        tree.column(col, width=tk.font.Font().measure(col) + 20, minwidth=50, stretch=True) # Added minwidth and stretch
    
    # Configure the column where the treeview is placed to expand horizontally
    tab.grid_columnconfigure(2, weight=1) # The treeview is in column 2
    
    tree.grid(row=0, column=2, rowspan=15, padx=15, pady=5, sticky="nsew") # Adjusted rowspan and row to 0 to align with top
    
    # Add scrollbar to the Treeview
    scrollbar_y = ttk.Scrollbar(tab, orient="vertical", command=tree.yview)
    scrollbar_y.grid(row=0, column=3, rowspan=15, sticky="ns")
    tree.configure(yscrollcommand=scrollbar_y.set)

    scrollbar_x = ttk.Scrollbar(tab, orient="horizontal", command=tree.xview)
    scrollbar_x.grid(row=15, column=2, sticky="ew") # Placed scrollbar_x in a new row below the treeview
    tree.configure(xscrollcommand=scrollbar_x.set)

    def reload_from_database():
        # Xóa toàn bộ dữ liệu trong bảng băm
        for i in range(book_table.capacity):
            book_table.table[i] = LinkedListForHash()
        book_table.size = 0

        # Truy vấn lại dữ liệu từ SQLite và chèn vào bảng băm
        for row in cursor.execute("SELECT * FROM books"):
            book = Book(*row[:6])
            book.available_quantity = row[6]
            book_table.insert(book.isbn, book)

        # Cập nhật lại Treeview
        refresh_tree()

    def refresh_tree():
        tree.delete(*tree.get_children())
        for book in book_table.get_all_values():
            tree.insert("", "end", values=(book.isbn, book.title, book.genre, book.author, book.year, book.quantity, book.available_quantity))

    def add_book():
        isbn = entries["ISBN"].get().strip()
        title = entries["Tiêu đề"].get().strip()
        genre = entries["Thể loại"].get().strip() or "Khác"
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

        book = Book(isbn, title,genre, author, year, quantity)
        book_table.insert(isbn, book)
        cursor.execute("INSERT INTO books VALUES (?, ?, ?,?, ?, ?, ?)", (isbn, title, genre, author, year, quantity, quantity))
        conn.commit()
        messagebox.showinfo("Thành công", "Đã thêm sách")
        refresh_tree()

    def delete_book():
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Lỗi", "Vui lòng chọn sách để xóa.")
            return
        isbn = tree.item(selected[0])["values"][0]
        if book_table.search(isbn):
            book_table.delete(isbn)
        cursor.execute("DELETE FROM books WHERE isbn = ?", (isbn,))
        conn.commit()
        refresh_tree()
        messagebox.showinfo("Thành công", "Đã xóa sách")

    def update_book():
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Lỗi", "Chọn sách để cập nhật")
            return
        isbn = entries["ISBN"].get().strip()
        genre = entries["Thể loại"].get().strip() or "Khác"
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
        book.genre = entries.get("Thể loại", "Không xác định")  # Optional field, default to "Không xác định"
        book.author = author
        book.year = year
        book.quantity = quantity
        book.available_quantity += diff
        book_table.insert(isbn, book) # Re-insert to update in hash table if key is the same

        cursor.execute("UPDATE books SET title=?, genre=?, author=?, year=?, quantity=?, available_quantity=? WHERE isbn=?",
                       (title, genre, author, year, quantity, book.available_quantity, isbn))
        conn.commit()
        refresh_tree()
        messagebox.showinfo("Thành công", "Đã cập nhật sách")
    
    def load_selected_book(event):
        selected = tree.selection()
        if selected:
            values = tree.item(selected[0])["values"]
            for i, key in enumerate(labels):
                entries[key].delete(0, tk.END)
                entries[key].insert(0, values[i])

    def search_books(table):
        keyword = search_entry.get().strip().lower()
        mode = search_type.get()
        result = []
        for book in table.get_all_values():
            if mode == "ISBN" and keyword in book.isbn.lower():
                result.append(book)
            elif mode == "Tiêu đề" and keyword in book.title.lower():
                result.append(book)
            elif mode == "Tác giả" and keyword in book.author.lower():
                result.append(book)

        tree.delete(*tree.get_children())
        for book in result:
            tree.insert("", "end", values=(book.isbn, book.title, book.genre, book.author, book.year, book.quantity, book.available_quantity))

    def sort_books(table):
        books = table.get_all_values()
        mode = sort_type.get()
        reverse = False
        if mode == "Tiêu đề (A-Z)":
            key_func = lambda book: book.title.lower()
        elif mode == "Tiêu đề (Z-A)":
            key_func = lambda book: book.title.lower()
            reverse = True
        elif mode == "ISBN (tăng dần)":
            key_func = lambda book: book.isbn
        elif mode == "ISBN (giảm dần)":
            key_func = lambda book: book.isbn
            reverse = True
        else:
            key_func = lambda book: book.title.lower()   # fallback

        def merge_sort(arr):
            if len(arr) <= 1:
                return arr
            mid = len(arr) // 2
            left = merge_sort(arr[:mid])
            right = merge_sort(arr[mid:])
            return merge(left, right)

        def merge(left, right):
            result = []
            i = j = 0
            while i < len(left) and j < len(right):
                if (key_func(left[i]) <= key_func(right[j])) ^ reverse:
                    result.append(left[i])
                else:
                    result.append(right[j])
                i += 1
                j += 1
            result.extend(left[i:])
            result.extend(right[j:])
            return result

        sorted_books = merge_sort(books)
        tree.delete(*tree.get_children())
        for book in sorted_books:
            tree.insert("", "end", values=(book.isbn, book.title, book.genre, book.author, book.year, book.quantity, book.available_quantity))


    def export_to_csv():
        with open("books_export.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ISBN", "Tiêu đề", "Tác giả", "Năm", "Số lượng", "Còn lại"])
            for book in book_table.get_all_values():
                writer.writerow([book.isbn, book.title, book.genre, book.author, book.year, book.quantity, book.available_quantity])
        messagebox.showinfo("Xuất CSV", "Đã lưu file books_export.csv")

    # Layout buttons
    tk.Button(tab, text="Thêm",bg="white", command=add_book).grid(row=6, column=0, pady=10, sticky="ew", columnspan=2)
    tk.Button(tab, text="Xóa", bg="white",command=delete_book).grid(row=7, column=0, pady=5, sticky="ew", columnspan=2)
    tk.Button(tab, text="Cập nhật", bg="white",command=update_book).grid(row=8, column=0, pady=5, sticky="ew", columnspan=2)
    tk.Button(tab, text="Xuất CSV", bg="white",command=export_to_csv).grid(row=9, column=0, pady=5, sticky="ew", columnspan=2)
    tk.Button(tab, text="Làm mới",bg="white", command=reload_from_database).grid(row=10, column=0, pady=5, sticky="ew", columnspan=2)

    # Search section
    tk.Label(tab, text="Tìm theo:").grid(row=11, column=0, sticky="e", padx=5, pady=5)
    search_type = ttk.Combobox(tab, values=["ISBN", "Tiêu đề", "Tác giả"])
    search_type.set("Tiêu đề")
    search_type.grid(row=11, column=1, pady=5, sticky="ew")
    
    tk.Label(tab, text="Từ khóa:").grid(row=12, column=0, sticky="e", padx=5, pady=5)
    search_entry = tk.Entry(tab)
    search_entry.grid(row=12, column=1, pady=5, sticky="ew")
    tk.Button(tab, text="Tìm kiếm", bg="white", command=lambda: search_books(book_table)).grid(row=13, column=0, pady=5, sticky="ew", columnspan=2)

    # Sort section
    tk.Label(tab, text="Sắp xếp theo:").grid(row=14, column=0, sticky="e", padx=5, pady=5)
    sort_type = ttk.Combobox(tab, values=["Tiêu đề (A-Z)", "Tiêu đề (Z-A)", "ISBN (tăng dần)", "ISBN (giảm dần)"])
    sort_type.set("Tiêu đề (A-Z)")
    sort_type.grid(row=14, column=1, pady=5, sticky="ew")
    tk.Button(tab, text="Sắp xếp", bg="white", command=lambda: sort_books(book_table)).grid(row=15, column=0, pady=5, sticky="ew", columnspan=2)


    tree.bind("<ButtonRelease-1>", load_selected_book)
    refresh_tree()
