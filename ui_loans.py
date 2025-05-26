import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ============================
# Cấu trúc dữ liệu cho phiếu mượn sách
# ============================

class LoanRecord:
    def __init__(self, loan_id, reader_id, isbn, borrow_date, due_date, return_date=None, status="Đang mượn"):
        self.loan_id = loan_id
        self.reader_id = reader_id
        self.isbn = isbn
        # Đảm bảo borrow_date và due_date là đối tượng datetime
        # Sử dụng format chuẩn cho SQLite datetime strings
        if isinstance(borrow_date, str):
            # CẬP NHẬT: Thêm %f để xử lý micro giây
            self.borrow_date = datetime.strptime(borrow_date, "%Y-%m-%d %H:%M:%S.%f")
        else:
            self.borrow_date = borrow_date

        if isinstance(due_date, str):
            # CẬP NHẬT: Thêm %f để xử lý micro giây
            self.due_date = datetime.strptime(due_date, "%Y-%m-%d %H:%M:%S.%f")
        else:
            self.due_date = due_date

        # return_date có thể là None
        if isinstance(return_date, str) and return_date:
            # CẬP NHẬT: Thêm %f để xử lý micro giây
            self.return_date = datetime.strptime(return_date, "%Y-%m-%d %H:%M:%S.%f")
        else:
            self.return_date = return_date
        self.status = status

# -------------------- AVL Tree Node --------------------
class TreeNode:
    def __init__(self, key, record):
        self.key = key
        self.record = record
        self.left = None
        self.right = None
        self.height = 1

# -------------------- LoanBST (AVL Tree) --------------------
class LoanBST:
    def __init__(self):
        self.root = None

    def insert(self, record):
        # Ensure key is unique, if not, handle collision (e.g., update or log)
        # If the record already exists based on loan_id, update it.
        # Otherwise, insert a new node.
        self.root = self._insert(self.root, record.loan_id, record)


    def _insert(self, node, key, record):
        if node is None:
            return TreeNode(key, record)

        if key < node.key:
            node.left = self._insert(node.left, key, record)
        elif key > node.key:
            node.right = self._insert(node.right, key, record)
        else:
            # If key already exists, update the record (important for DB sync)
            node.record = record
            return node

        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))
        balance = self._get_balance(node)

        # Cân bằng cây
        if balance > 1 and key < node.left.key:  # Left Left
            return self._rotate_right(node)
        if balance < -1 and key > node.right.key:  # Right Right
            return self._rotate_left(node)
        if balance > 1 and key > node.left.key:  # Left Right
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        if balance < -1 and key < node.right.key:  # Right Left
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)

        return node

    def search_by_loan_id(self, loan_id):
        return self._search(self.root, loan_id)

    def _search(self, node, key):
        if node is None or node.key == key:
            return node.record if node else None
        if key < node.key:
            return self._search(node.left, key)
        else:
            return self._search(node.right, key)

    def inorder(self):
        result = []
        self._inorder(self.root, result)
        return result

    def _inorder(self, node, result):
        if node:
            self._inorder(node.left, result)
            result.append(node.record)
            self._inorder(node.right, result)

    # AVL bổ trợ
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

# -------------------- LoanManager --------------------
class LoanManager:
    def __init__(self, db_name="library3.db"):
        self.bst = LoanBST()
        self.loan_id_counter = 1
        self.db_name = db_name
        self._initialize_db_table() # Đảm bảo bảng tồn tại trước khi tải
        self.load_loans_from_db() # Tải dữ liệu khi khởi tạo

    def _initialize_db_table(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS loans (
                loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                reader_id TEXT,
                isbn TEXT,
                borrow_date TEXT,
                due_date TEXT,
                return_date TEXT,
                status TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def save_loans_to_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        # Xóa tất cả dữ liệu cũ và chèn lại để đảm bảo đồng bộ
        cursor.execute("DELETE FROM loans")
        for record in self.bst.inorder():
            cursor.execute('''
                INSERT INTO loans (loan_id, reader_id, isbn, borrow_date, due_date, return_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.loan_id,
                record.reader_id,
                record.isbn,
                # CẬP NHẬT: Thêm %f khi lưu vào DB
                record.borrow_date.strftime("%Y-%m-%d %H:%M:%S.%f"),
                record.due_date.strftime("%Y-%m-%d %H:%M:%S.%f"),
                record.return_date.strftime("%Y-%m-%d %H:%M:%S.%f") if record.return_date else None,
                record.status
            ))
        conn.commit()
        conn.close()

    def load_loans_from_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM loans")
        rows = cursor.fetchall()
        # Reset BST before loading to prevent duplicates if called multiple times
        self.bst = LoanBST()
        for row in rows:
            loan_id, reader_id, isbn, borrow_date_str, due_date_str, return_date_str, status = row
            # Chuyển đổi chuỗi ngày thành đối tượng datetime
            try:
                # CẬP NHẬT: Thêm %f để xử lý micro giây khi đọc từ DB
                borrow_date = datetime.strptime(borrow_date_str, "%Y-%m-%d %H:%M:%S.%f")
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d %H:%M:%S.%f")
                return_date = datetime.strptime(return_date_str, "%Y-%m-%d %H:%M:%S.%f") if return_date_str else None
            except ValueError:
                # Fallback for old data without microseconds (e.g., if you had data before this fix)
                # You might need to refine this based on your exact data consistency.
                borrow_date = datetime.strptime(borrow_date_str, "%Y-%m-%d %H:%M:%S")
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d %H:%M:%S")
                return_date = datetime.strptime(return_date_str, "%Y-%m-%d %H:%M:%S") if return_date_str else None
                print(f"Warning: Loaded loan {loan_id} with old datetime format. Consider re-saving to update format.")
            
            record = LoanRecord(loan_id, reader_id, isbn, borrow_date, due_date, return_date, status)
            self.bst.insert(record)
            if loan_id >= self.loan_id_counter:
                self.loan_id_counter = loan_id + 1
        conn.close()


    def create_loan(self, reader_id, isbn, borrow_days=30):
        borrow_date = datetime.now()
        due_date = borrow_date + timedelta(days=borrow_days)
        new_loan = LoanRecord(
            loan_id=self.loan_id_counter,
            reader_id=reader_id,
            isbn=isbn,
            borrow_date=borrow_date,
            due_date=due_date
        )
        self.bst.insert(new_loan)
        self.save_loans_to_db() # Lưu vào DB sau khi tạo
        print(f"Tạo phiếu mượn thành công: Loan ID = {self.loan_id_counter}")
        self.loan_id_counter += 1

    def return_book(self, loan_id):
        record = self.bst.search_by_loan_id(loan_id)
        if record and record.status == "Đang mượn":
            record.return_date = datetime.now()
            record.status = "Đã trả"
            # Since the BST's node.record is a direct reference,
            # updating it directly means the BST 'contains' the updated record.
            # Now, just resave the entire BST to the DB.
            self.save_loans_to_db()
            print(f"Trả sách thành công cho phiếu mượn {loan_id}")
            return True
        else:
            print(f"Không tìm thấy phiếu mượn hợp lệ (ID: {loan_id}) để trả hoặc đã được trả.")
            return False

    def show_current_loans(self, reader_id):
        found = False
        for record in self.bst.inorder():
            if record.reader_id == reader_id and record.status == "Đang mượn":
                print(f"Loan ID: {record.loan_id}, ISBN: {record.isbn}, Due: {record.due_date.date()}")
                found = True
        if not found:
            print("Không có sách đang mượn")

    def show_overdue_loans(self, check_date):
        found = False
        for record in self.bst.inorder():
            if record.status == "Đang mượn" and record.due_date.date() < check_date:
                print(f"Loan ID: {record.loan_id}, Reader: {record.reader_id}, ISBN: {record.isbn}, Due: {record.due_date.date()}")
                found = True
        if not found:
            print("Không có phiếu mượn quá hạn")

    def get_loan_history_by_reader(self, reader_id):
        loan_ids = []
        for record in self.bst.inorder():
            if record.reader_id == reader_id:
                loan_ids.append(record.loan_id)
        if loan_ids:
            print(f"Lịch sử mượn của bạn đọc {reader_id}: {loan_ids}")
        else:
            print("Không có lịch sử mượn")
        return loan_ids

    def get_loan_history_by_isbn(self, isbn):
        found = False
        for record in self.bst.inorder():
            if record.isbn == isbn:
                print(f"Loan ID: {record.loan_id}, Reader: {record.reader_id}, Ngày mượn: {record.borrow_date.date()}, Ngày trả: {record.return_date.date() if record.return_date else 'Chưa trả'}")
                found = True
        if not found:
            print("Chưa có lịch sử mượn cho quyển sách này")
    
    def count_loans_by_isbn(self):
        stats = {}
        for record in self.bst.inorder():
            isbn = record.isbn
            if isbn not in stats:
                stats[isbn] = {"Đang mượn": 0, "Đã trả": 0}
            # Phòng trường hợp status có giá trị ngoài 2 loại trên
            if record.status in stats[isbn]:
                stats[isbn][record.status] += 1
            else:
                stats[isbn][record.status] = 1 # Tự động thêm nếu trạng thái mới

        if stats:
            print("Thống kê mượn/trả theo ISBN:")
            for isbn, counts in stats.items():
                print(f"ISBN: {isbn} | Đang mượn: {counts.get('Đang mượn', 0)} | Đã trả: {counts.get('Đã trả', 0)}")
        else:
            print("Chưa có dữ liệu mượn sách.")
        return stats


# ============================
# Giao diện quản lý mượn - trả
# ============================

def create_loan_tab(notebook, loan_manager: LoanManager):
    tab = ttk.Frame(notebook)
    notebook.add(tab, text="Mượn - Trả Sách")

    labels = ["Mã bạn đọc", "ISBN", "Số ngày mượn (mặc định 30)"]
    entries = {}
    for i, label in enumerate(labels):
        tk.Label(tab, text=label).grid(row=i, column=0, padx=5, pady=5, sticky="e")
        entry = tk.Entry(tab)
        entry.grid(row=i, column=1, padx=5, pady=5, sticky="w")
        entries[label] = entry

    tree = ttk.Treeview(tab, columns=("Loan ID", "Reader ID", "ISBN", "Ngày mượn", "Hạn trả", "Ngày trả", "Trạng thái"), show="headings")
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, width=100)
    tree.grid(row=0, column=2, rowspan=15, padx=10, pady=5)

    output_text = tk.Text(tab, width=50, height=15)
    output_text.grid(row=6, column=0, columnspan=2, padx=5, pady=5)

    def refresh_tree():
        tree.delete(*tree.get_children())
        for record in loan_manager.bst.inorder():
            # CẬP NHẬT: Thêm %f khi hiển thị trên Treeview
            borrow = record.borrow_date.strftime("%Y-%m-%d %H:%M:%S.%f")
            due = record.due_date.strftime("%Y-%m-%d %H:%M:%S.%f")
            ret = record.return_date.strftime("%Y-%m-%d %H:%M:%S.%f") if record.return_date else ""
            tree.insert("", "end", values=(
                record.loan_id,
                record.reader_id,
                record.isbn,
                borrow,
                due,
                ret,
                record.status
            ))

    def create_loan():
        reader_id = entries["Mã bạn đọc"].get().strip()
        isbn = entries["ISBN"].get().strip()
        days_str = entries["Số ngày mượn (mặc định 30)"].get().strip()
        days = int(days_str) if days_str.isdigit() else 30

        if not reader_id or not isbn:
            messagebox.showwarning("Lỗi", "Mã bạn đọc và ISBN không được để trống.")
            return

        loan_manager.create_loan(reader_id, isbn, days)
        refresh_tree()
        messagebox.showinfo("Thành công", f"Đã tạo phiếu mượn cho bạn đọc {reader_id}")
        # Clear entries after successful creation
        entries["Mã bạn đọc"].delete(0, tk.END)
        entries["ISBN"].delete(0, tk.END)
        entries["Số ngày mượn (mặc định 30)"].delete(0, tk.END)

    def return_book():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Thông báo", "Vui lòng chọn phiếu mượn để trả sách.")
            return
        
        # Lấy loan_id từ hàng được chọn
        loan_id = tree.item(selected[0])["values"][0]
        
        if loan_manager.return_book(loan_id):
            refresh_tree()
            messagebox.showinfo("Trả sách", f"Phiếu #{loan_id} đã trả sách")
        else:
            messagebox.showwarning("Thông báo", f"Không thể trả sách cho phiếu #{loan_id}. Có thể phiếu đã được trả hoặc không tồn tại.")

    def search_loan_history_by_reader():
        output_text.delete("1.0", tk.END)
        reader_id = entries["Mã bạn đọc"].get().strip()
        if not reader_id:
            messagebox.showwarning("Lỗi", "Nhập mã bạn đọc để tìm kiếm lịch sử mượn.")
            return
        
        found_records = [rec for rec in loan_manager.bst.inorder() if rec.reader_id == reader_id]
        if found_records:
            output_text.insert(tk.END, f"Lịch sử mượn của bạn đọc {reader_id}:\n")
            for record in found_records:
                borrow_date = record.borrow_date.strftime("%Y-%m-%d %H:%M:%S.%f") # CẬP NHẬT: Thêm %f
                return_date = record.return_date.strftime("%Y-%m-%d %H:%M:%S.%f") if record.return_date else "Chưa trả" # CẬP NHẬT: Thêm %f
                output_text.insert(tk.END, f"  Loan ID: {record.loan_id}, ISBN: {record.isbn}, Ngày mượn: {borrow_date}, Ngày trả: {return_date}, Trạng thái: {record.status}\n")
        else:
            output_text.insert(tk.END, "Không có lịch sử mượn\n")

    def search_loan_history_by_isbn():
        output_text.delete("1.0", tk.END)
        isbn = entries["ISBN"].get().strip()
        if not isbn:
            messagebox.showwarning("Lỗi", "Nhập ISBN để tìm kiếm lịch sử mượn.")
            return
        
        found_records = [rec for rec in loan_manager.bst.inorder() if rec.isbn == isbn]
        if found_records:
            output_text.insert(tk.END, f"Lịch sử mượn của sách ISBN '{isbn}':\n")
            for record in found_records:
                borrow_date = record.borrow_date.strftime("%Y-%m-%d %H:%M:%S.%f") # CẬP NHẬT: Thêm %f
                return_date = record.return_date.strftime("%Y-%m-%d %H:%M:%S.%f") if record.return_date else "Chưa trả" # CẬP NHẬT: Thêm %f
                output_text.insert(tk.END, f"  Loan ID: {record.loan_id}, Bạn đọc: {record.reader_id}, Ngày mượn: {borrow_date}, Ngày trả: {return_date}, Trạng thái: {record.status}\n")
        else:
            output_text.insert(tk.END, "Chưa có lịch sử mượn cho quyển sách này\n")

    def show_current_loans_by_reader():
        output_text.delete("1.0", tk.END)
        reader_id = entries["Mã bạn đọc"].get().strip()
        if not reader_id:
            messagebox.showwarning("Lỗi", "Nhập mã bạn đọc để xem sách đang mượn.")
            return
        found = False
        for record in loan_manager.bst.inorder():
            if record.reader_id == reader_id and record.status == "Đang mượn":
                due = record.due_date.strftime("%Y-%m-%d %H:%M:%S.%f") # CẬP NHẬT: Thêm %f
                output_text.insert(tk.END, f"Loan ID: {record.loan_id}, ISBN: {record.isbn}, Hạn trả: {due}\n")
                found = True
        if not found:
            output_text.insert(tk.END, "Không có sách đang mượn\n")

    def show_overdue_loans():
        output_text.delete("1.0", tk.END)
        check_date = datetime.now().date() # Sử dụng ngày hiện tại
        found = False
        for record in loan_manager.bst.inorder():
            if record.status == "Đang mượn" and record.due_date.date() < check_date:
                due = record.due_date.strftime("%Y-%m-%d %H:%M:%S.%f") # CẬP NHẬT: Thêm %f
                output_text.insert(tk.END, f"Loan ID: {record.loan_id}, Bạn đọc: {record.reader_id}, ISBN: {record.isbn}, Hạn trả: {due}\n")
                found = True
        if not found:
            output_text.insert(tk.END, "Không có phiếu mượn quá hạn\n")

    def count_loans_by_isbn():
        output_text.delete("1.0", tk.END)
        stats = loan_manager.count_loans_by_isbn()
        if stats:
            output_text.insert(tk.END, "Thống kê mượn/trả theo ISBN:\n")
            for isbn, counts in stats.items():
                output_text.insert(tk.END, f"ISBN: {isbn} | Đang mượn: {counts.get('Đang mượn', 0)} | Đã trả: {counts.get('Đã trả', 0)}\n")
        else:
            output_text.insert(tk.END, "Chưa có dữ liệu mượn sách.\n")

    tk.Button(tab, text="Tạo phiếu mượn", command=create_loan).grid(row=4, column=0, pady=10)
    tk.Button(tab, text="Trả sách", command=return_book).grid(row=4, column=1, pady=10)

    tk.Button(tab, text="Lịch sử mượn theo bạn đọc", command=search_loan_history_by_reader).grid(row=7, column=0, pady=5, sticky="ew")
    tk.Button(tab, text="Lịch sử mượn theo ISBN", command=search_loan_history_by_isbn).grid(row=7, column=1, pady=5, sticky="ew")

    tk.Button(tab, text="Sách đang mượn của bạn đọc", command=show_current_loans_by_reader).grid(row=8, column=0, pady=5, sticky="ew")
    tk.Button(tab, text="Sách quá hạn", command=show_overdue_loans).grid(row=8, column=1, pady=5, sticky="ew")

    tk.Button(tab, text="Thống kê mượn/trả theo ISBN", command=count_loans_by_isbn).grid(row=9, column=0, columnspan=2, pady=5, sticky="ew")

    tk.Button(tab, text="Xóa ô kết quả", command=lambda: output_text.delete("1.0", tk.END)).grid(row=10, column=0, columnspan=2, pady=5)

    refresh_tree()

# Ví dụ cách sử dụng (thêm vào phần khởi tạo ứng dụng chính của bạn)
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Quản lý Thư viện")

    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill="both")

    loan_manager = LoanManager() # Khởi tạo LoanManager, dữ liệu sẽ được load từ DB

    create_loan_tab(notebook, loan_manager)

    root.mainloop()
