import tkinter as tk
from tkinter import messagebox, ttk
import requests
import threading

API_URL = "http://127.0.0.1:5000"

class BookstoreApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Online Bookstore Desktop Client")
        self.root.geometry("800x600")
        
        self.session = {} # Stores user_id, role, token
        self.cart = []    # Stores items added to cart
        
        self.show_login_screen()

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # --- AUTHENTICATION SCREENS --- 

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
        tk.Button(frame, text="Register", command=self.show_register_screen).pack(pady=5, fill='x')

    def show_register_screen(self):
        self.clear_screen()
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(expand=True)
        
        tk.Label(frame, text="Create Account", font=("Arial", 16)).pack(pady=10)
        
        tk.Label(frame, text="Username").pack()
        self.reg_user = tk.Entry(frame)
        self.reg_user.pack()
        
        tk.Label(frame, text="Email").pack()
        self.reg_email = tk.Entry(frame)
        self.reg_email.pack()
        
        tk.Label(frame, text="Password").pack()
        self.reg_pass = tk.Entry(frame, show="*")
        self.reg_pass.pack()
        
        tk.Label(frame, text="Role (customer/manager)").pack()
        self.reg_role = tk.Entry(frame)
        self.reg_role.insert(0, "customer")
        self.reg_role.pack()
        
        tk.Button(frame, text="Sign Up", command=self.handle_register, bg="#2196F3", fg="white").pack(pady=10, fill='x')
        tk.Button(frame, text="Back to Login", command=self.show_login_screen).pack(pady=5, fill='x')

    # --- LOGIC HANDLERS ---

    def handle_login(self):
        username = self.entry_user.get()
        password = self.entry_pass.get()
        
        def run():
            try:
                resp = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
                if resp.status_code == 200:
                    data = resp.json()
                    self.session = data
                    self.root.after(0, self.route_dashboard)
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Invalid Login"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Connection Error", str(e)))
        
        threading.Thread(target=run).start()

    def handle_register(self):
        data = {
            "username": self.reg_user.get(),
            "password": self.reg_pass.get(),
            "email": self.reg_email.get(),
            "role": self.reg_role.get()
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

    def route_dashboard(self):
        if self.session.get('role') == 'manager':
            self.show_manager_dashboard()
        else:
            self.show_customer_dashboard()

    # --- CUSTOMER DASHBOARD ---

    def show_customer_dashboard(self):
        self.clear_screen()
        
        # Header
        header = tk.Frame(self.root, bg="#eee", pady=10)
        header.pack(fill='x')
        tk.Label(header, text=f"Welcome, {self.session.get('user_id')}", bg="#eee").pack(side='left', padx=10)
        tk.Button(header, text="Logout", command=self.show_login_screen).pack(side='right', padx=10)
        tk.Button(header, text=f"View Cart ({len(self.cart)})", command=self.show_cart).pack(side='right', padx=10)

        # Search Area
        search_frame = tk.Frame(self.root, pady=10)
        search_frame.pack()
        tk.Label(search_frame, text="Search Book:").pack(side='left')
        self.search_entry = tk.Entry(search_frame, width=30)
        self.search_entry.pack(side='left', padx=5)
        tk.Button(search_frame, text="Search", command=self.search_books).pack(side='left')

        # Results Area (Treeview)
        cols = ('ID', 'Title', 'Author', 'Buy Price', 'Rent Price')
        self.tree = ttk.Treeview(self.root, columns=cols, show='headings')
        for col in cols:
            self.tree.heading(col, text=col)
        self.tree.pack(expand=True, fill='both', padx=20, pady=10)
        
        # Action Buttons
        btn_frame = tk.Frame(self.root, pady=10)
        btn_frame.pack()
        tk.Button(btn_frame, text="Add to Cart (Buy)", command=lambda: self.add_to_cart('buy')).pack(side='left', padx=10)
        tk.Button(btn_frame, text="Add to Cart (Rent)", command=lambda: self.add_to_cart('rent')).pack(side='left', padx=10)

    def search_books(self):
        query = self.search_entry.get()
        def run():
            try:
                resp = requests.get(f"{API_URL}/books", params={'q': query})
                books = resp.json()
                self.root.after(0, lambda: self.update_book_list(books))
            except:
                pass
        threading.Thread(target=run).start()

    def update_book_list(self, books):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for b in books:
            self.tree.insert("", "end", values=(b['id'], b['title'], b['author'], b['price_buy'], b['price_rent']))

    def add_to_cart(self, type_):
        selected = self.tree.focus()
        if not selected:
            return
        vals = self.tree.item(selected)['values']
        # vals: id, title, author, buy_price, rent_price
        price = vals[3] if type_ == 'buy' else vals[4]
        
        item = {
            "book_id": vals[0],
            "title": vals[1],
            "type": type_,
            "price": price
        }
        self.cart.append(item)
        messagebox.showinfo("Cart", f"Added {vals[1]} ({type_}) to cart.")
        self.show_customer_dashboard() # Refresh to update cart count

    def show_cart(self):
        # simple cart window
        top = tk.Toplevel(self.root)
        top.title("Your Cart")
        top.geometry("400x400")
        
        listbox = tk.Listbox(top)
        listbox.pack(expand=True, fill='both', padx=10, pady=10)
        
        total = 0
        for item in self.cart:
            listbox.insert("end", f"{item['title']} - {item['type'].upper()} - ${item['price']}")
            total += float(item['price'])
            
        tk.Label(top, text=f"Total: ${total:.2f}", font=("Arial", 12, "bold")).pack(pady=10)
        
        def checkout():
            payload = {
                "user_id": self.session['user_id'],
                "items": self.cart
            }
            try:
                resp = requests.post(f"{API_URL}/order", json=payload)
                if resp.status_code == 201:
                    messagebox.showinfo("Success", "Order Placed! Bill sent to email.")
                    self.cart = []
                    top.destroy()
                    self.show_customer_dashboard()
                else:
                    messagebox.showerror("Error", "Failed to place order")
            except Exception as e:
                messagebox.showerror("Error", str(e))
                
        tk.Button(top, text="Checkout / Place Order", command=checkout, bg="#4CAF50", fg="white").pack(pady=10)

    # --- MANAGER DASHBOARD ---

    def show_manager_dashboard(self):
        self.clear_screen()
        
        header = tk.Frame(self.root, bg="#333", pady=10)
        header.pack(fill='x')
        tk.Label(header, text="MANAGER DASHBOARD", bg="#333", fg="white").pack(side='left', padx=10)
        tk.Button(header, text="Logout", command=self.show_login_screen).pack(side='right', padx=10)
        tk.Button(header, text="Refresh Orders", command=self.load_orders).pack(side='right', padx=10)
        
        cols = ('ID', 'User', 'Total', 'Status', 'Date')
        self.order_tree = ttk.Treeview(self.root, columns=cols, show='headings')
        for col in cols:
            self.order_tree.heading(col, text=col)
        self.order_tree.pack(expand=True, fill='both', padx=20, pady=10)
        
        btn_frame = tk.Frame(self.root, pady=10)
        btn_frame.pack()
        tk.Button(btn_frame, text="Mark as Paid", command=self.mark_paid).pack()
        
        # Load orders initially
        self.load_orders()

    def load_orders(self):
        def run():
            try:
                resp = requests.get(f"{API_URL}/admin/orders")
                orders = resp.json()
                self.root.after(0, lambda: self.update_order_list(orders))
            except:
                pass
        threading.Thread(target=run).start()
        
    def update_order_list(self, orders):
        for row in self.order_tree.get_children():
            self.order_tree.delete(row)
        for o in orders:
            self.order_tree.insert("", "end", values=(o['id'], o['username'], o['total_amount'], o['payment_status'], o['order_date']))

    def mark_paid(self):
        selected = self.order_tree.focus()
        if not selected: return
        
        order_id = self.order_tree.item(selected)['values'][0]
        
        def run():
            try:
                requests.post(f"{API_URL}/admin/payment", json={"order_id": order_id, "status": "Paid"})
                self.root.after(0, lambda: [messagebox.showinfo("Info", "Status Updated"), self.load_orders()])
            except:
                pass
        threading.Thread(target=run).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = BookstoreApp(root)
    root.mainloop()