import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ============================\
# Cấu trúc dữ liệu cho phiếu mượn sách
# ============================\

class LoanRecord:
    def __init__(self, loan_id, reader_id, isbn, borrow_date, due_date, return_date=None, status="Đang mượn", book_title=None, reader_name=None):
        self.loan_id = loan_id
        self.reader_id = reader_id
        self.isbn = isbn
        self.borrow_date = datetime.strptime(borrow_date, "%Y-%m-%d %H:%M:%S.%f") if isinstance(borrow_date, str) else borrow_date
        self.due_date = datetime.strptime(due_date, "%Y-%m-%d %H:%M:%S.%f") if isinstance(due_date, str) else due_date
        self.return_date = datetime.strptime(return_date, "%Y-%m-%d %H:%M:%S.%f") if isinstance(return_date, str) and return_date != "None" else return_date
        self.status = status
        self.book_title = book_title  # Thêm thuộc tính tên sách
        self.reader_name = reader_name # Thêm thuộc tính tên bạn đọc

    def to_tuple(self):
        # Không cần book_title và reader_name trong tuple để lưu vào DB vì chúng được lấy từ bảng khác
        return (self.loan_id, self.reader_id, self.isbn,
                self.borrow_date.strftime("%Y-%m-%d %H:%M:%S.%f") if self.borrow_date else None,
                self.due_date.strftime("%Y-%m-%d %H:%M:%S.%f") if self.due_date else None,
                self.return_date.strftime("%Y-%m-%d %H:%M:%S.%f") if self.return_date else None,
                self.status)

    def __str__(self):
        return (f"ID Phiếu: {self.loan_id}, Bạn đọc ID: {self.reader_id} ({self.reader_name}), " # Hiển thị tên bạn đọc
                f"ISBN: {self.isbn} ({self.book_title}), " # Hiển thị tên sách
                f"Ngày mượn: {self.borrow_date.strftime('%Y-%m-%d')}, Ngày trả: {self.due_date.strftime('%Y-%m-%d')}, "
                f"Ngày thực trả: {self.return_date.strftime('%Y-%m-%d') if self.return_date else 'N/A'}, "
                f"Trạng thái: {self.status}")

# ============================\
# Cấu trúc dữ liệu cây tìm kiếm nhị phân (Binary Search Tree) cho phiếu mượn sách
# ============================\

class TreeNode:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.left = None
        self.right = None

class LoanBST:
    def __init__(self):
        self.root = None

    def insert(self, loan_record):
        key = loan_record.loan_id
        if self.root is None:
            self.root = TreeNode(key, loan_record)
        else:
            self._insert_recursive(self.root, key, loan_record)

    def _insert_recursive(self, node, key, loan_record):
        if key < node.key:
            if node.left is None:
                node.left = TreeNode(key, loan_record)
            else:
                self._insert_recursive(node.left, key, loan_record)
        elif key > node.key:
            if node.right is None:
                node.right = TreeNode(key, loan_record)
            else:
                self._insert_recursive(node.right, key, loan_record)
        else:
            node.value = loan_record # Update existing record if key is same

    def search(self, key):
        return self._search_recursive(self.root, key)

    def _search_recursive(self, node, key):
        if node is None or node.key == key:
            return node.value if node else None
        return self._search_recursive(node.left, key) if key < node.key else self._search_recursive(node.right, key)

    def delete(self, key):
        self.root = self._delete_recursive(self.root, key)

    def _delete_recursive(self, node, key):
        if not node:
            return node
        if key < node.key:
            node.left = self._delete_recursive(node.left, key)
        elif key > node.key:
            node.right = self._delete_recursive(node.right, key)
        else:
            if not node.left:
                return node.right
            elif not node.right:
                return node.left
            temp = self._min_value_node(node.right)
            node.key = temp.key
            node.value = temp.value
            node.right = self._delete_recursive(node.right, temp.key)
        return node

    def _min_value_node(self, node):
        while node.left:
            node = node.left
        return node

    def inorder(self):
        result = []
        self._inorder_recursive(self.root, result)
        return result

    def _inorder_recursive(self, node, result):
        if node:
            self._inorder_recursive(node.left, result)
            result.append(node.value)
            self._inorder_recursive(node.right, result)

class LoanManager:
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()
        self.loans = LoanBST()
        self._load_loans_from_db()

    def _load_loans_from_db(self):
        self.loans = LoanBST() # Reset BST
        self.cursor.execute("SELECT * FROM loans")
        rows = self.cursor.fetchall()
        for row in rows:
            loan_id, reader_id, isbn, borrow_date_str, due_date_str, return_date_str, status = row
            
            # Lấy tên sách và tên bạn đọc
            self.cursor.execute("SELECT title FROM books WHERE isbn = ?", (isbn,))
            book_title_result = self.cursor.fetchone()
            book_title = book_title_result[0] if book_title_result else "N/A"

            self.cursor.execute("SELECT name FROM readers WHERE reader_id = ?", (reader_id,))
            reader_name_result = self.cursor.fetchone()
            reader_name = reader_name_result[0] if reader_name_result else "N/A"

            borrow_date = datetime.strptime(borrow_date_str, "%Y-%m-%d %H:%M:%S.%f")
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d %H:%M:%S.%f")
            return_date = datetime.strptime(return_date_str, "%Y-%m-%d %H:%M:%S.%f") if return_date_str else None
            
            # Truyền thêm book_title và reader_name vào LoanRecord
            loan = LoanRecord(loan_id, reader_id, isbn, borrow_date, due_date, return_date, status, book_title, reader_name)
            self.loans.insert(loan)

    def _get_next_loan_id(self):
        self.cursor.execute("SELECT MAX(loan_id) FROM loans")
        max_id = self.cursor.fetchone()[0]
        return (max_id if max_id else 0) + 1

    def _reader_exists(self, reader_id):
        self.cursor.execute("SELECT 1 FROM readers WHERE reader_id = ?", (reader_id,))
        return self.cursor.fetchone() is not None

    def _book_exists(self, isbn):
        self.cursor.execute("SELECT 1 FROM books WHERE isbn = ?", (isbn,))
        return self.cursor.fetchone() is not None

    # Hàm bổ sung để kiểm tra sách đang được mượn bởi bạn đọc
    def _is_book_currently_borrowed_by_reader(self, reader_id, isbn):
        # Không dùng SQLite, chỉ duyệt qua dữ liệu trong RAM (BST)
        all_loans = self.loans.inorder()
        for loan in all_loans:
            if loan.reader_id == reader_id and loan.isbn == isbn and loan.status == "Đang mượn":
                return True
        return False

    def add_loan(self, reader_id, isbn):
        # Tải lại dữ liệu để đảm bảo BST có trạng thái mới nhất từ DB
        # (quan trọng vì các thao tác ở các tab khác có thể thay đổi DB)
        self._load_loans_from_db() 

        if not self._reader_exists(reader_id):
            messagebox.showerror("Lỗi", f"Mã bạn đọc '{reader_id}' không tồn tại.")
            return False
        if not self._book_exists(isbn):
            messagebox.showerror("Lỗi", f"Mã ISBN '{isbn}' không tồn tại.")
            return False
        
        # --- BỔ SUNG LOGIC KIỂM TRA TẠI ĐÂY ---
        if self._is_book_currently_borrowed_by_reader(reader_id, isbn):
            messagebox.showerror("Lỗi", f"Bạn đọc '{reader_id}' đang mượn sách có ISBN '{isbn}' và chưa trả.")
            return False
        # ------------------------------------

        self.cursor.execute("SELECT available_quantity FROM books WHERE isbn = ?", (isbn,))
        result = self.cursor.fetchone()
        if result and result[0] > 0:
            loan_id = self._get_next_loan_id()
            borrow_date = datetime.now()
            due_date = borrow_date + timedelta(days=14)

            # Lấy tên sách và tên bạn đọc ngay khi tạo phiếu mượn
            self.cursor.execute("SELECT title FROM books WHERE isbn = ?", (isbn,))
            book_title_result = self.cursor.fetchone()
            book_title = book_title_result[0] if book_title_result else "N/A"

            self.cursor.execute("SELECT name FROM readers WHERE reader_id = ?", (reader_id,))
            reader_name_result = self.cursor.fetchone()
            reader_name = reader_name_result[0] if reader_name_result else "N/A"

            loan = LoanRecord(loan_id, reader_id, isbn, borrow_date, due_date, book_title=book_title, reader_name=reader_name)
            self.loans.insert(loan)
            self.cursor.execute("INSERT INTO loans (loan_id, reader_id, isbn, borrow_date, due_date, status) VALUES (?, ?, ?, ?, ?, ?)",
                (loan_id, reader_id, isbn, borrow_date.strftime("%Y-%m-%d %H:%M:%S.%f"),
                 due_date.strftime("%Y-%m-%d %H:%M:%S.%f"), "Đang mượn"))
            self.cursor.execute("UPDATE books SET available_quantity = available_quantity - 1 WHERE isbn = ?", (isbn,))
            self.conn.commit()
            messagebox.showinfo("Thành công", "Đã tạo phiếu mượn.")
            return True
        else:
            messagebox.showerror("Lỗi", "Không còn sách để cho mượn.")
            return False

    def return_loan(self, loan_id):
        record = self.loans.search(loan_id)
        if record and record.status == "Đang mượn":
            record.return_date = datetime.now()
            record.status = "Đã trả"
            self.cursor.execute("UPDATE loans SET return_date=?, status=? WHERE loan_id=?",
                (record.return_date.strftime("%Y-%m-%d %H:%M:%S.%f"), record.status, loan_id))
            self.cursor.execute("UPDATE books SET available_quantity = available_quantity + 1 WHERE isbn = ?", (record.isbn,))
            self.conn.commit()
            # Cập nhật lại BST trong RAM sau khi trả sách thành công
            self._load_loans_from_db() 
            return True
        return False

    def get_all_loans(self):
        self._load_loans_from_db() # Reload to ensure latest book/reader names are fetched
        return self.loans.inorder()

    def get_loan_history_by_reader(self, reader_id):
        self._load_loans_from_db() # Reload
        return [loan for loan in self.get_all_loans() if loan.reader_id == reader_id]

    def get_loan_history_by_isbn(self, isbn):
        self._load_loans_from_db() # Reload
        return [loan for loan in self.get_all_loans() if loan.isbn == isbn]

    def get_current_loans_by_reader(self, reader_id):
        self._load_loans_from_db() # Reload
        return [loan for loan in self.get_all_loans() if loan.reader_id == reader_id and loan.status == "Đang mượn"]

    def get_overdue_loans(self):
        self._load_loans_from_db() # Reload
        today = datetime.now()
        return [loan for loan in self.get_all_loans() if loan.status == "Đang mượn" and loan.due_date < today]

    def count_loans_by_isbn(self):
        self._load_loans_from_db() # Reload
        stats = {}
        for loan in self.get_all_loans():
            stats[f"{loan.isbn} - {loan.book_title}"] = stats.get(f"{loan.isbn} - {loan.book_title}", 0) + 1 # Bao gồm tên sách
        return stats

    def delete_loan(self, loan_id):
        record = self.loans.search(loan_id)
        if record and record.status != "Đang mượn":
            self.loans.delete(loan_id)
            self.cursor.execute("DELETE FROM loans WHERE loan_id = ?", (loan_id,))
            self.conn.commit()
            # Cập nhật lại BST trong RAM sau khi xóa thành công
            self._load_loans_from_db()
            return True
        return False

    def get_loan_details(self, loan_id):
        self._load_loans_from_db() # Reload
        return self.loans.search(loan_id)


# ============================\
# Giao diện quản lý mượn/trả sách (hoàn chỉnh)
# ============================\

def create_loan_tab(notebook, loan_manager):
    tab = ttk.Frame(notebook)
    notebook.add(tab, text="📬 Quản lý Mượn/Trả")

    # Khung nhập liệu
    input_frame = ttk.LabelFrame(tab, text="Thông tin phiếu mượn")
    input_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

    tk.Label(input_frame, text="Mã bạn đọc:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    reader_id_entry = tk.Entry(input_frame)
    reader_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(input_frame, text="Mã ISBN sách:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    isbn_entry = tk.Entry(input_frame)
    isbn_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(input_frame, text="ID Phiếu Mượn:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
    loan_id_entry = tk.Entry(input_frame)
    loan_id_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

    # Khung hiển thị kết quả
    output_frame = ttk.LabelFrame(tab, text="Kết quả")
    output_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
    tab.grid_rowconfigure(1, weight=1)
    tab.grid_columnconfigure(0, weight=1)

    output_text = tk.Text(output_frame, height=20, wrap="none")
    output_text.pack(fill="both", expand=True)
    scroll_y = ttk.Scrollbar(output_frame, orient="vertical", command=output_text.yview)
    scroll_y.pack(side="right", fill="y")
    output_text.config(yscrollcommand=scroll_y.set)

    def display_loans(loans):
        output_text.delete("1.0", tk.END)
        if not loans:
            output_text.insert(tk.END, "Không có dữ liệu.\n")
            return
        # Cập nhật tiêu đề cột để bao gồm tên sách và tên bạn đọc
        output_text.insert(tk.END, f"{'ID':<5} {'Mã bạn đọc':<10} {'Tên bạn đọc':<20} {'ISBN':<15} {'Tên sách':<30} {'Mượn':<12} {'Đến hạn':<12} {'Trả':<12} {'Trạng thái':<10}\n")
        output_text.insert(tk.END, "-" * 150 + "\n") # Điều chỉnh độ dài dấu gạch ngang
        for loan in loans:
            output_text.insert(tk.END, f"{loan.loan_id:<5} {loan.reader_id:<10} {loan.reader_name:<20} {loan.isbn:<15} {loan.book_title:<30} {loan.borrow_date.strftime('%Y-%m-%d'):<12} {loan.due_date.strftime('%Y-%m-%d'):<12} {loan.return_date.strftime('%Y-%m-%d') if loan.return_date else 'N/A':<12} {loan.status:<10}\n")

    def display_loan_counts(counts):
        output_text.delete("1.0", tk.END)
        # Cập nhật tiêu đề cột để hiển thị tên sách
        output_text.insert(tk.END, f"{'ISBN - Tên sách':<45} {'Số lượt mượn':<15}\n")
        output_text.insert(tk.END, "-" * 60 + "\n")
        for isbn_title, count in counts.items():
            output_text.insert(tk.END, f"{isbn_title:<45} {count:<15}\n")

    def create_loan():
        # Đảm bảo các giá trị được strip để tránh khoảng trắng
        reader_id = reader_id_entry.get().strip()
        isbn = isbn_entry.get().strip()
        if loan_manager.add_loan(reader_id, isbn):
            # Sau khi thêm thành công, cần cập nhật lại Treeview
            display_loans(loan_manager.get_all_loans())

    def return_book():
        try:
            loan_id = int(loan_id_entry.get().strip())
            if loan_manager.return_loan(loan_id):
                messagebox.showinfo("Thành công", "Đã trả sách.")
                display_loans(loan_manager.get_all_loans()) # Refresh list after successful return
            else:
                messagebox.showerror("Lỗi", "Không thể trả sách. Có thể phiếu mượn không tồn tại hoặc đã được trả.")
        except ValueError:
            messagebox.showerror("Lỗi", "ID phiếu mượn không hợp lệ.")

    def delete_loan():
        try:
            loan_id = int(loan_id_entry.get().strip())
            if loan_manager.delete_loan(loan_id):
                messagebox.showinfo("Thành công", "Đã xoá phiếu mượn.")
                display_loans(loan_manager.get_all_loans()) # Refresh list after successful deletion
            else:
                messagebox.showerror("Lỗi", "Không thể xoá phiếu mượn. Chỉ có thể xoá phiếu đã trả.")
        except ValueError:
            messagebox.showerror("Lỗi", "ID phiếu mượn không hợp lệ.")

    def search_by_reader():
        display_loans(loan_manager.get_loan_history_by_reader(reader_id_entry.get().strip()))

    def search_by_isbn():
        display_loans(loan_manager.get_loan_history_by_isbn(isbn_entry.get().strip()))

    def show_current_loans():
        display_loans(loan_manager.get_current_loans_by_reader(reader_id_entry.get().strip()))

    def show_overdue():
        display_loans(loan_manager.get_overdue_loans())

    def show_statistics():
        display_loan_counts(loan_manager.count_loans_by_isbn())

    def show_all():
        display_loans(loan_manager.get_all_loans())

    # Các nút chức năng
    button_frame = ttk.Frame(tab)
    button_frame.grid(row=2, column=0, columnspan=2, pady=5)

    ttk.Button(button_frame, text="Tạo phiếu mượn", command=create_loan).grid(row=0, column=0, padx=2)
    ttk.Button(button_frame, text="Trả sách", command=return_book).grid(row=0, column=1, padx=2)
    ttk.Button(button_frame, text="Xoá phiếu mượn", command=delete_loan).grid(row=0, column=2, padx=2)
    ttk.Button(button_frame, text="Tìm theo bạn đọc", command=search_by_reader).grid(row=1, column=0, padx=2)
    ttk.Button(button_frame, text="Tìm theo ISBN", command=search_by_isbn).grid(row=1, column=1, padx=2)
    ttk.Button(button_frame, text="Sách đang mượn", command=show_current_loans).grid(row=1, column=2, padx=2)
    ttk.Button(button_frame, text="Sách quá hạn", command=show_overdue).grid(row=2, column=0, padx=2)
    ttk.Button(button_frame, text="Thống kê mượn theo ISBN", command=show_statistics).grid(row=2, column=1, padx=2)
    ttk.Button(button_frame, text="Xem tất cả", command=show_all).grid(row=2, column=2, padx=2)

    show_all()
