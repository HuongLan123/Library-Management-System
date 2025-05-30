import tkinter as tk
from tkinter import ttk, messagebox
import datetime # Cho các thao tác ngày tháng
import sqlite3
db_connection = sqlite3.connect("library3.db") # Kết nối CSDL SQLite
# ==============================================================================
# IMPORT CÁC LỚP CTDL TỰ CÀI ĐẶT VÀ ĐỐI TƯỢNG
# ==============================================================================
try:
    from ui_books import HashTable as BookHashTable, Book 

    from ui_readers import Reader 
 
    from ui_loans import LoanBST, TreeNode, LoanRecord, LoanManager 
except ImportError as e:
    messagebox.showerror("Lỗi Import (Module 4)", f"Không thể import CTDL/Đối tượng cần thiết: {e}\nKiểm tra lại đường dẫn và tên file.")


# ==============================================================================
# GIẢI THUẬT TỰ CÀI ĐẶT 
# ==============================================================================
def self_implemented_merge_sort(data_list, key_func=None, reverse=False):
    """Sắp xếp danh sách bằng Merge Sort tự cài đặt."""
    
    def merge_sort(arr):
        if len(arr) <= 1:
            return arr
        mid = len(arr) // 2
        left = merge_sort(arr[:mid])
        right = merge_sort(arr[mid:])
        return merge(left, right)

    def merge(left, right):
        merged = []
        i = j = 0
        while i < len(left) and j < len(right):
            a = key_func(left[i]) if key_func else left[i]
            b = key_func(right[j]) if key_func else right[j]
            if (a <= b) ^ reverse:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1
        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged

    return merge_sort(data_list)


def self_implemented_count_frequencies(list_of_objects, attribute_name_to_count):
    """Đếm tần suất của một thuộc tính trong danh sách đối tượng."""
    frequency_map_list = [] # List các tuple (giá trị thuộc tính, số lần đếm)
    if not list_of_objects:
        return frequency_map_list
    for obj_item in list_of_objects:
        try:
            key_to_count = getattr(obj_item, attribute_name_to_count)
        except AttributeError:
            print(f"Cảnh báo (Đếm tần suất): Đối tượng {type(obj_item)} không có thuộc tính '{attribute_name_to_count}'.")
            continue
        found_in_map = False
        for i, entry in enumerate(frequency_map_list):
            if entry[0] == key_to_count:
                frequency_map_list[i] = (entry[0], entry[1] + 1)
                found_in_map = True
                break
        if not found_in_map:
            frequency_map_list.append((key_to_count, 1))
    return frequency_map_list

# ==============================================================================
# UI MODULE 4 - BÁO CÁO & THỐNG KÊ
# ==============================================================================

def create_statistics_tab(notebook, db_connection):
    """
    Tạo tab Báo cáo & Thống kê.
    Dữ liệu được nạp từ CSDL vào các CTDL RAM riêng của Module 4 khi nhấn "Làm mới".
    Các hàm thống kê hoạt động trên các CTDL RAM này.
    """
    tab = ttk.Frame(notebook)
    notebook.add(tab, text="📊 Báo cáo & Thống kê")

    # Các instance CTDL trong bộ nhớ, dành riêng cho Module 4 này
    # Sẽ được nạp dữ liệu khi người dùng nhấn "Làm mới"
    ht_books_stats = BookHashTable() # Sử dụng HashTable từ ui_books
    ht_readers_stats = BookHashTable() # Giả sử dùng chung kiểu HashTable cho bạn đọc
    
    # LoanManager_stats sẽ quản lý LoanBST cho riêng Module 4 này
    # Khởi tạo LoanManager mà không cần ht_books, ht_readers của các module khác
    # vì nó sẽ dùng ht_books_stats và ht_readers_stats của riêng mình.
    # Nếu constructor của LoanManager yêu cầu, bạn có thể truyền chúng vào.
    loan_manager_stats = LoanManager(db_connection)
                                     # Hoặc LoanManager() nếu constructor cho phép

    # --- Giao diện ---
    output_text_area = tk.Text(tab, width=120, height=28, wrap=tk.WORD, font=("Consolas", 10), relief=tk.SUNKEN, borderwidth=1)
    output_text_area.grid(row=0, column=0, columnspan=3, padx=10, pady=(10,0), sticky="nsew")
    
    scrollbar = ttk.Scrollbar(tab, orient="vertical", command=output_text_area.yview)
    scrollbar.grid(row=0, column=3, sticky="ns", pady=(10,0))
    output_text_area.config(yscrollcommand=scrollbar.set)

    tab.grid_rowconfigure(0, weight=1) # Cho Text widget co giãn
    for i in range(3): 
        tab.grid_columnconfigure(i, weight=1)

    # --- Hàm nạp dữ liệu từ CSDL vào CTDL của Module 4 ---
    def refresh_data_for_statistics_command():
        ht_books_stats.size = 0 
        ht_books_stats.table = [type(ht_books_stats.table[0])() for _ in range(ht_books_stats.capacity)] # Tạo lại list các LinkedListForHash rỗng

        ht_readers_stats.size = 0
        ht_readers_stats.table = [type(ht_readers_stats.table[0])() for _ in range(ht_readers_stats.capacity)]
        
        loan_manager_stats.loans.root = None # Reset cây AVL
        loan_manager_stats.loan_id_counter = 1 # Reset counter

        cursor = db_connection.cursor()
        loaded_books_count = 0
        loaded_readers_count = 0
        loaded_loans_count = 0

        # Nạp sách
        try:
            for row in cursor.execute("SELECT isbn, title, author, year, quantity, available_quantity FROM books"):
                book = Book(row[0], row[1], row[2], int(row[3]), int(row[4]))
                book.available_quantity = int(row[5]) # Gán lại từ CSDL
                ht_books_stats.insert(book.isbn, book)
                loaded_books_count += 1
        except Exception as e:
            messagebox.showerror("Lỗi Nạp Sách (Stats)", f"Không thể nạp sách: {e}")
            return

        # Nạp bạn đọc
        try:
            for row in cursor.execute("SELECT reader_id, name, birth_date, address FROM readers"):
                reader = Reader(row[0], row[1], row[2], row[3])
                ht_readers_stats.insert(reader.reader_id, reader)
                loaded_readers_count += 1
        except Exception as e:
            messagebox.showerror("Lỗi Nạp Bạn Đọc (Stats)", f"Không thể nạp bạn đọc: {e}")
            return
            
        # Nạp phiếu mượn vào LoanBST của loan_manager_stats
        try:
            max_loan_id_db = 0
            for row in cursor.execute("SELECT loan_id, reader_id, isbn, borrow_date, due_date, return_date, status FROM loans"):
                try:
                    loan_id_from_db = int(row[0])
                    if loan_id_from_db > max_loan_id_db: max_loan_id_db = loan_id_from_db
                    #date.strftime("%Y-%m-%d %H:%M:%S.%f")
                    borrow_date_obj = datetime.datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S.%f").date() if row[3] else None
                    due_date_obj = datetime.datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S.%f").date() if row[4] else None
                    return_date_obj = datetime.datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S.%f").date() if row[5] else None
                    
                    if borrow_date_obj and due_date_obj: # Ngày mượn và hạn trả là bắt buộc
                        # Tạo LoanRecord với loan_id từ CSDL
                        loan = LoanRecord(loan_id_from_db, row[1], row[2], borrow_date_obj, due_date_obj, return_date_obj, row[6])
                        loan_manager_stats.loans.insert(loan) # Sử dụng insert của Loanloans
                        loaded_loans_count += 1
                    else:
                        print(f"Cảnh báo (Stats): Phiếu mượn {row[0]} thiếu ngày mượn/hạn trả, bỏ qua.")
                except ValueError as ve:
                    print(f"Cảnh báo (Stats): Phiếu mượn {row[0]} có định dạng ngày lỗi ({ve}), bỏ qua.")
            
            loan_manager_stats.loan_id_counter = max_loan_id_db + 1 # Cập nhật counter
            
            # Cập nhật trạng thái phiếu mượn sau khi nạp
            today = datetime.datetime.now().date()
            for record in loan_manager_stats.loans.inorder(): # Duyệt cây
                if record.return_date: record.status = "Đã trả"
                elif record.due_date and record.due_date < today: record.status = "Quá hạn"
                elif not record.return_date: record.status = "Đang mượn"
            
        except Exception as e:
            messagebox.showerror("Lỗi Nạp Phiếu Mượn (Stats)", f"Không thể nạp phiếu mượn: {e}")
            return
            
        messagebox.showinfo("Thành công", f"Đã làm mới dữ liệu cho thống kê từ CSDL.\nSách: {loaded_books_count}, Bạn đọc: {loaded_readers_count}, Phiếu mượn: {loaded_loans_count}")
        clear_output_area_command()
        output_text_area.insert(tk.END, "Dữ liệu đã được làm mới. Vui lòng chọn lại chức năng thống kê.\n")

    # --- Các hàm thống kê (hoạt động trên ht_books_stats, ht_readers_stats, loan_manager_stats) ---
    def clear_output_area_command():
        output_text_area.delete("1.0", tk.END)

    def display_top_n_books_command():
        clear_output_area_command()
        # Kiểm tra xem đã nạp dữ liệu chưa
        if ht_books_stats.size == 0 and not loan_manager_stats.loans.inorder():
            messagebox.showwarning("Chưa có dữ liệu", "Vui lòng 'Làm mới Dữ liệu Thống kê' trước.")
            return
        n_top = 10
        all_loan_records = loan_manager_stats.loans.inorder()
        if not all_loan_records:
            output_text_area.insert(tk.END, "Chưa có dữ liệu mượn sách để thống kê.\n"); return

        isbn_frequencies = self_implemented_count_frequencies(all_loan_records, "isbn")
        if not isbn_frequencies:
            output_text_area.insert(tk.END, "Không có ISBN nào được ghi nhận mượn.\n"); return
            
        sorted_top_books_data = self_implemented_merge_sort(list(isbn_frequencies), key_func=lambda pair: pair[1], reverse=True)

        output_text_area.insert(tk.END, f"--- Top {n_top} Sách Được Mượn Nhiều Nhất ---\n")
        for i, (isbn, count) in enumerate(sorted_top_books_data[:n_top], 1):
            book_object = ht_books_stats.search(isbn)
            title = book_object.title if book_object else f"[Sách ISBN {isbn} không tìm thấy]"
            output_text_area.insert(tk.END, f"Hạng {i}: {title} (ISBN: {isbn}) - Số lượt mượn: {count}\n")

    def display_top_n_readers_command():
        clear_output_area_command()
        if ht_readers_stats.size == 0 and not loan_manager_stats.loans.inorder():
            messagebox.showwarning("Chưa có dữ liệu", "Vui lòng 'Làm mới Dữ liệu Thống kê' trước.")
            return
        n_top = 10
        all_loan_records = loan_manager_stats.loans.inorder()
        if not all_loan_records:
            output_text_area.insert(tk.END, "Chưa có dữ liệu mượn sách để thống kê.\n"); return

        reader_id_frequencies = self_implemented_count_frequencies(all_loan_records, "reader_id")
        if not reader_id_frequencies:
            output_text_area.insert(tk.END, "Không có bạn đọc nào mượn sách.\n"); return
            
        sorted_top_readers_data = self_implemented_merge_sort(list(reader_id_frequencies), key_func=lambda pair: pair[1], reverse=True)

        output_text_area.insert(tk.END, f"--- Top {n_top} Bạn Đọc Mượn Sách Nhiều Nhất ---\n")
        for i, (reader_id, count) in enumerate(sorted_top_readers_data[:n_top], 1):
            reader_object = ht_readers_stats.search(reader_id)
            name = reader_object.name if reader_object else f"[Bạn đọc mã {reader_id} không tìm thấy]"
            output_text_area.insert(tk.END, f"Hạng {i}: {name} (Mã: {reader_id}) - Số lượt mượn: {count}\n")
    
    def display_total_books_stats_command():
        clear_output_area_command()
        if ht_books_stats.size == 0:
             messagebox.showwarning("Chưa có dữ liệu", "Vui lòng 'Làm mới Dữ liệu Thống kê' trước.")
             return
        num_titles = ht_books_stats.size
        all_book_objects = ht_books_stats.get_all_values()
        total_copies = sum(book.quantity for book in all_book_objects if book) if all_book_objects else 0
        output_text_area.insert(tk.END, "--- Thống Kê Tổng Số Sách ---\n")
        output_text_area.insert(tk.END, f"Tổng số đầu sách trong thư viện: {num_titles}\n")
        output_text_area.insert(tk.END, f"Tổng số cuốn sách trong thư viện: {total_copies}\n")

    def display_total_readers_stats_command():
        clear_output_area_command()
        if ht_readers_stats.size== 0:
             messagebox.showwarning("Chưa có dữ liệu", "Vui lòng 'Làm mới Dữ liệu Thống kê' trước.")
             return
        count = ht_readers_stats.size
        output_text_area.insert(tk.END, "--- Thống Kê Tổng Số Bạn Đọc ---\n")
        output_text_area.insert(tk.END, f"Tổng số bạn đọc đã đăng ký: {count}\n")

    def display_books_currently_loaned_stats_command():
        clear_output_area_command()
        all_loan_records = loan_manager_stats.loans.inorder()
        if not all_loan_records:
             messagebox.showwarning("Chưa có dữ liệu", "Vui lòng 'Làm mới Dữ liệu Thống kê' trước.")
             return
        
        # Cập nhật trạng thái trước khi đếm
        today = datetime.datetime.now().date()
        for record in all_loan_records:
            if record.return_date: record.status = "Đã trả"
            elif record.due_date and record.due_date < today: record.status = "Quá hạn"
            elif not record.return_date: record.status = "Đang mượn"
            
        count = sum(1 for loan in all_loan_records if loan and (loan.status == "Đang mượn" or loan.status == "Quá hạn"))
        output_text_area.insert(tk.END, "--- Thống Kê Sách Đang Được Mượn ---\n")
        output_text_area.insert(tk.END, f"Tổng số sách hiện đang được mượn (bao gồm quá hạn): {count}\n")

    def display_books_overdue_stats_command():
        clear_output_area_command()
        all_loan_records = loan_manager_stats.loans.inorder()
        if not all_loan_records:
             messagebox.showwarning("Chưa có dữ liệu", "Vui lòng 'Làm mới Dữ liệu Thống kê' trước.")
             return

        # Cập nhật trạng thái trước khi đếm
        today = datetime.datetime.now().date()
        for record in all_loan_records:
            if record.return_date: record.status = "Đã trả"
            elif record.due_date and record.due_date < today: record.status = "Quá hạn"
            elif not record.return_date: record.status = "Đang mượn"

        count = sum(1 for loan in all_loan_records if loan and loan.status == "Quá hạn")
        output_text_area.insert(tk.END, "--- Thống Kê Sách Đã Quá Hạn Trả ---\n")
        output_text_area.insert(tk.END, f"Tổng số sách đã quá hạn trả: {count}\n")

    # --- Tạo các nút bấm ---
    controls_frame = ttk.Frame(tab)
    controls_frame.grid(row=1, column=0, columnspan=3, pady=5, sticky="ew")

    btn_refresh_data = ttk.Button(controls_frame, text="🔄 LÀM MỚI DỮ LIỆU THỐNG KÊ TỪ CSDL", command=refresh_data_for_statistics_command, style="Accent.TButton")
    btn_refresh_data.pack(fill=tk.X, padx=5, pady=(5,10))
    
    stats_buttons_frame = ttk.Frame(controls_frame)
    stats_buttons_frame.pack(fill=tk.X, expand=True)
    stats_buttons_frame.columnconfigure(0, weight=1); stats_buttons_frame.columnconfigure(1, weight=1)

    btn_top_books = ttk.Button(stats_buttons_frame, text="🏆 Top Sách Mượn Nhiều", command=display_top_n_books_command)
    btn_top_books.grid(row=0, column=0, padx=5, pady=2, sticky="ew")
    btn_top_readers = ttk.Button(stats_buttons_frame, text="🥇 Top Bạn Đọc Mượn Nhiều", command=display_top_n_readers_command)
    btn_top_readers.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
    
    btn_total_books = ttk.Button(stats_buttons_frame, text="📚 Tổng Số Sách", command=display_total_books_stats_command)
    btn_total_books.grid(row=1, column=0, padx=5, pady=2, sticky="ew")
    btn_total_readers = ttk.Button(stats_buttons_frame, text="👥 Tổng Số Bạn Đọc", command=display_total_readers_stats_command)
    btn_total_readers.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
    
    btn_currently_loaned = ttk.Button(stats_buttons_frame, text="⏳ Sách Đang Mượn", command=display_books_currently_loaned_stats_command)
    btn_currently_loaned.grid(row=2, column=0, padx=5, pady=2, sticky="ew")
    btn_overdue = ttk.Button(stats_buttons_frame, text="⏰ Sách Quá Hạn Trả", command=display_books_overdue_stats_command)
    btn_overdue.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
    
    btn_clear = ttk.Button(controls_frame, text="🗑️ Xóa Kết Quả Hiển Thị", command=clear_output_area_command)
    btn_clear.pack(fill=tk.X, padx=5, pady=(10,5))
    
    # Thêm style cho nút (tùy chọn, cần import ttk.Style)
    # style = ttk.Style()
    # style.configure("Accent.TButton", foreground="blue", font=('Helvetica', 10, 'bold'))

    output_text_area.insert(tk.END, "Chào mừng đến Tab Thống kê!\n\n"
                                    "Để xem các số liệu mới nhất, vui lòng nhấn nút:\n"
                                    "'LÀM MỚI DỮ LIỆU THỐNG KÊ TỪ CSDL'\n\n"
                                    "Sau đó, bạn có thể chọn các chức năng thống kê bên dưới.\n")
