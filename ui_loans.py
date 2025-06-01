import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
import sys
import io

# Cấu hình in Unicode ra console nếu chạy trên Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ===================================================
# Cấu trúc dữ liệu: Phiếu mượn sách & BST (có AVL logic)
# ===================================================

class LoanRecord:
    def __init__(self, loan_id, reader_id, isbn, borrow_date, due_date, return_date=None, status="Đang mượn", book_title=None, reader_name=None):
        self.loan_id = loan_id
        self.reader_id = reader_id
        self.isbn = isbn
        self.borrow_date = datetime.strptime(borrow_date, "%Y-%m-%d %H:%M:%S.%f") if isinstance(borrow_date, str) else borrow_date
        self.due_date = datetime.strptime(due_date, "%Y-%m-%d %H:%M:%S.%f") if isinstance(due_date, str) else due_date
        self.return_date = datetime.strptime(return_date, "%Y-%m-%d %H:%M:%S.%f") if isinstance(return_date, str) and return_date != "None" else return_date
        self.status = status
        self.book_title = book_title
        self.reader_name = reader_name

    def to_tuple(self):
        return (self.loan_id, self.reader_id, self.isbn,
                self.borrow_date.strftime("%Y-%m-%d %H:%M:%S.%f") if self.borrow_date else None,
                self.due_date.strftime("%Y-%m-%d %H:%M:%S.%f") if self.due_date else None,
                self.return_date.strftime("%Y-%m-%d %H:%M:%S.%f") if self.return_date else None,
                self.status)

    def __str__(self):
        return (f"ID Phiếu: {self.loan_id}, Bạn đọc ID: {self.reader_id} ({self.reader_name}), "
                f"ISBN: {self.isbn} ({self.book_title}), "
                f"Ngày mượn: {self.borrow_date.strftime('%Y-%m-%d')}, Ngày trả: {self.due_date.strftime('%Y-%m-%d')}, "
                f"Ngày thực trả: {self.return_date.strftime('%Y-%m-%d') if self.return_date else 'N/A'}, "
                f"Trạng thái: {self.status}")

class TreeNode:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.left = None
        self.right = None
        self.height = 1

class LoanBST:
    def __init__(self):
        self.root = None

    def _get_height(self, node):
        return node.height if node else 0

    def _get_balance(self, node):
        return self._get_height(node.left) - self._get_height(node.right) if node else 0

    def _rotate_left(self, z):
        y = z.right
        T2 = y.left
        y.left = z
        z.right = T2
        z.height = 1 + max(self._get_height(z.left), self._get_height(z.right))
        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))
        return y

    def _rotate_right(self, y):
        x = y.left
        T2 = x.right
        x.right = y
        y.left = T2
        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))
        x.height = 1 + max(self._get_height(x.left), self._get_height(x.right))
        return x

    def insert(self, loan_record):
        self.root = self._insert_recursive(self.root, loan_record.loan_id, loan_record)

    def _insert_recursive(self, node, key, record):
        if node is None:
            return TreeNode(key, record)

        if key < node.key:
            node.left = self._insert_recursive(node.left, key, record)
        else:
            node.right = self._insert_recursive(node.right, key, record)

        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))
        balance = self._get_balance(node)

        # AVL Balancing
        if balance > 1 and key < node.left.key:
            return self._rotate_right(node)
        if balance < -1 and key > node.right.key:
            return self._rotate_left(node)
        if balance > 1 and key > node.left.key:
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        if balance < -1 and key < node.right.key:
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)

        return node

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
            node.key, node.value = temp.key, temp.value
            node.right = self._delete_recursive(node.right, temp.key)
        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))
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
        self.cursor.execute("SELECT loan_id FROM loans")
        rows = self.cursor.fetchall()
        max_id = 0
        for row in rows:
            loan_id = row[0]
            if loan_id > max_id:
                max_id = loan_id
        return max_id + 1


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

    def add_loan(self, reader_id, isbn, duedays):
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
            due_date = borrow_date + timedelta(days=duedays)

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
    tk.Label(input_frame, text="Số ngày mượn:").grid(row=3, column=0, padx=5, pady=5, sticky="w")

# Ô nhập số ngày mượn
    duedays_entry = tk.Entry(input_frame)
    duedays_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
    # Khung hiển thị kết quả
    output_frame = ttk.LabelFrame(tab, text="Kết quả")
    output_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
    tab.grid_rowconfigure(1, weight=1)
    tab.grid_columnconfigure(0, weight=1)

    columns = ("loan_id", "reader_id", "reader_name", "isbn", "book_title", "borrow_date", "due_date", "return_date", "status")
    tree = ttk.Treeview(output_frame, columns=columns, show="headings")

    # Thiết lập tên cột và độ rộng
    tree.heading("loan_id", text="ID")
    tree.column("loan_id", width=50, anchor="center")

    tree.heading("reader_id", text="Mã bạn đọc")
    tree.column("reader_id", width=100)

    tree.heading("reader_name", text="Tên bạn đọc")
    tree.column("reader_name", width=150)

    tree.heading("isbn", text="ISBN")
    tree.column("isbn", width=120)

    tree.heading("book_title", text="Tên sách")
    tree.column("book_title", width=200)

    tree.heading("borrow_date", text="Ngày mượn")
    tree.column("borrow_date", width=100)

    tree.heading("due_date", text="Hạn trả")
    tree.column("due_date", width=100)

    tree.heading("return_date", text="Ngày trả")
    tree.column("return_date", width=100)

    tree.heading("status", text="Trạng thái")
    tree.column("status", width=100)

    # Thêm thanh cuộn
    scrollbar_y = ttk.Scrollbar(output_frame, orient="vertical", command=tree.yview)
    scrollbar_y.pack(side="right", fill="y")
    tree.configure(yscroll=scrollbar_y.set)

    scrollbar_x = ttk.Scrollbar(output_frame, orient="horizontal", command=tree.xview)
    scrollbar_x.pack(side="bottom", fill="x")
    tree.configure(xscroll=scrollbar_x.set)

    tree.pack(fill="both", expand=True)


    def display_loans(loans):
        for row in tree.get_children():
            tree.delete(row)
        if not loans:
            messagebox.showinfo("Thông báo", "Không có dữ liệu.")
            return
        for loan in loans:
            tree.insert("", "end", values=(
                loan.loan_id,
                loan.reader_id,
                loan.reader_name,
                loan.isbn,
                loan.book_title,
                loan.borrow_date.strftime('%Y-%m-%d'),
                loan.due_date.strftime('%Y-%m-%d'),
                loan.return_date.strftime('%Y-%m-%d') if loan.return_date else "N/A",
                loan.status
        ))


    def display_loan_counts(counts):
        # Xóa tất cả cột cũ
        for col in tree["columns"]:
            tree.heading(col, text="")
            tree.column(col, width=0)
        tree["columns"] = ("isbn_title", "count")

        tree.heading("isbn_title", text="ISBN - Tên sách")
        tree.column("isbn_title", width=400)

        tree.heading("count", text="Số lượt mượn")
        tree.column("count", width=100, anchor="center")

        # Xóa dữ liệu cũ
        for row in tree.get_children():
            tree.delete(row)

        if not counts:
            messagebox.showinfo("Thông báo", "Không có dữ liệu.")
            return

    # Thêm dữ liệu mới
        for isbn_title, count in counts.items():
            tree.insert("", "end", values=(isbn_title, count))


    def create_loan():
        # Đảm bảo các giá trị được strip để tránh khoảng trắng
        reader_id = reader_id_entry.get().strip()
        isbn = isbn_entry.get().strip()
        value = duedays_entry.get().strip()
        duedays = int(value) if value else 30
        if loan_manager.add_loan(reader_id, isbn,duedays):
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
        selected = tree.selection()
        if selected:
            try:
            # Lấy loan_id từ dòng đang chọn trên TreeView
                loan_id = int(tree.item(selected[0])["values"][0])
            except (IndexError, ValueError):
                messagebox.showerror("Lỗi", "Không thể đọc ID phiếu mượn từ bảng.")
                return
        else:
            # Nếu không chọn dòng nào, lấy từ ô nhập liệu
            try:
                loan_id = int(loan_id_entry.get().strip())
            except ValueError:
                messagebox.showerror("Lỗi", "ID phiếu mượn không hợp lệ.")
                return
        # Gọi hàm xóa
        if loan_manager.delete_loan(loan_id):
            messagebox.showinfo("Thành công", "Đã xoá phiếu mượn.")
            display_loans(loan_manager.get_all_loans()) # Refresh list after successful deletion
        else:
            messagebox.showerror("Lỗi", "Không thể xoá phiếu mượn. Chỉ có thể xoá phiếu đã trả.")


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
    original_columns = columns  # columns = ("loan_id", "reader_id", ..., "status")
    original_column_config = {
    "loan_id": {"text": "ID", "width": 50, "anchor": "center"},
    "reader_id": {"text": "Mã bạn đọc", "width": 100},
    "reader_name": {"text": "Tên bạn đọc", "width": 150},
    "isbn": {"text": "ISBN", "width": 120},
    "book_title": {"text": "Tên sách", "width": 200},
    "borrow_date": {"text": "Ngày mượn", "width": 100},
    "due_date": {"text": "Hạn trả", "width": 100},
    "return_date": {"text": "Ngày trả", "width": 100},
    "status": {"text": "Trạng thái", "width": 100},
}
    def reset_treeview_columns():
        tree["columns"] = original_columns
        for col in original_columns:
            cfg = original_column_config[col]
            tree.heading(col, text=cfg["text"])
            tree.column(col, width=cfg.get("width", 100), anchor=cfg.get("anchor", "w"))

    def show_all():
        reset_treeview_columns()  # Reset lại cấu hình cột
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
    ttk.Button(button_frame, text="Reset dữ liệu", command=show_all).grid(row=2, column=2, padx=2)

    show_all()
