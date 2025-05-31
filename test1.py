import time
import tracemalloc
from datetime import datetime, timedelta

from ui_books import HashTable as BookHashTable, Book
from ui_readers import HashTable as ReaderHashTable, Reader
from ui_loans import LoanRecord, LoanBST
from ui_statistics import self_implemented_merge_sort, self_implemented_count_frequencies

sample_sizes = [50, 100, 1000, 10000]

def measure_performance(description, func, *args, **kwargs):
    tracemalloc.start()
    start_time = time.perf_counter()
    func(*args, **kwargs)
    end_time = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"{description:<60} | Time: {end_time - start_time:.6f} s | Peak Mem: {peak / 1024:.2f} KB")

def generate_books(n):
    return [Book(f"ISBN{i:05}", f"Title{i}", "Genre", f"Author{i}", 2000+i%20, i%10+1) for i in range(n)]

def generate_readers(n):
    return [Reader(f"RD{i:05}", f"Name{i}", "2000-01-01", f"Address{i}") for i in range(n)]

def generate_loans(n):
    today = datetime.now()
    return [
        LoanRecord(i, f"RD{i%100:05}", f"ISBN{i%100:05}", today - timedelta(days=i%30), today + timedelta(days=14))
        for i in range(n)
    ]

if __name__ == "__main__":
    for size in sample_sizes:
        print(f"\n--- Benchmark for size: {size} ---")

        # BOOK HASH TABLE
        books = generate_books(size)
        book_table = BookHashTable()
        measure_performance(f"Insert {size} books to HashTable", lambda: [book_table.insert(b.isbn, b) for b in books])
        measure_performance(f"Search {size} books in HashTable", lambda: [book_table.search(b.isbn) for b in books])
        measure_performance(f"Delete {size} books from HashTable", lambda: [book_table.delete(b.isbn) for b in books])
        [book_table.insert(b.isbn, b) for b in books]
        measure_performance(f"Update {size} books in HashTable", lambda: [book_table.insert(b.isbn, b) for b in books])
        measure_performance(f"get_all_values() with {size} books", book_table.get_all_values)
        measure_performance(f"Sort books by title (merge sort)", lambda: self_implemented_merge_sort(book_table.get_all_values(), key_func=lambda b: b.title))

        # READER HASH TABLE
        readers = generate_readers(size)
        reader_table = ReaderHashTable()
        measure_performance(f"Insert {size} readers to HashTable", lambda: [reader_table.insert(r.reader_id, r) for r in readers])
        measure_performance(f"Search {size} readers in HashTable", lambda: [reader_table.search(r.reader_id) for r in readers])
        measure_performance(f"Delete {size} readers from HashTable", lambda: [reader_table.delete(r.reader_id) for r in readers])
        [reader_table.insert(r.reader_id, r) for r in readers]
        measure_performance(f"Update {size} readers in HashTable", lambda: [reader_table.insert(r.reader_id, r) for r in readers])
        measure_performance(f"get_all_values() with {size} readers", reader_table.get_all_values)
        measure_performance(f"Sort readers by name (merge sort)", lambda: self_implemented_merge_sort(reader_table.get_all_values(), key_func=lambda r: r.name))

        # LOAN AVL TREE
        loans = generate_loans(size)
        loan_tree = LoanBST()
        measure_performance(f"Insert {size} loans to AVL Tree", lambda: [loan_tree.insert(l) for l in loans])
        measure_performance(f"Search {size} loans in AVL Tree", lambda: [loan_tree.search(l.loan_id) for l in loans])
        measure_performance(f"Delete {size} loans from AVL Tree", lambda: [loan_tree.delete(l.loan_id) for l in loans])
        [loan_tree.insert(l) for l in loans]
        measure_performance(f"Inorder traversal of {size} loans", loan_tree.inorder)
        measure_performance(f"Sort loans by due_date", lambda: self_implemented_merge_sort(loan_tree.inorder(), key_func=lambda l: l.due_date))

        # STATISTICS
        measure_performance(f"Count ISBN frequencies from {size} loans", lambda: self_implemented_count_frequencies(loans, "isbn"))
        measure_performance(f"Count reader frequencies from {size} loans", lambda: self_implemented_count_frequencies(loans, "reader_id"))
