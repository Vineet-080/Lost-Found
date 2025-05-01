import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import sqlite3
import os

# Database setup
USER_DB = "users.db"
ITEM_DB = "lost_and_found.db"

def init_db():
    conn = sqlite3.connect(ITEM_DB)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT,
                        description TEXT,
                        location TEXT,
                        time TEXT,
                        contact TEXT,
                        image TEXT)''')
    conn.commit()
    conn.close()

def init_user_db():
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT)''')
    conn.commit()
    conn.close()

def register_user(username, password):
    try:
        conn = sqlite3.connect(USER_DB)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_user(username, password):
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def insert_item(category, description, location, time, contact, image):
    conn = sqlite3.connect(ITEM_DB)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO items (category, description, location, time, contact, image) VALUES (?, ?, ?, ?, ?, ?)", 
                   (category, description, location, time, contact, image))
    conn.commit()
    conn.close()

def fetch_items(category):
    conn = sqlite3.connect(ITEM_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT description, location, time, contact, image FROM items WHERE category=?", (category,))
    items = cursor.fetchall()
    conn.close()
    return items

class LostAndFoundApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Lost and Found System")
        self.root.geometry("500x500")
        
        init_user_db()
        init_db()
        self.show_user_selection()
    
    def show_user_selection(self):
        self.clear_screen()
        ttk.Label(self.root, text="Select User Type", font=("Arial", 14)).pack(pady=10)
        ttk.Button(self.root, text="New User", command=self.show_register).pack(pady=5)
        ttk.Button(self.root, text="Existing User", command=self.show_login).pack(pady=5)
    
    def show_register(self):
        self.clear_screen()
        ttk.Label(self.root, text="Register", font=("Arial", 14)).pack(pady=10)
        ttk.Label(self.root, text="Username:").pack()
        self.username_entry = ttk.Entry(self.root)
        self.username_entry.pack()
        ttk.Label(self.root, text="Password:").pack()
        self.password_entry = ttk.Entry(self.root, show="*")
        self.password_entry.pack()
        ttk.Button(self.root, text="Register", command=self.register).pack(pady=10)
    
    def show_login(self):
        self.clear_screen()
        ttk.Label(self.root, text="Login", font=("Arial", 14)).pack(pady=10)
        ttk.Label(self.root, text="Username:").pack()
        self.username_entry = ttk.Entry(self.root)
        self.username_entry.pack()
        ttk.Label(self.root, text="Password:").pack()
        self.password_entry = ttk.Entry(self.root, show="*")
        self.password_entry.pack()
        ttk.Button(self.root, text="Login", command=self.login).pack(pady=10)
    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if register_user(username, password):
            messagebox.showinfo("Success", "Registration successful!")
            self.show_user_selection()
        else:
            messagebox.showerror("Error", "Username already exists.")
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if authenticate_user(username, password):
            messagebox.showinfo("Success", "Login successful!")
            self.show_main_menu()
        else:
            messagebox.showerror("Error", "Invalid credentials.")
    
    def show_main_menu(self):
        self.clear_screen()
        ttk.Button(self.root, text="Report Lost Item", command=lambda: self.item_form("Lost")).pack(pady=10)
        ttk.Button(self.root, text="Report Found Item", command=lambda: self.item_form("Found")).pack(pady=10)
        ttk.Button(self.root, text="View Lost Items", command=lambda: self.view_items("Lost")).pack(pady=10)
        ttk.Button(self.root, text="View Found Items", command=lambda: self.view_items("Found")).pack(pady=10)
    
    def item_form(self, category):
        form = tk.Toplevel(self.root)
        form.title(f"Report {category} Item")
        
        ttk.Label(form, text="Description:").pack()
        description_entry = ttk.Entry(form)
        description_entry.pack()
        
        ttk.Label(form, text="Location:").pack()
        location_entry = ttk.Entry(form)
        location_entry.pack()
        
        ttk.Label(form, text="Time:").pack()
        time_entry = ttk.Entry(form)
        time_entry.pack()
        
        ttk.Label(form, text="Contact:").pack()
        contact_entry = ttk.Entry(form)
        contact_entry.pack()
        
        img_label = ttk.Label(form, text="No Image Selected")
        img_label.pack()
        
        def upload_image():
            filepath = filedialog.askopenfilename(title="Select Image", filetypes=[("Image Files", ".png;.jpg;*.jpeg")])
            if filepath:
                img_label.config(text=filepath)
        
        ttk.Button(form, text="Upload Image", command=upload_image).pack()
        
        ttk.Button(form, text="Submit", command=lambda: self.submit_item(category, description_entry, location_entry, time_entry, contact_entry, img_label, form)).pack()
    
    def submit_item(self, category, description, location, time, contact, img_label, form):
        insert_item(category, description.get(), location.get(), time.get(), contact.get(), img_label.cget("text"))
        messagebox.showinfo("Success", f"{category} item reported successfully!")
        form.destroy()
    
    def view_items(self, category):
        items = fetch_items(category)
        view_window = tk.Toplevel(self.root)
        view_window.title(f"{category} Items")
        if not items:
            tk.Label(view_window, text=f"No {category.lower()} items reported.").pack()
            return
        for item in items:
            description, location, time, contact, image = item
            tk.Label(view_window, text=f"Description: {description}").pack()
            tk.Label(view_window, text=f"Location: {location}").pack()
            tk.Label(view_window, text=f"Time: {time}").pack()
            tk.Label(view_window, text=f"Contact: {contact}").pack()
            if image and os.path.exists(image):
                img = Image.open(image)
                img = img.resize((100, 100), Image.LANCZOS)
                img = ImageTk.PhotoImage(img)
                img_label = tk.Label(view_window, image=img)
                img_label.image = img
                img_label.pack()
    
    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = LostAndFoundApp(root)
    root.mainloop()