import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import requests
import threading

API_URL = "http://127.0.0.1:5000"

# test credentials
# customer
# username: testuser
# password: pass    
# 
# manager
# username: testmanager  
# password: pass

class BookstoreApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Online Bookstore Desktop Client")
        self.root.geometry("950x700") 
        
        self.session = {} 
        self.cart = []
        
        self.target_role = "customer" 
        self.manager_secret = ""

        self.show_login_screen()

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # --- AUTH ---
    def show_login_screen(self):
        self.clear_screen()
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(expand=True)
        
        tk.Label(frame, text="Bookstore Login", font=("Arial", 16)).pack(pady=10)
        
        tk.Label(frame, text="Username").pack()
        self.entry_user = tk.Entry(frame)
        self.entry_user.pack()
        
        tk.Label(frame, text="Password").pack()
        self.entry_pass = tk.Entry(frame, show="*")
        self.entry_pass.pack()
        
        tk.Button(frame, text="Login", command=self.handle_login, bg="#4CAF50", fg="white").pack(pady=10, fill='x')
        tk.Button(frame, text="Create Account", command=self.show_register_screen).pack(pady=5, fill='x')

    def show_register_screen(self):
        self.clear_screen()
        self.target_role = "customer"
        self.manager_secret = ""

        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(expand=True)
        
        self.lbl_title = tk.Label(frame, text="Create Customer Account", font=("Arial", 16))
        self.lbl_title.pack(pady=10)

        tk.Label(frame, text="Full Name").pack()
        self.reg_name = tk.Entry(frame)
        self.reg_name.pack()
        
        tk.Label(frame, text="Username").pack()
        self.reg_user = tk.Entry(frame)
        self.reg_user.pack()
        
        tk.Label(frame, text="Email").pack()
        self.reg_email = tk.Entry(frame)
        self.reg_email.pack()
        
        verify_frame = tk.Frame(frame)
        verify_frame.pack(pady=5)
        tk.Button(verify_frame, text="Send Code", command=self.request_code, bg="#FF9800", fg="white").pack(side='left')
        tk.Label(frame, text="Enter Code from Email").pack()
        self.reg_code = tk.Entry(frame)
        self.reg_code.pack()
        
        tk.Label(frame, text="Password").pack()
        self.reg_pass = tk.Entry(frame, show="*")
        self.reg_pass.pack()
        
        tk.Button(frame, text="Sign Up", command=self.handle_register, bg="#2196F3", fg="white").pack(pady=10, fill='x')
        tk.Button(frame, text="Back to Login", command=self.show_login_screen).pack(pady=5, fill='x')

        tk.Label(frame, text="--- OR ---").pack(pady=10)
        tk.Button(frame, text="Create Manager Account", command=self.prompt_manager_code, fg="red").pack()

    def prompt_manager_code(self):
        code = simpledialog.askstring("Manager Access", "Enter Manager Code:", show='*')
        if code:
            self.manager_secret = code
            self.target_role = "manager"
            self.lbl_title.config(text="Create MANAGER Account", fg="red")
            messagebox.showinfo("Access Granted", "Manager mode enabled. Please complete the form above.")

    def request_code(self):
        email = self.reg_email.get()
        if not email: return
        threading.Thread(target=lambda: requests.post(f"{API_URL}/send-code", json={"email": email})).start()
        messagebox.showinfo("Sent", "Check email for code")

    def handle_register(self):
        data = {
            "username": self.reg_user.get(),
            "password": self.reg_pass.get(),
            "email": self.reg_email.get(),
            "full_name": self.reg_name.get(),
            "code": self.reg_code.get(),
            "role": self.target_role,
            "manager_secret": self.manager_secret
        }
        def run():
            try:
                resp = requests.post(f"{API_URL}/register", json=data)
                if resp.status_code == 201:
                    self.root.after(0, lambda: [messagebox.showinfo("Success", "Account created!"), self.show_login_screen()])
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", resp.text))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e))) 
        threading.Thread(target=run).start()

    def handle_login(self):
        username = self.entry_user.get()
        password = self.entry_pass.get()
        def run():
            try:
                resp = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
                if resp.status_code == 200:
                    self.session = resp.json()
                    self.root.after(0, self.route_dashboard)
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Invalid Login"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=run).start()

    def route_dashboard(self):
        if self.session.get('role') == 'manager':
            self.show_manager_dashboard()
        else:
            self.show_customer_dashboard()

    # --- CUSTOMER ---
    def show_customer_dashboard(self):
        self.clear_screen()

        display_name = self.session.get('full_name') or self.session.get('username') or "User"

        header = tk.Frame(self.root, bg="#eee", pady=10)
        header.pack(fill='x')
        tk.Label(header, text=f"Welcome, {display_name}", bg="#eee").pack(side='left', padx=10)

        tk.Button(header, text="Logout", command=self.show_login_screen).pack(side='right', padx=10)
        tk.Button(header, text=f"Cart ({len(self.cart)})", command=self.show_cart).pack(side='right', padx=10)
        tk.Button(header, text="Profile", command=self.show_profile_view, bg="#2196F3", fg="white").pack(side='right', padx=10)

        search_frame = tk.Frame(self.root, pady=10)
        search_frame.pack()
        self.search_entry = tk.Entry(search_frame, width=30)
        self.search_entry.pack(side='left', padx=5)
        tk.Button(search_frame, text="Search", command=self.search_books).pack(side='left')

        cols = ('ID', 'Title', 'Author', 'Stock', 'Buy $', 'Rent $')
        self.tree = ttk.Treeview(self.root, columns=cols, show='headings')
        for col in cols: self.tree.heading(col, text=col)
        self.tree.column('ID', width=40); self.tree.column('Stock', width=50)
        self.tree.pack(expand=True, fill='both', padx=20, pady=10)
        
        btn_frame = tk.Frame(self.root, pady=10)
        btn_frame.pack()
        tk.Button(btn_frame, text="Add to Cart (Buy)", command=lambda: self.add_to_cart('buy')).pack(side='left', padx=10)
        tk.Button(btn_frame, text="Add to Cart (Rent)", command=lambda: self.add_to_cart('rent')).pack(side='left', padx=10)
        tk.Button(btn_frame, text="View Ratings/Reviews", command=self.view_book_reviews, bg="#9C27B0", fg="white").pack(side='left', padx=10)

        self.search_books() # auto calls this function to show all books immediately after login

    def view_book_reviews(self):
        sel = self.tree.focus()
        if not sel: 
            messagebox.showinfo("Select", "Please select a book to view reviews.")
            return
        vals = self.tree.item(sel)['values']
        book_id = vals[0]
        book_title = vals[1]

        # Fetch reviews
        try:
            resp = requests.get(f"{API_URL}/reviews/book/{book_id}")
            if resp.status_code == 200:
                data = resp.json()
                reviews = data.get('reviews', [])
                avg = data.get('average', 0)
                
                # Show Popup
                top = tk.Toplevel(self.root)
                top.title(f"Reviews for: {book_title}")
                top.geometry("500x400")

                tk.Label(top, text=f"Average Rating: {avg}/10", font=("Arial", 14, "bold"), pady=10).pack()
                
                # Scrollable list for reviews
                container = tk.Frame(top)
                container.pack(fill='both', expand=True, padx=10, pady=10)
                
                canvas = tk.Canvas(container)
                scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
                scrollable_frame = tk.Frame(canvas)

                scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
                canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)

                canvas.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")

                if not reviews:
                    tk.Label(scrollable_frame, text="No reviews yet.").pack(pady=20)
                
                for r in reviews:
                    f = tk.Frame(scrollable_frame, relief="groove", borderwidth=1, padx=5, pady=5)
                    f.pack(fill='x', pady=5)
                    tk.Label(f, text=f"Rating: {r['rating']}/10", font=("Arial", 10, "bold")).pack(anchor='w')
                    tk.Label(f, text=r['review_text'], wraplength=400, justify="left").pack(anchor='w')
                    tk.Label(f, text=f"Posted: {r['created_at']}", fg="gray", font=("Arial", 8)).pack(anchor='e')

            else:
                messagebox.showerror("Error", "Could not load reviews")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_profile_view(self):
        self.clear_screen()
        
        # --- Header ---
        header = tk.Frame(self.root, bg="#eee", pady=10)
        header.pack(fill='x')
        tk.Label(header, text="My Profile", bg="#eee", font=("Arial", 14)).pack(side='left', padx=10)
        tk.Button(header, text="Back to Dashboard", command=self.show_customer_dashboard).pack(side='right', padx=10)

        # Use a Notebook (Tabs) to organize Profile vs Reviews
        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # === TAB 1: DETAILS & ORDERS ===
        tab_main = tk.Frame(notebook)
        notebook.add(tab_main, text="Details & Orders")

        # 1. Update Details Section
        edit_frame = tk.LabelFrame(tab_main, text="Update Details", padx=10, pady=10)
        edit_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(edit_frame, text="Full Name:").grid(row=0, column=0, sticky='e')
        entry_name = tk.Entry(edit_frame, width=30)
        entry_name.grid(row=0, column=1, padx=5, pady=5)
        entry_name.insert(0, self.session.get('full_name') or "")

        tk.Label(edit_frame, text="Email:").grid(row=1, column=0, sticky='e')
        entry_email = tk.Entry(edit_frame, width=30)
        entry_email.grid(row=1, column=1, padx=5, pady=5)
        entry_email.insert(0, self.session.get('email') or "")

        def update_info():
            new_name = entry_name.get()
            new_email = entry_email.get()
            def run_update():
                try:
                    resp = requests.post(f"{API_URL}/user/update", json={
                        "user_id": self.session['user_id'], "full_name": new_name, "email": new_email
                    })
                    if resp.status_code == 200:
                        self.session['full_name'] = new_name
                        self.session['email'] = new_email
                        self.root.after(0, lambda: messagebox.showinfo("Success", "Profile Updated"))
                    else:
                        self.root.after(0, lambda: messagebox.showerror("Error", resp.text))
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            threading.Thread(target=run_update).start()

        tk.Button(edit_frame, text="Save Changes", command=update_info, bg="#4CAF50", fg="white").grid(row=2, column=1, pady=10, sticky='w')

        # 2. Order History Section
        hist_frame = tk.LabelFrame(tab_main, text="Order History", padx=10, pady=10)
        hist_frame.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ('Order ID', 'Date', 'Total Amount', 'Status')
        hist_tree = ttk.Treeview(hist_frame, columns=cols, show='headings')
        for col in cols: hist_tree.heading(col, text=col)
        hist_tree.pack(fill='both', expand=True)

        def load_history():
            try:
                user_id = self.session.get('user_id')
                resp = requests.get(f"{API_URL}/user/orders/{user_id}")
                if resp.status_code == 200:
                    orders = resp.json()
                    self.root.after(0, lambda: update_hist_tree(orders))
            except: pass

        def update_hist_tree(orders):
            for row in hist_tree.get_children(): hist_tree.delete(row)
            if orders:
                for o in orders:
                    hist_tree.insert("", "end", values=(o['id'], o['order_date'], f"${o['total_amount']}", o['payment_status']))

        # === TAB 2: RATINGS & REVIEWS ===
        tab_reviews = tk.Frame(notebook)
        notebook.add(tab_reviews, text="Rate My Books")

        lbl_instr = tk.Label(tab_reviews, text="Select a book from your library to rate/review it.", font=("Arial", 10, "italic"))
        lbl_instr.pack(pady=5)

        # Split view: Left side (List of books), Right side (Review Form)
        paned = tk.PanedWindow(tab_reviews, orient=tk.HORIZONTAL)
        paned.pack(fill='both', expand=True, padx=5, pady=5)

        # Left: List of purchased books
        frame_list = tk.Frame(paned)
        paned.add(frame_list, width=300)
        
        cols_rev = ('Book Title', 'My Rating')
        self.rev_tree = ttk.Treeview(frame_list, columns=cols_rev, show='headings')
        self.rev_tree.heading('Book Title', text='Book Title')
        self.rev_tree.heading('My Rating', text='My Rating')
        self.rev_tree.column('My Rating', width=80)
        self.rev_tree.pack(fill='both', expand=True)

        # Right: Edit Form
        frame_edit = tk.Frame(paned, padx=10, pady=10, bg="#f9f9f9")
        paned.add(frame_edit)

        tk.Label(frame_edit, text="Rate this book (0-10):", bg="#f9f9f9").pack(anchor='w')
        self.combo_rating = ttk.Combobox(frame_edit, values=[str(i) for i in range(11)], state="readonly", width=5)
        self.combo_rating.pack(anchor='w', pady=5)

        tk.Label(frame_edit, text="Write a review (Anonymous):", bg="#f9f9f9").pack(anchor='w', pady=(10,0))
        self.txt_review = tk.Text(frame_edit, height=10, width=40)
        self.txt_review.pack(anchor='w', fill='both', expand=True)

        self.btn_save_review = tk.Button(frame_edit, text="Submit Review", bg="#2196F3", fg="white", state="disabled")
        self.btn_save_review.pack(pady=10, fill='x')

        # Hidden var to store selected book id for the review
        self.review_target_book_id = None 

        def on_book_select(event):
            sel = self.rev_tree.focus()
            if not sel: return
            item = self.rev_tree.item(sel)['values']
            # Tree values: Title, Rating, (Hidden ID, Hidden Text) -> We need to store these better
            # Actually, let's store the full data map locally to lookup
            
            # Find the full data object corresponding to selection
            book_title = item[0]
            # We need the ID. Let's retrieve it from the hidden storage or api data
            selected_data = next((x for x in self.my_books_data if x['title'] == book_title), None)
            
            if selected_data:
                self.review_target_book_id = selected_data['book_id']
                
                # Enable button
                self.btn_save_review.config(state="normal", command=submit_review_action)
                
                # Fill Form
                self.combo_rating.set(str(selected_data['rating']) if selected_data['rating'] is not None else "")
                self.txt_review.delete("1.0", tk.END)
                if selected_data['review_text']:
                    self.txt_review.insert("1.0", selected_data['review_text'])
        
        self.rev_tree.bind("<<TreeviewSelect>>", on_book_select)

        def load_reviewable_books():
            try:
                resp = requests.get(f"{API_URL}/reviews/user/{self.session['user_id']}")
                if resp.status_code == 200:
                    self.my_books_data = resp.json() # Store globally to access in click event
                    self.root.after(0, update_rev_tree)
            except: pass

        def update_rev_tree():
            for row in self.rev_tree.get_children(): self.rev_tree.delete(row)
            for b in self.my_books_data:
                rating_display = b['rating'] if b['rating'] is not None else "-"
                self.rev_tree.insert("", "end", values=(b['title'], rating_display))

        def submit_review_action():
            rating = self.combo_rating.get()
            review_text = self.txt_review.get("1.0", tk.END).strip()
            
            if not rating: 
                messagebox.showerror("Error", "Please select a rating (0-10)")
                return

            payload = {
                "user_id": self.session['user_id'],
                "book_id": self.review_target_book_id,
                "rating": int(rating),
                "review_text": review_text
            }
            
            def run_sub():
                try:
                    resp = requests.post(f"{API_URL}/reviews/submit", json=payload)
                    if resp.status_code == 200:
                        self.root.after(0, lambda: [messagebox.showinfo("Success", "Review Saved!"), load_reviewable_books()])
                    else:
                        self.root.after(0, lambda: messagebox.showerror("Error", resp.json().get('error')))
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            threading.Thread(target=run_sub).start()

        # Load data
        threading.Thread(target=load_history).start()
        threading.Thread(target=load_reviewable_books).start()

    def search_books(self):
        query = self.search_entry.get() if hasattr(self, 'search_entry') else ''
        def run():
            try:
                resp = requests.get(f"{API_URL}/books", params={'q': query})
                books = resp.json()
                self.root.after(0, lambda: self.update_book_list(books))
            except: pass
        threading.Thread(target=run).start()

    def update_book_list(self, books):
        for row in self.tree.get_children(): self.tree.delete(row)
        for b in books:
            self.tree.insert("", "end", values=(b['id'], b['title'], b['author'], b['stock'], b['price_buy'], b['price_rent']))

    def add_to_cart(self, type_):
        sel = self.tree.focus()
        if not sel: return
        vals = self.tree.item(sel)['values']
        if vals[3] < 1:
            messagebox.showerror("Error", "Out of Stock")
            return
        price = vals[4] if type_ == 'buy' else vals[5]
        self.cart.append({"book_id": vals[0], "title": vals[1], "type": type_, "price": price})
        messagebox.showinfo("Cart", "Added to cart")
        self.show_customer_dashboard()

    def show_cart(self):
        top = tk.Toplevel(self.root)
        top.geometry("400x400")
        listbox = tk.Listbox(top)
        listbox.pack(expand=True, fill='both')
        total = 0
        for item in self.cart:
            listbox.insert("end", f"{item['title']} ({item['type']}) - ${item['price']}")
            total += float(item['price'])
        
        tk.Label(top, text=f"Total: ${total:.2f}").pack()
        
        def checkout():
            try:
                resp = requests.post(f"{API_URL}/order", json={"user_id": self.session['user_id'], "items": self.cart})
                if resp.status_code == 201:
                    messagebox.showinfo("Success", "Order Placed. Check your email for your receipt!")
                    self.cart = []
                    top.destroy()
                    self.show_customer_dashboard()
                else:
                    messagebox.showerror("Error", resp.json().get('error'))
            except Exception as e:
                messagebox.showerror("Error", str(e))
        tk.Button(top, text="Checkout", command=checkout).pack()

    # --- MANAGER DASHBOARD ---
    def show_manager_dashboard(self):
        self.clear_screen()
        header = tk.Frame(self.root, bg="#333", pady=10)
        header.pack(fill='x')
        tk.Label(header, text="MANAGER DASHBOARD", bg="#333", fg="white").pack(side='left', padx=10)
        tk.Button(header, text="Logout", command=self.show_login_screen).pack(side='right', padx=10)

        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # TAB 1: Inventory
        self.tab_inv = tk.Frame(notebook)
        notebook.add(self.tab_inv, text="Inventory")
        self.build_inventory_tab()

        # TAB 2: Returns / Rentals
        self.tab_ret = tk.Frame(notebook)
        notebook.add(self.tab_ret, text="Rentals & Returns")
        self.build_returns_tab()
        
        # TAB 3: Orders / Payment
        self.tab_orders = tk.Frame(notebook)
        notebook.add(self.tab_orders, text="All Orders")
        self.build_orders_tab()
        
    def build_inventory_tab(self):
        # Top controls
        tk.Button(self.tab_inv, text="Refresh List", command=self.refresh_mgr_books).pack(pady=5)
        
        # Treeview
        cols = ('ID', 'Title', 'Author', 'Stock', 'Buy $', 'Rent $')
        self.mgr_tree = ttk.Treeview(self.tab_inv, columns=cols, show='headings', height=8)
        for col in cols: self.mgr_tree.heading(col, text=col)
        self.mgr_tree.pack(fill='both', expand=True)
        
        # Bind click event to populate form
        self.mgr_tree.bind("<<TreeviewSelect>>", self.on_mgr_book_select) 

        # Add/Edit Book Form
        frm = tk.LabelFrame(self.tab_inv, text="Book Details (Select book to Edit, or fill to Add)")
        frm.pack(fill='x', padx=10, pady=10)
        
        # Use 'self.' so we can access these from other functions
        tk.Label(frm, text="Title:").grid(row=0, column=0)
        self.e_title = tk.Entry(frm); self.e_title.grid(row=0, column=1)
        
        tk.Label(frm, text="Author:").grid(row=0, column=2)
        self.e_auth = tk.Entry(frm); self.e_auth.grid(row=0, column=3)
        
        tk.Label(frm, text="Stock:").grid(row=1, column=0)
        self.e_stock = tk.Entry(frm); self.e_stock.grid(row=1, column=1)
        
        tk.Label(frm, text="Buy Price:").grid(row=1, column=2)
        self.e_buy = tk.Entry(frm); self.e_buy.grid(row=1, column=3)
        
        tk.Label(frm, text="Rent Price:").grid(row=1, column=4)
        self.e_rent = tk.Entry(frm); self.e_rent.grid(row=1, column=5)
        
        # ID Holder (Hidden)
        self.selected_book_id = None

        # Buttons
        btn_frame = tk.Frame(frm)
        btn_frame.grid(row=2, columnspan=6, pady=10)

        tk.Button(btn_frame, text="Add New Book", command=self.add_book_req, bg="green", fg="white").pack(side='left', padx=5)
        tk.Button(btn_frame, text="Update Selected Book", command=self.update_book_req, bg="blue", fg="white").pack(side='left', padx=5)
        tk.Button(btn_frame, text="Clear Fields", command=self.clear_form, bg="gray", fg="white").pack(side='left', padx=5)
        
        self.refresh_mgr_books()

    def on_mgr_book_select(self, event):
        # Auto-populate fields when a row is clicked
        sel = self.mgr_tree.focus()
        if not sel: return
        vals = self.mgr_tree.item(sel)['values']
        
        # Store ID
        self.selected_book_id = vals[0]

        # Clear and Insert
        self.clear_form(clear_id=False) # Don't clear ID
        self.e_title.insert(0, vals[1])
        self.e_auth.insert(0, vals[2])
        self.e_stock.insert(0, vals[3])
        self.e_buy.insert(0, vals[4])
        self.e_rent.insert(0, vals[5])

    def clear_form(self, clear_id=True):
        if clear_id:
            self.selected_book_id = None
            # Deselect tree
            if self.mgr_tree.selection():
                self.mgr_tree.selection_remove(self.mgr_tree.selection())

        entries = [self.e_title, self.e_auth, self.e_stock, self.e_buy, self.e_rent]
        for e in entries:
            e.delete(0, tk.END)

    def add_book_req(self):
        data = {
            "title": self.e_title.get(), "author": self.e_auth.get(),
            "stock": self.e_stock.get(), "price_buy": self.e_buy.get(), "price_rent": self.e_rent.get()
        }
        def run():
            requests.post(f"{API_URL}/books", json=data)
            self.root.after(0, lambda: [self.refresh_mgr_books(), self.clear_form()])
        threading.Thread(target=run).start()

    def update_book_req(self):
        if not self.selected_book_id:
            messagebox.showerror("Error", "No book selected")
            return

        data = {
            "id": self.selected_book_id,
            "title": self.e_title.get(), 
            "author": self.e_auth.get(),
            "stock": self.e_stock.get(), 
            "price_buy": self.e_buy.get(), 
            "price_rent": self.e_rent.get()
        }
        def run():
            requests.post(f"{API_URL}/books/update", json=data)
            self.root.after(0, lambda: [self.refresh_mgr_books(), self.clear_form()])
        threading.Thread(target=run).start()
        
    def add_book_req():
        data = {
            "title": e_title.get(), "author": e_auth.get(),
            "stock": e_stock.get(), "price_buy": e_buy.get(), "price_rent": e_rent.get()
        }
    def run():
        requests.post(f"{API_URL}/books", json=data)
        self.root.after(0, self.refresh_mgr_books)
        # Clear fields (must run on main thread)
        self.root.after(0, lambda: [
            e_title.delete(0, tk.END), e_auth.delete(0, tk.END),
            e_stock.delete(0, tk.END), e_buy.delete(0, tk.END),
            e_rent.delete(0, tk.END)
        ])
        threading.Thread(target=run).start()

        tk.Button(frm, text="Add Book", command=add_book_req, bg="green", fg="white").grid(row=2, columnspan=6, pady=5)
        self.refresh_mgr_books()

    def refresh_mgr_books(self):
        def run():
            try:
                resp = requests.get(f"{API_URL}/books")
                books = resp.json()
                self.root.after(0, lambda: self.update_mgr_tree(books))
            except: pass
        threading.Thread(target=run).start()

    def update_mgr_tree(self, books):
        for row in self.mgr_tree.get_children(): self.mgr_tree.delete(row)
        for b in books:
            self.mgr_tree.insert("", "end", values=(b['id'], b['title'], b['author'], b['stock'], b['price_buy'], b['price_rent']))

    def build_returns_tab(self):
        tk.Button(self.tab_ret, text="Refresh Rentals", command=self.load_rentals).pack(pady=5)
        cols = ('ID', 'Title', 'User', 'Price', 'Date')
        self.ret_tree = ttk.Treeview(self.tab_ret, columns=cols, show='headings')
        for col in cols: self.ret_tree.heading(col, text=col)
        self.ret_tree.pack(fill='both', expand=True)
        tk.Button(self.tab_ret, text="Mark Selected as RETURNED", command=self.process_return, bg="orange").pack(pady=10)
        self.load_rentals()

    def load_rentals(self):
        def run():
            try:
                resp = requests.get(f"{API_URL}/admin/rentals")
                items = resp.json()
                self.root.after(0, lambda: self.update_ret_tree(items))
            except: pass
        threading.Thread(target=run).start()

    def update_ret_tree(self, items):
        for row in self.ret_tree.get_children(): self.ret_tree.delete(row)
        for i in items:
            self.ret_tree.insert("", "end", values=(i['id'], i['title'], i['username'], i['price'], i['order_date']))
            
    def process_return(self):
        sel = self.ret_tree.focus()
        if not sel: return
        order_item_id = self.ret_tree.item(sel)['values'][0]
        def run():
            requests.post(f"{API_URL}/admin/return", json={"order_item_id": order_item_id})
            self.root.after(0, lambda: [messagebox.showinfo("Success", "Book returned"), self.load_rentals()])
        threading.Thread(target=run).start()

    def build_orders_tab(self):
        tk.Button(self.tab_orders, text="Refresh Orders", command=self.load_orders).pack(pady=5)
        
        # Cols: ID, User, Email, Total, Status, Date
        cols = ('ID', 'User', 'Email', 'Total', 'Status', 'Date')
        self.ord_tree = ttk.Treeview(self.tab_orders, columns=cols, show='headings')
        for col in cols: self.ord_tree.heading(col, text=col)
        self.ord_tree.column('ID', width=40)
        self.ord_tree.pack(fill='both', expand=True)
        
        tk.Button(self.tab_orders, text="Mark Selected as PAID", command=self.mark_order_paid, bg="#4CAF50", fg="white").pack(pady=10)
        self.load_orders()

    def load_orders(self):
        def run():
            try:
                resp = requests.get(f"{API_URL}/admin/orders")
                orders = resp.json()
                self.root.after(0, lambda: self.update_orders_tree(orders))
            except: pass
        threading.Thread(target=run).start()
    
    def update_orders_tree(self, orders):
        for row in self.ord_tree.get_children(): self.ord_tree.delete(row)
        for o in orders:
            self.ord_tree.insert("", "end", values=(o['id'], o['username'], o['email'], f"${o['total_amount']}", o['payment_status'], o['order_date']))

    def mark_order_paid(self):
        sel = self.ord_tree.focus()
        if not sel: return
        order_id = self.ord_tree.item(sel)['values'][0]
        def run():
            requests.post(f"{API_URL}/admin/payment", json={"order_id": order_id, "status": "Paid"})
            self.root.after(0, lambda: [messagebox.showinfo("Success", "Order marked as Paid"), self.load_orders()])
        threading.Thread(target=run).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = BookstoreApp(root)
    root.mainloop()