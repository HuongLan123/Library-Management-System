import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import csv
from tkinter import font # Import module font

# =============================
# HashTable và Reader Class để quản lý nội bộ
# Sao chép từ ui_books.py
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

class Reader:
    def __init__(self, reader_id, name, birth_date, address):
        self.reader_id = reader_id
        self.name = name
        self.birth_date = birth_date
        self.address = address

    def __str__(self):
        return f"{self.reader_id} | {self.name} | {self.birth_date} | {self.address}"

# =============================
# Giao diện quản lý bạn đọc
# =============================

def create_reader_tab(notebook, conn):
    tab = ttk.Frame(notebook)
    notebook.add(tab, text="👥 Quản lý Bạn đọc")

    reader_table = HashTable() 

    cursor = conn.cursor()
    # Lấy dữ liệu ban đầu và chèn vào HashTable
    for row in cursor.execute("SELECT * FROM readers"):
        reader_table.insert(row[0], Reader(*row))

    labels = ["Mã bạn đọc", "Họ tên", "Ngày sinh", "Địa chỉ"]
    entries = {}
    for i, label in enumerate(labels):
        tk.Label(tab, text=label).grid(row=i, column=0, padx=5,pady=5, sticky="e") # Giảm pady
        entry = tk.Entry(tab)
        entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew") # Giảm pady và thêm sticky="ew"
        entries[label] = entry

    # Cấu hình để cột 2 (nơi Treeview sẽ nằm) giãn nở
    tab.grid_columnconfigure(2, weight=1) 

    # Frame chứa Treeview và Scrollbar
    tree_frame = ttk.Frame(tab)
    # Tăng rowspan để bảng to hơn, rowspan được tăng lên đến 18 hoặc 20 để bao phủ hết các nút và tìm kiếm/sắp xếp
    # column=2 để nó nằm bên phải của các entry/button, sticky="nsew" để nó giãn nở
    tree_frame.grid(row=0, column=2, rowspan=18, padx=25, pady= 5, sticky="nsew") 

    # Thanh cuộn dọc
    scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical")
    scrollbar_y.pack(side="right", fill="y")

    # Thanh cuộn ngang
    scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal")
    scrollbar_x.pack(side="bottom", fill="x")

    # Treeview có gắn scrollbar
    tree = ttk.Treeview(tree_frame, columns=labels, show="headings",
                         yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
    tree.pack(fill="both", expand=True) # expand=True để treeview lấp đầy tree_frame

    # Gắn scrollbar với tree
    scrollbar_y.config(command=tree.yview)
    scrollbar_x.config(command=tree.xview)

    for col in labels:
        tree.heading(col, text=col)
        # Tăng width để cột rộng hơn, sử dụng font.Font().measure để tính toán độ rộng văn bản
        tree.column(col, width=font.Font().measure(col) + 50, minwidth=100, anchor="w") 

    def refresh_tree(data=None):
        tree.delete(*tree.get_children())
        display_data = data if data is not None else reader_table.get_all_values()
        
        for r in display_data:
            tree.insert("", "end", values=(r.reader_id, r.name, r.birth_date, r.address))

    def add_reader():
        reader_id = entries["Mã bạn đọc"].get().strip()
        name = entries["Họ tên"].get().strip()
        birth_date = entries["Ngày sinh"].get().strip()
        address = entries["Địa chỉ"].get().strip()

        if not reader_id or not name or not birth_date or not address:
            messagebox.showerror("Lỗi", "Vui lòng điền đầy đủ thông tin.")
            return

        if reader_table.search(reader_id):
            messagebox.showerror("Lỗi", "Mã bạn đọc đã tồn tại")
            return
        
        new_reader = Reader(reader_id, name, birth_date, address)
        reader_table.insert(reader_id, new_reader)
        cursor.execute("INSERT INTO readers VALUES (?, ?, ?, ?)", (reader_id, name, birth_date, address))
        conn.commit()
        messagebox.showinfo("Thành công", "Đã thêm bạn đọc")
        refresh_tree() 
        # Clear entry fields after adding
        for entry in entries.values():
            entry.delete(0, tk.END)

    def delete_reader():
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Lỗi", "Vui lòng chọn bạn đọc để xóa.")
            return
        reader_id = tree.item(selected[0])["values"][0]
        
        if reader_table.search(reader_id):
            reader_table.delete(reader_id)
            cursor.execute("DELETE FROM readers WHERE reader_id = ?", (reader_id,))
            conn.commit()
            refresh_tree() 
            messagebox.showinfo("Thành công", "Đã xóa bạn đọc")
        else:
            messagebox.showerror("Lỗi", "Không tìm thấy bạn đọc để xóa.")
        # Clear entry fields after deleting
        for entry in entries.values():
            entry.delete(0, tk.END)


    def update_reader():
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Lỗi", "Chọn bạn đọc để cập nhật")
            return

        reader_id = entries["Mã bạn đọc"].get().strip()
        name = entries["Họ tên"].get().strip()
        birth_date = entries["Ngày sinh"].get().strip()
        address = entries["Địa chỉ"].get().strip()

        if not reader_id or not name or not birth_date or not address:
            messagebox.showerror("Lỗi", "Vui lòng điền đầy đủ thông tin.")
            return

        # Ensure the ISBN in the entry matches the selected item's ISBN
        r = reader_table.search(reader_id)
        if not r:
            messagebox.showerror("Lỗi", "Không tìm thấy bạn đọc để cập nhật")
            return
        
        r.name = name
        r.birth_date = birth_date
        r.address = address

        cursor.execute("UPDATE readers SET name=?, birth_date=?, address=? WHERE reader_id=?",
                       (name, birth_date, address, reader_id))
        conn.commit()
        refresh_tree() 
        messagebox.showinfo("Thành công", "Đã cập nhật bạn đọc")

    def load_selected_reader(event):
        selected = tree.selection()
        if selected:
            values = tree.item(selected[0])["values"]
            for i, key in enumerate(labels):
                entries[key].delete(0, tk.END)
                entries[key].insert(0, values[i])

    def search_readers(table):
        keyword = search_entry.get().strip().lower()
        mode = search_type.get()
        result = []
        for reader in table.get_all_values(): 
            if mode == "Mã bạn đọc" and keyword in reader.reader_id.lower():
                result.append(reader)
            elif mode == "Họ tên" and keyword in reader.name.lower():
                result.append(reader)
            elif mode == "Địa chỉ" and keyword in reader.address.lower():
                result.append(reader)

        refresh_tree(result) 

    def sort_readers(table):
        readers = table.get_all_values() 
        mode = sort_type.get()
        reverse = False

        def extract_vietnamese_last_name(full_name):
            parts = full_name.strip().lower().split()
            return parts[-1] if parts else ""

        if mode == "Họ tên (A-Z)":
            key_func = lambda r: extract_vietnamese_last_name(r.name)
        elif mode == "Họ tên (Z-A)":
            key_func = lambda r: extract_vietnamese_last_name(r.name)
            reverse = True
        elif mode == "Mã số (tăng dần)":
            key_func = lambda r: r.reader_id
        elif mode == "Mã số (giảm dần)":
            key_func = lambda r: r.reader_id
            reverse = True
        else:
            key_func = lambda r: r.reader_id 

        def merge_sort_inner(arr):
            if len(arr) <= 1:
                return arr
            mid = len(arr) // 2
            left = merge_sort_inner(arr[:mid])
            right = merge_sort_inner(arr[mid:])
            return merge_inner(left, right)

        def merge_inner(left, right):
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

        sorted_readers = merge_sort_inner(readers) 
        refresh_tree(sorted_readers) 

    def export_csv():
        with open("readers_export.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(labels)
            for r in reader_table.get_all_values(): 
                writer.writerow([r.reader_id, r.name, r.birth_date, r.address])
        messagebox.showinfo("Xuất CSV", "Đã lưu file readers_export.csv")

    # Các nút Thêm, Xóa, Xuất CSV
    # Đặt các nút trên cùng một hàng để chúng gần nhau hơn
    tk.Button(tab, text="Thêm", bg="white", command=add_reader).grid(row=len(labels), column=0, pady= 5, sticky="ew")
    tk.Button(tab, text="Xóa", bg="white", command=delete_reader).grid(row=len(labels), column=1, padx= 15, pady = 5, sticky="ew")
    tk.Button(tab, text="Xuất CSV", bg="white", command=export_csv).grid(row=len(labels) + 1, column=0, sticky="ew", pady = 5, columnspan=2)

    # Nút Cập nhật (di chuyển lên gần các nút khác)
    tk.Button(tab, text="Cập nhật", bg="white", command=update_reader).grid(row=len(labels) + 2, column=0, pady = 5,sticky="ew", columnspan=2)

    # Khung Tìm kiếm
    tk.Label(tab, text="Tìm theo:").grid(row=len(labels) + 3, column=0, sticky="e", padx=5, pady=5) # Giảm pady
    search_type = ttk.Combobox(tab, values=["Mã bạn đọc", "Họ tên", "Địa chỉ"])
    search_type.set("Họ tên")
    search_type.grid(row=len(labels) + 3, column=1, pady=5, sticky="ew") # Giảm pady và thêm sticky="ew"
    
    tk.Label(tab, text="Từ khóa:").grid(row=len(labels) + 4, column=0, sticky="e", padx=5, pady=2) # Giảm pady
    search_entry = tk.Entry(tab)
    search_entry.grid(row=len(labels) + 4, column=1, pady=5, sticky="ew") # Giảm pady và thêm sticky="ew"
    tk.Button(tab, text="Tìm kiếm", bg="white", command=lambda: search_readers(reader_table)).grid(row=len(labels) + 5, column=0, pady=5, sticky="ew", columnspan=2)

    # Khung Sắp xếp
    tk.Label(tab, text="Sắp xếp theo:").grid(row=len(labels) + 6, column=0, sticky="e", padx=5, pady=5) # Giảm pady
    sort_type = ttk.Combobox(tab, values=["Họ tên (A-Z)", "Họ tên (Z-A)", "Mã số (tăng dần)", "Mã số (giảm dần)"])
    sort_type.set("Họ tên (A-Z)")
    sort_type.grid(row=len(labels) + 6, column=1, pady=5, sticky="ew") # Giảm pady và thêm sticky="ew"
    tk.Button(tab, bg="white", text="Sắp xếp", command=lambda: sort_readers(reader_table)).grid(row=len(labels) + 7, column=0, pady=5, sticky="ew", columnspan=2)

    tree.bind("<ButtonRelease-1>", load_selected_reader)
    refresh_tree()
