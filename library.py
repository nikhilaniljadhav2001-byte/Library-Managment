
import os
import sys
import urllib.request
import tkinter as tk
from tkinter import ttk, messagebox

import mysql.connector
from mysql.connector import Error
from PIL import Image, ImageTk


# =========================================================
# CONFIGURATION
# =========================================================

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "Nikhil@2001"  # Replace with your MySQL password
DB_NAME = "library_db"

NAVY = "#17324d"
BLUE = "#2463a6"
BG = "#f2f5f9"
GREEN = "#168568"
RED = "#c84c55"
WHITE = "#ffffff"
GREY = "#65758b"

IMAGE_URL = (
    "https://images.unsplash.com/photo-1507842217343-583bb7270b66"
    "?auto=format&fit=crop&w=1400&q=85"
)


def resource_path(filename):
    """Find resources when running as Python or as a PyInstaller app."""
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_dir, filename)


ASSET_DIR = resource_path("assets")
IMAGE_PATH = os.path.join(ASSET_DIR, "library_bg.jpg")


# =========================================================
# IMAGE
# =========================================================

def prepare_image():
    """Download a background image if one is not already available."""
    os.makedirs(ASSET_DIR, exist_ok=True)

    if os.path.exists(IMAGE_PATH):
        return

    try:
        request = urllib.request.Request(
            IMAGE_URL,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(request, timeout=15) as response:
            image_data = response.read()

        with open(IMAGE_PATH, "wb") as image_file:
            image_file.write(image_data)

    except Exception as exc:
        print("Background image unavailable:", exc)


# =========================================================
# DATABASE
# =========================================================

def get_connection():
    """Connect to the library database."""
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


def initialize_database():
    """Create the database and required tables."""
    connection = None
    cursor = None

    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = connection.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`"
        )

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                author VARCHAR(150) NOT NULL,
                isbn VARCHAR(50),
                total_copies INT NOT NULL DEFAULT 1,
                available_copies INT NOT NULL DEFAULT 1
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS issued_books (
                id INT AUTO_INCREMENT PRIMARY KEY,
                book_id INT NOT NULL,
                member_name VARCHAR(150) NOT NULL,
                issue_date DATE NOT NULL,
                return_date DATE NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'Issued',
                FOREIGN KEY (book_id) REFERENCES books(id)
            )
        """)

        connection.commit()

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


# =========================================================
# MAIN APPLICATION
# =========================================================

class LibraryApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Library Management System")
        self.root.geometry("1150x750")
        self.root.minsize(950, 650)
        self.root.configure(bg=BG)

        self.selected_book_id = None
        self.photo = None

        self.setup_style()
        self.create_header()
        self.create_tabs()

        self.load_books(show_error=False)
        self.load_issued_books(show_error=False)
        self.update_stats(show_error=False)

    # -----------------------------------------------------
    # STYLES
    # -----------------------------------------------------

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background=WHITE,
            foreground="#243447",
            rowheight=29,
            fieldbackground=WHITE,
            font=("Arial", 10)
        )

        style.configure(
            "Treeview.Heading",
            background=NAVY,
            foreground=WHITE,
            font=("Arial", 10, "bold")
        )

        style.map(
            "Treeview",
            background=[("selected", "#c9e1ff")],
            foreground=[("selected", NAVY)]
        )

        style.configure(
            "TNotebook",
            background=BG,
            borderwidth=0
        )

        style.configure(
            "TNotebook.Tab",
            padding=(18, 10),
            font=("Arial", 10, "bold")
        )

    # -----------------------------------------------------
    # HEADER AND BACKGROUND
    # -----------------------------------------------------

    def create_header(self):
        header = tk.Frame(self.root, bg=NAVY, height=180)
        header.pack(fill="x")
        header.pack_propagate(False)

        title_panel = tk.Frame(header, bg=NAVY)

        try:
            prepare_image()

            if os.path.exists(IMAGE_PATH):
                image = Image.open(IMAGE_PATH).convert("RGB")
                image = image.resize((1150, 180))
                self.photo = ImageTk.PhotoImage(image)

                image_label = tk.Label(
                    header,
                    image=self.photo,
                    borderwidth=0
                )
                image_label.place(
                    x=0, y=0, relwidth=1, relheight=1
                )

        except Exception as exc:
            print("Background image error:", exc)

        title_panel.place(x=25, y=28)

        tk.Label(
            title_panel,
            text="LIBRARY MANAGEMENT SYSTEM",
            font=("Arial", 24, "bold"),
            fg=WHITE,
            bg=NAVY
        ).pack(anchor="w")

        tk.Label(
            title_panel,
            text="Manage books | Track issues | Record returns",
            font=("Arial", 11),
            fg="#e3edf7",
            bg=NAVY
        ).pack(anchor="w", pady=(7, 0))

        self.stats_label = tk.Label(
            self.root,
            text="Loading library data...",
            bg=BG,
            fg=NAVY,
            font=("Arial", 11, "bold"),
            anchor="w",
            padx=18,
            pady=10
        )
        self.stats_label.pack(fill="x")

    # -----------------------------------------------------
    # TABS
    # -----------------------------------------------------

    def create_tabs(self):
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0, 12)
        )

        self.books_tab = tk.Frame(self.tabs, bg=BG)
        self.issues_tab = tk.Frame(self.tabs, bg=BG)

        self.tabs.add(self.books_tab, text="  Books  ")
        self.tabs.add(self.issues_tab, text="  Issue / Return  ")

        self.create_books_page()
        self.create_issues_page()

    # -----------------------------------------------------
    # REUSABLE BUTTON
    # -----------------------------------------------------

    @staticmethod
    def make_button(parent, text, command, color):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg=WHITE,
            activebackground=color,
            activeforeground=WHITE,
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=12,
            pady=7,
            cursor="hand2"
        )

    # -----------------------------------------------------
    # BOOKS PAGE
    # -----------------------------------------------------

    def create_books_page(self):
        form = tk.LabelFrame(
            self.books_tab,
            text=" Book Details ",
            bg=BG,
            fg=NAVY,
            font=("Arial", 11, "bold"),
            padx=12,
            pady=12
        )
        form.pack(fill="x", padx=12, pady=12)

        self.title_var = tk.StringVar()
        self.author_var = tk.StringVar()
        self.isbn_var = tk.StringVar()
        self.copies_var = tk.StringVar(value="1")
        self.search_var = tk.StringVar()

        fields = [
            ("Book Title", self.title_var),
            ("Author", self.author_var),
            ("ISBN", self.isbn_var),
            ("Copies", self.copies_var)
        ]

        for index, (label_text, variable) in enumerate(fields):
            tk.Label(
                form,
                text=label_text,
                bg=BG,
                fg=NAVY,
                font=("Arial", 10, "bold")
            ).grid(
                row=0,
                column=index,
                sticky="w",
                padx=6,
                pady=(0, 5)
            )

            tk.Entry(
                form,
                textvariable=variable,
                font=("Arial", 10),
                width=23
            ).grid(
                row=1,
                column=index,
                sticky="ew",
                padx=6,
                pady=(0, 10)
            )

        for column in range(4):
            form.grid_columnconfigure(column, weight=1)

        buttons = tk.Frame(form, bg=BG)
        buttons.grid(
            row=2,
            column=0,
            columnspan=4,
            sticky="w",
            padx=5
        )

        self.make_button(
            buttons, "Add Book", self.add_book, GREEN
        ).pack(side="left", padx=(0, 8))

        self.make_button(
            buttons, "Update Selected", self.update_book, BLUE
        ).pack(side="left", padx=(0, 8))

        self.make_button(
            buttons, "Delete Selected", self.delete_book, RED
        ).pack(side="left", padx=(0, 8))

        self.make_button(
            buttons, "Clear Form", self.clear_form, GREY
        ).pack(side="left")

        search_frame = tk.Frame(self.books_tab, bg=BG)
        search_frame.pack(fill="x", padx=12, pady=(0, 10))

        tk.Label(
            search_frame,
            text="Search books:",
            bg=BG,
            fg=NAVY,
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=(0, 8))

        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Arial", 10),
            width=35
        )
        search_entry.pack(side="left", padx=(0, 8))
        search_entry.bind(
            "<KeyRelease>",
            lambda event: self.load_books(show_error=False)
        )

        self.make_button(
            search_frame, "Refresh", self.load_books, BLUE
        ).pack(side="left")

        table_frame = tk.Frame(self.books_tab, bg=BG)
        table_frame.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=(0, 12)
        )

        columns = (
            "id", "title", "author", "isbn", "total", "available"
        )

        self.books_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        headings = {
            "id": "ID",
            "title": "Book Title",
            "author": "Author",
            "isbn": "ISBN",
            "total": "Total Copies",
            "available": "Available"
        }

        widths = {
            "id": 55,
            "title": 260,
            "author": 200,
            "isbn": 150,
            "total": 110,
            "available": 100
        }

        for col in columns:
            self.books_tree.heading(col, text=headings[col])
            self.books_tree.column(
                col,
                width=widths[col],
                anchor="w"
            )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.books_tree.yview
        )

        self.books_tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.books_tree.pack(
            side="left",
            fill="both",
            expand=True
        )
        scrollbar.pack(side="right", fill="y")

        self.books_tree.bind(
            "<<TreeviewSelect>>",
            self.on_book_select
        )

    # -----------------------------------------------------
    # ISSUE AND RETURN PAGE
    # -----------------------------------------------------

    def create_issues_page(self):
        form = tk.LabelFrame(
            self.issues_tab,
            text=" Issue Selected Book ",
            bg=BG,
            fg=NAVY,
            font=("Arial", 11, "bold"),
            padx=12,
            pady=12
        )
        form.pack(fill="x", padx=12, pady=12)

        self.member_var = tk.StringVar()

        tk.Label(
            form,
            text="Member Name",
            bg=BG,
            fg=NAVY,
            font=("Arial", 10, "bold")
        ).grid(
            row=0, column=0, sticky="w", padx=6, pady=(0, 5)
        )

        tk.Entry(
            form,
            textvariable=self.member_var,
            font=("Arial", 10),
            width=35
        ).grid(
            row=1, column=0, sticky="w", padx=6
        )

        self.make_button(
            form,
            "Issue Selected Book",
            self.issue_book,
            GREEN
        ).grid(row=1, column=1, padx=12, sticky="w")

        tk.Label(
            form,
            text="First select a book in the Books tab.",
            bg=BG,
            fg="#526579",
            font=("Arial", 9)
        ).grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="w",
            padx=6,
            pady=8
        )

        table_frame = tk.Frame(self.issues_tab, bg=BG)
        table_frame.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=(0, 12)
        )

        columns = (
            "id", "book_id", "title", "member",
            "issue_date", "return_date", "status"
        )

        self.issues_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        headings = {
            "id": "Issue ID",
            "book_id": "Book ID",
            "title": "Book Title",
            "member": "Member",
            "issue_date": "Issue Date",
            "return_date": "Return Date",
            "status": "Status"
        }

        widths = {
            "id": 75,
            "book_id": 75,
            "title": 220,
            "member": 170,
            "issue_date": 115,
            "return_date": 115,
            "status": 90
        }

        for col in columns:
            self.issues_tree.heading(col, text=headings[col])
            self.issues_tree.column(
                col,
                width=widths[col],
                anchor="w"
            )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.issues_tree.yview
        )

        self.issues_tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.issues_tree.pack(
            side="left",
            fill="both",
            expand=True
        )
        scrollbar.pack(side="right", fill="y")

        self.make_button(
            self.issues_tab,
            "Return Selected Book",
            self.return_book,
            BLUE
        ).pack(anchor="w", padx=12, pady=(0, 12))

    # -----------------------------------------------------
    # ADD BOOK
    # -----------------------------------------------------

    def add_book(self):
        title = self.title_var.get().strip()
        author = self.author_var.get().strip()
        isbn = self.isbn_var.get().strip()
        copies_text = self.copies_var.get().strip()

        if not title or not author:
            messagebox.showerror(
                "Missing Details",
                "Enter both book title and author."
            )
            return

        try:
            copies = int(copies_text)
            if copies < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid Copies",
                "Copies must be a whole number of at least 1."
            )
            return

        connection = None
        cursor = None

        try:
            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO books
                    (title, author, isbn, total_copies, available_copies)
                VALUES (%s, %s, %s, %s, %s)
            """, (title, author, isbn, copies, copies))

            connection.commit()

            self.clear_form()
            self.refresh_all()

            messagebox.showinfo(
                "Success",
                "Book added successfully!"
            )

        except Error as exc:
            messagebox.showerror("Database Error", str(exc))

        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None and connection.is_connected():
                connection.close()

    # -----------------------------------------------------
    # LOAD AND SEARCH BOOKS
    # -----------------------------------------------------

    def load_books(self, show_error=True):
        if not hasattr(self, "books_tree"):
            return

        for item in self.books_tree.get_children():
            self.books_tree.delete(item)

        search = (
            self.search_var.get().strip()
            if hasattr(self, "search_var")
            else ""
        )

        connection = None
        cursor = None

        try:
            connection = get_connection()
            cursor = connection.cursor()

            pattern = f"%{search}%"

            cursor.execute("""
                SELECT id, title, author, isbn,
                       total_copies, available_copies
                FROM books
                WHERE title LIKE %s
                   OR author LIKE %s
                   OR isbn LIKE %s
                ORDER BY id DESC
            """, (pattern, pattern, pattern))

            for row in cursor.fetchall():
                self.books_tree.insert("", "end", values=row)

        except Error as exc:
            if show_error:
                messagebox.showerror("Database Error", str(exc))
            else:
                print("Load books error:", exc)

        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None and connection.is_connected():
                connection.close()

    # -----------------------------------------------------
    # SELECT BOOK
    # -----------------------------------------------------

    def on_book_select(self, event=None):
        selected = self.books_tree.selection()

        if not selected:
            return

        values = self.books_tree.item(
            selected[0], "values"
        )

        self.selected_book_id = int(values[0])
        self.title_var.set(values[1])
        self.author_var.set(values[2])
        self.isbn_var.set(values[3] or "")
        self.copies_var.set(str(values[4]))

    # -----------------------------------------------------
    # UPDATE BOOK
    # -----------------------------------------------------

    def update_book(self):
        if self.selected_book_id is None:
            messagebox.showwarning(
                "Select Book",
                "Select a book from the table first."
            )
            return

        title = self.title_var.get().strip()
        author = self.author_var.get().strip()
        isbn = self.isbn_var.get().strip()

        try:
            total = int(self.copies_var.get().strip())

            if not title or not author or total < 1:
                raise ValueError

        except ValueError:
            messagebox.showerror(
                "Invalid Details",
                "Enter title, author and valid copies."
            )
            return

        connection = None
        cursor = None

        try:
            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute("""
                SELECT total_copies, available_copies
                FROM books
                WHERE id = %s
            """, (self.selected_book_id,))

            row = cursor.fetchone()

            if row is None:
                messagebox.showerror(
                    "Not Found",
                    "This book no longer exists."
                )
                return

            old_total, old_available = row
            issued_count = old_total - old_available

            if total < issued_count:
                messagebox.showerror(
                    "Copies Error",
                    f"{issued_count} copies are currently issued. "
                    f"Total copies cannot be less than {issued_count}."
                )
                return

            new_available = total - issued_count

            cursor.execute("""
                UPDATE books
                SET title = %s,
                    author = %s,
                    isbn = %s,
                    total_copies = %s,
                    available_copies = %s
                WHERE id = %s
            """, (
                title,
                author,
                isbn,
                total,
                new_available,
                self.selected_book_id
            ))

            connection.commit()

            self.clear_form()
            self.refresh_all()

            messagebox.showinfo(
                "Success",
                "Book updated successfully."
            )

        except Error as exc:
            messagebox.showerror("Database Error", str(exc))

        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None and connection.is_connected():
                connection.close()

    # -----------------------------------------------------
    # DELETE BOOK
    # -----------------------------------------------------

    def delete_book(self):
        if self.selected_book_id is None:
            messagebox.showwarning(
                "Select Book",
                "Select a book from the table first."
            )
            return

        if not messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this book?"
        ):
            return

        connection = None
        cursor = None

        try:
            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute("""
                SELECT COUNT(*)
                FROM issued_books
                WHERE book_id = %s AND status = 'Issued'
            """, (self.selected_book_id,))

            active_issues = cursor.fetchone()[0]

            if active_issues:
                messagebox.showerror(
                    "Cannot Delete",
                    "This book has active issues. Return it first."
                )
                return

            cursor.execute(
                "DELETE FROM issued_books WHERE book_id = %s",
                (self.selected_book_id,)
            )

            cursor.execute(
                "DELETE FROM books WHERE id = %s",
                (self.selected_book_id,)
            )

            connection.commit()

            self.clear_form()
            self.refresh_all()

            messagebox.showinfo(
                "Deleted",
                "Book deleted successfully."
            )

        except Error as exc:
            if connection is not None and connection.is_connected():
                connection.rollback()

            messagebox.showerror("Database Error", str(exc))

        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None and connection.is_connected():
                connection.close()

    # -----------------------------------------------------
    # CLEAR FORM
    # -----------------------------------------------------

    def clear_form(self):
        self.selected_book_id = None

        self.title_var.set("")
        self.author_var.set("")
        self.isbn_var.set("")
        self.copies_var.set("1")

        if hasattr(self, "books_tree"):
            for item in self.books_tree.selection():
                self.books_tree.selection_remove(item)

    # -----------------------------------------------------
    # ISSUE BOOK
    # -----------------------------------------------------

    def issue_book(self):
        if self.selected_book_id is None:
            messagebox.showwarning(
                "Select Book",
                "Open the Books tab and select a book first."
            )
            return

        member = self.member_var.get().strip()

        if not member:
            messagebox.showerror(
                "Missing Member",
                "Enter the member's name."
            )
            return

        connection = None
        cursor = None

        try:
            connection = get_connection()
            connection.start_transaction()
            cursor = connection.cursor()

            cursor.execute("""
                SELECT available_copies
                FROM books
                WHERE id = %s
                FOR UPDATE
            """, (self.selected_book_id,))

            row = cursor.fetchone()

            if row is None:
                connection.rollback()
                messagebox.showerror("Not Found", "Book not found.")
                return

            if row[0] < 1:
                connection.rollback()
                messagebox.showwarning(
                    "Not Available",
                    "No copies of this book are available."
                )
                return

            cursor.execute("""
                INSERT INTO issued_books
                    (book_id, member_name, issue_date, status)
                VALUES (%s, %s, CURDATE(), 'Issued')
            """, (self.selected_book_id, member))

            cursor.execute("""
                UPDATE books
                SET available_copies = available_copies - 1
                WHERE id = %s
            """, (self.selected_book_id,))

            connection.commit()

            self.member_var.set("")
            self.refresh_all()

            messagebox.showinfo(
                "Success",
                "Book issued successfully!"
            )

        except Error as exc:
            if connection is not None and connection.is_connected():
                connection.rollback()

            messagebox.showerror("Database Error", str(exc))

        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None and connection.is_connected():
                connection.close()

    # -----------------------------------------------------
    # LOAD ISSUED BOOKS
    # -----------------------------------------------------

    def load_issued_books(self, show_error=True):
        if not hasattr(self, "issues_tree"):
            return

        for item in self.issues_tree.get_children():
            self.issues_tree.delete(item)

        connection = None
        cursor = None

        try:
            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute("""
                SELECT i.id, i.book_id, b.title, i.member_name,
                       i.issue_date, i.return_date, i.status
                FROM issued_books AS i
                JOIN books AS b ON b.id = i.book_id
                ORDER BY i.id DESC
            """)

            for row in cursor.fetchall():
                self.issues_tree.insert("", "end", values=row)

        except Error as exc:
            if show_error:
                messagebox.showerror("Database Error", str(exc))
            else:
                print("Load issued books error:", exc)

        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None and connection.is_connected():
                connection.close()

    # -----------------------------------------------------
    # RETURN BOOK
    # -----------------------------------------------------

    def return_book(self):
        selected = self.issues_tree.selection()

        if not selected:
            messagebox.showwarning(
                "Select Issue",
                "Select an issued book from the table."
            )
            return

        values = self.issues_tree.item(
            selected[0], "values"
        )

        issue_id = int(values[0])
        book_id = int(values[1])
        status = values[6]

        if status != "Issued":
            messagebox.showinfo(
                "Already Returned",
                "This book has already been returned."
            )
            return

        if not messagebox.askyesno(
            "Confirm Return",
            "Mark this book as returned?"
        ):
            return

        connection = None
        cursor = None

        try:
            connection = get_connection()
            connection.start_transaction()
            cursor = connection.cursor()

            cursor.execute("""
                UPDATE issued_books
                SET status = 'Returned',
                    return_date = CURDATE()
                WHERE id = %s AND status = 'Issued'
            """, (issue_id,))

            if cursor.rowcount == 1:
                cursor.execute("""
                    UPDATE books
                    SET available_copies = available_copies + 1
                    WHERE id = %s
                """, (book_id,))

                connection.commit()

                messagebox.showinfo(
                    "Success",
                    "Book returned successfully."
                )

            else:
                connection.rollback()

                messagebox.showinfo(
                    "Already Returned",
                    "This issue was already returned."
                )

            self.refresh_all()

        except Error as exc:
            if connection is not None and connection.is_connected():
                connection.rollback()

            messagebox.showerror("Database Error", str(exc))

        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None and connection.is_connected():
                connection.close()

    # -----------------------------------------------------
    # STATISTICS
    # -----------------------------------------------------

    def update_stats(self, show_error=True):
        connection = None
        cursor = None

        try:
            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute("""
                SELECT COUNT(*),
                       COALESCE(SUM(total_copies), 0),
                       COALESCE(SUM(available_copies), 0)
                FROM books
            """)

            books_count, total_copies, available = cursor.fetchone()

            cursor.execute("""
                SELECT COUNT(*)
                FROM issued_books
                WHERE status = 'Issued'
            """)

            issued = cursor.fetchone()[0]

            self.stats_label.config(
                text=(
                    f"Book Titles: {books_count}     "
                    f"Total Copies: {total_copies}     "
                    f"Available: {available}     "
                    f"Currently Issued: {issued}"
                )
            )

        except Error as exc:
            self.stats_label.config(
                text="Could not load library statistics."
            )

            if show_error:
                messagebox.showerror("Database Error", str(exc))
            else:
                print("Statistics error:", exc)

        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None and connection.is_connected():
                connection.close()

    # -----------------------------------------------------
    # REFRESH ALL DATA
    # -----------------------------------------------------

    def refresh_all(self):
        self.load_books(show_error=False)
        self.load_issued_books(show_error=False)
        self.update_stats(show_error=False)


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":
    try:
        initialize_database()

        root = tk.Tk()
        app = LibraryApp(root)
        root.mainloop()

    except Error as exc:
        error_root = tk.Tk()
        error_root.withdraw()

        messagebox.showerror(
            "MySQL Connection Error",
            "Could not connect to MySQL.\n\n"
            "Check that MySQL Server is running and your "
            "username/password are correct.\n\n"
            f"Details: {exc}"
        )

        error_root.destroy()
