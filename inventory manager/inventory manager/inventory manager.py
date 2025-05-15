import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
import csv
import tempfile
import platform
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

USER_FILE = "users.json"


def load_users():
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w") as f:
            json.dump({}, f)
    with open(USER_FILE, "r") as f:
        return json.load(f)


def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)


def load_inventory(username):
    inventory_file = f"{username}_inventory.json"
    if not os.path.exists(inventory_file):
        return []
    with open(inventory_file, "r") as f:
        return json.load(f)


def save_inventory(username, inventory):
    inventory_file = f"{username}_inventory.json"
    with open(inventory_file, "w") as f:
        json.dump(inventory, f)


def show_login_screen():
    def login():
        users = load_users()
        username = username_entry.get()
        password = password_entry.get()
        if users.get(username) == password:
            login_window.destroy()
            show_inventory_screen(username)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    def open_register_window():
        register_window = tk.Toplevel(login_window)
        register_window.title("Register")
        register_window.geometry("400x300")
        register_window.configure(bg="#f0f4f8")

        tk.Label(register_window, text="Username", bg="#f0f4f8", font=("Segoe UI", 14)).pack(pady=10)
        register_username_entry = tk.Entry(register_window, font=("Segoe UI", 14), width=30, bd=2, relief="groove")
        register_username_entry.pack(pady=5)

        tk.Label(register_window, text="Password", bg="#f0f4f8", font=("Segoe UI", 14)).pack(pady=10)
        register_password_entry = tk.Entry(register_window, show="*", font=("Segoe UI", 14), width=30, bd=2, relief="groove")
        register_password_entry.pack(pady=5)

        def register_user():
            users = load_users()
            username = register_username_entry.get()
            password = register_password_entry.get()
            if username in users:
                messagebox.showerror("Register Failed", "Username already exists.")
            elif not username or not password:
                messagebox.showerror("Register Failed", "Fields cannot be empty.")
            else:
                users[username] = password
                save_users(users)
                messagebox.showinfo("Registration Successful", "You can now log in.")
                register_window.destroy()

        tk.Button(register_window, text="Register", command=register_user, font=("Segoe UI", 14), bg="#27ae60",
                  fg="white", relief="flat", width=20, height=2).pack(pady=15)

    login_window = tk.Tk()
    login_window.title("Inventory System Login")
    login_window.configure(bg="#f0f4f8")
    width = 500
    height = 400

    # Center window
    screen_width = login_window.winfo_screenwidth()
    screen_height = login_window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    login_window.geometry(f"{width}x{height}+{x}+{y}")

    font = ("Segoe UI", 14)

    tk.Label(login_window, text="Username", bg="#f0f4f8", font=font).pack(pady=10)
    username_entry = tk.Entry(login_window, font=font, width=30, bd=2, relief="groove")
    username_entry.pack(pady=5)

    tk.Label(login_window, text="Password", bg="#f0f4f8", font=font).pack(pady=10)
    password_entry = tk.Entry(login_window, show="*", font=font, width=30, bd=2, relief="groove")
    password_entry.pack(pady=5)

    tk.Button(login_window, text="Login", command=login, font=font, bg="#4a90e2", fg="white",
              relief="flat", width=20, height=2).pack(pady=15)
    tk.Button(login_window, text="Register", command=open_register_window, font=font, bg="#7ed6df", fg="black",
              relief="flat", width=20, height=2).pack()

    login_window.mainloop()


def show_inventory_screen(username):
    inventory = load_inventory(username)

    def add_item():
        name = name_entry.get().strip()
        qty = qty_entry.get().strip()
        price = price_entry.get().strip()

        if not name or not qty.isdigit() or not price.replace('.', '', 1).isdigit():
            messagebox.showerror("Invalid Input", "Please enter valid item details.")
            return

        name = name.title()

        # Check if item already exists, add quantity if yes
        for item in inventory:
            if item["name"] == name:
                item["quantity"] += int(qty)
                item["price"] = float(price)  # update price if changed
                break
        else:
            inventory.append({
                "name": name,
                "quantity": int(qty),
                "price": float(price)
            })
        update_inventory_view()
        name_entry.delete(0, tk.END)
        qty_entry.delete(0, tk.END)
        price_entry.delete(0, tk.END)
        save_inventory(username, inventory)

    def on_barcode_enter(event):
        code = barcode_entry.get().strip()

        # Simulated barcode-to-product mapping
        barcode_db = {
            "123456": ("Apple", 10.0),
            "789012": ("Banana", 5.0),
            "345678": ("Orange Juice", 50.0)
        }

        if code in barcode_db:
            name, price = barcode_db[code]
            name_entry.delete(0, tk.END)
            name_entry.insert(0, name)
            qty_entry.delete(0, tk.END)
            qty_entry.insert(0, "1")
            price_entry.delete(0, tk.END)
            price_entry.insert(0, str(price))
            barcode_entry.delete(0, tk.END)
            add_item()
        else:
            messagebox.showerror("Not Found", f"No product found for barcode: {code}")
            barcode_entry.delete(0, tk.END)

    def remove_item():
        selected = tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select an item to remove.")
            return
        index = tree.index(selected)
        inventory.pop(index)
        update_inventory_view()
        save_inventory(username, inventory)

    def update_inventory_view():
        for row in tree.get_children():
            tree.delete(row)
        for item in inventory:
            tree.insert('', tk.END, values=(item["name"], item["quantity"], f"P{item['price']:.2f}"))
        update_total_cost()

    def update_total_cost():
        total = sum(item['quantity'] * item['price'] for item in inventory)
        total_label.config(text=f"Total Cost: P{total:.2f}")

    def save_to_csv():
        if not inventory:
            messagebox.showinfo("No Data", "No inventory to save.")
            return
        try:
            with open("inventory.csv", "w", newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Name", "Quantity", "Price"])
                for item in inventory:
                    writer.writerow([item["name"], item["quantity"], item["price"]])
            messagebox.showinfo("Success", "Inventory saved to inventory.csv")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

    def print_inventory_pdf():
        if not inventory:
            messagebox.showinfo("No Data", "No inventory to print.")
            return
        try:
            # Create a temp PDF file
            temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_pdf.close()  # Close the file so ReportLab can write to it

            c = canvas.Canvas(temp_pdf.name, pagesize=letter)
            width, height = letter
            c.setFont("Helvetica-Bold", 16)
            c.drawString(72, height - 72, "Inventory List")

            c.setFont("Helvetica", 12)
            y = height - 100
            c.drawString(72, y, f"{'Name':<30} {'Quantity':<10} {'Price':>10}")
            y -= 20
            c.line(72, y, width - 72, y)
            y -= 20

            for item in inventory:
                line = f"{item['name']:<30} {item['quantity']:<10} P{item['price']:>9.2f}"
                c.drawString(72, y, line)
                y -= 20
                if y < 72:  # Check for page overflow
                    c.showPage()
                    c.setFont("Helvetica", 12)
                    y = height - 72

            y -= 20
            total = sum(item['quantity'] * item['price'] for item in inventory)
            c.drawString(72, y, f"Total Cost: P{total:.2f}")

            c.save()

            # Open PDF file (works on Windows, Mac, Linux)
            if platform.system() == "Windows":
                os.startfile(temp_pdf.name)
            elif platform.system() == "Darwin":  # macOS
                os.system(f"open {temp_pdf.name}")
            else:  # Linux
                os.system(f"xdg-open {temp_pdf.name}")

            messagebox.showinfo("Success", f"Inventory PDF generated and opened.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create PDF: {e}")

    def logout():
        root.destroy()
        show_login_screen()

    root = tk.Tk()
    root.title("Inventory Manager")
    root.state('zoomed')
    root.configure(bg="#eaf0f6")

    font = ("Segoe UI", 12)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview", font=font, rowheight=28)
    style.configure("Treeview.Heading", font=("Segoe UI", 13, "bold"), background="#4a90e2", foreground="white")
    style.map("Treeview", background=[('selected', '#dfe6e9')])

    input_frame = tk.Frame(root, bg="#eaf0f6", pady=20)
    input_frame.pack()

    tk.Label(input_frame, text="Scan Barcode:", bg="#eaf0f6", font=font).grid(row=0, column=0, padx=10, pady=10, sticky='e')
    barcode_entry = tk.Entry(input_frame, font=font, width=30)
    barcode_entry.grid(row=0, column=1, padx=10, pady=10)
    barcode_entry.bind("<Return>", on_barcode_enter)
    barcode_entry.focus_set()

    tk.Label(input_frame, text="Item Name:", bg="#eaf0f6", font=font).grid(row=1, column=0, padx=10, pady=10, sticky='e')
    name_entry = tk.Entry(input_frame, font=font, width=30)
    name_entry.grid(row=1, column=1, padx=10, pady=10)

    tk.Label(input_frame, text="Quantity:", bg="#eaf0f6", font=font).grid(row=2, column=0, padx=10, pady=10, sticky='e')
    qty_entry = tk.Entry(input_frame, font=font, width=30)
    qty_entry.grid(row=2, column=1, padx=10, pady=10)

    tk.Label(input_frame, text="Price:", bg="#eaf0f6", font=font).grid(row=3, column=0, padx=10, pady=10, sticky='e')
    price_entry = tk.Entry(input_frame, font=font, width=30)
    price_entry.grid(row=3, column=1, padx=10, pady=10)

    tk.Button(input_frame, text="Add Item", command=add_item, font=font, bg="#27ae60", fg="white", relief="flat",
              width=20, height=2).grid(row=4, column=0, columnspan=2, pady=20)

    table_frame = tk.Frame(root, bg="#eaf0f6")
    table_frame.pack(fill="both", expand=True, padx=40)

    columns = ("Name", "Quantity", "Cost")
    tree = ttk.Treeview(table_frame, columns=columns, show='headings')
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center")
    tree.pack(fill="both", expand=True)

    total_label = tk.Label(root, text="Total Cost: P0.00", bg="#eaf0f6", font=("Segoe UI", 14, "bold"))
    total_label.pack(pady=10)

    button_frame = tk.Frame(root, bg="#eaf0f6", pady=20)
    button_frame.pack()

    remove_btn = tk.Button(button_frame, text="Remove Selected Item", command=remove_item, font=font, bg="#c0392b",
                           fg="white", relief="flat", width=20, height=2)
    remove_btn.grid(row=0, column=0, padx=10)

    save_btn = tk.Button(button_frame, text="Save to CSV", command=save_to_csv, font=font, bg="#2980b9", fg="white",
                         relief="flat", width=20, height=2)
    save_btn.grid(row=0, column=1, padx=10)

    print_btn = tk.Button(button_frame, text="Print Inventory", command=print_inventory_pdf, font=font, bg="#8e44ad",
                          fg="white", relief="flat", width=20, height=2)
    print_btn.grid(row=0, column=2, padx=10)

    logout_btn = tk.Button(button_frame, text="Logout", command=logout, font=font, bg="#7f8c8d", fg="white",
                           relief="flat", width=20, height=2)
    logout_btn.grid(row=0, column=3, padx=10)

    update_inventory_view()

    root.mainloop()


show_login_screen()
