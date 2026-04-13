import tkinter as tk
from tkinter import ttk, messagebox

# ==========================================
# MÀN HÌNH 1: ĐĂNG NHẬP (Login Window)
# ==========================================
class LoginWindow(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg="#f0f4f8") # Màu nền xám nhạt hiện đại

        # Khung chứa nội dung (Căn giữa)
        frame = tk.Frame(self, bg="white", padx=40, pady=40)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="ĐẠI LÝ VÉ MÁY BAY", font=("Arial", 16, "bold"), bg="white", fg="#1a365d").pack(pady=(0, 20))

        # Nhập liệu
        tk.Label(frame, text="Tên đăng nhập:", bg="white", anchor="w").pack(fill="x")
        self.entry_user = ttk.Entry(frame, font=("Arial", 12))
        self.entry_user.pack(fill="x", pady=(0, 15), ipady=5)

        tk.Label(frame, text="Mật khẩu:", bg="white", anchor="w").pack(fill="x")
        self.entry_pass = ttk.Entry(frame, font=("Arial", 12), show="*")
        self.entry_pass.pack(fill="x", pady=(0, 20), ipady=5)

        # Nút bấm
        ttk.Button(frame, text="Đăng nhập", command=self.check_login).pack(fill="x", ipady=5, pady=5)
        
        # Nút Face ID (Điểm nhấn đồ án)
        face_btn = tk.Button(frame, text="Đăng nhập bằng Face ID 📷", bg="#3182ce", fg="white", font=("Arial", 10, "bold"), relief="flat")
        face_btn.pack(fill="x", ipady=5, pady=5)

    def check_login(self):
        # Demo Tuần 2: Bấm là vào luôn, Tuần 3 sẽ nối Database sau
        self.controller.show_frame("DashboardWindow")


# ==========================================
# MÀN HÌNH 2 & 3: DASHBOARD & BÁN VÉ
# ==========================================
class DashboardWindow(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- Sidebar (Menu bên trái) ---
        sidebar = tk.Frame(self, bg="#2d3748", width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False) # Cố định chiều rộng

        tk.Label(sidebar, text="MENU QUẢN LÝ", font=("Arial", 12, "bold"), bg="#2d3748", fg="white").pack(pady=20)
        
        # Nút điều hướng chuyển Tab
        ttk.Button(sidebar, text="Trang chủ (Chuyến bay)", command=lambda: self.notebook.select(0)).pack(fill="x", padx=10, pady=5, ipady=5)
        ttk.Button(sidebar, text="Nghiệp vụ Bán vé", command=lambda: self.notebook.select(1)).pack(fill="x", padx=10, pady=5, ipady=5)
        ttk.Button(sidebar, text="Đăng xuất", command=lambda: self.controller.show_frame("LoginWindow")).pack(side="bottom", fill="x", padx=10, pady=20, ipady=5)

        # --- Main Content (Khu vực chính giữa dùng thẻ Tab - Notebook) ---
        main_content = tk.Frame(self, bg="white")
        main_content.pack(side="right", fill="both", expand=True)

        self.notebook = ttk.Notebook(main_content)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tạo các Tab
        self.tab_home = tk.Frame(self.notebook, bg="white")
        self.tab_booking = tk.Frame(self.notebook, bg="white")
        
        self.notebook.add(self.tab_home, text="Danh sách chuyến bay")
        self.notebook.add(self.tab_booking, text="Bán vé & Đặt chỗ")

        self.build_home_tab()
        self.build_booking_tab()

    def build_home_tab(self):
        tk.Label(self.tab_home, text="DANH SÁCH CHUYẾN BAY TRONG NGÀY", font=("Arial", 14, "bold"), bg="white").pack(pady=10)
        
        # Bảng dữ liệu (Treeview)
        columns = ("macb", "di", "den", "gio", "ghe")
        tree = ttk.Treeview(self.tab_home, columns=columns, show="headings", height=15)
        tree.heading("macb", text="Mã CB")
        tree.heading("di", text="Sân bay đi")
        tree.heading("den", text="Sân bay đến")
        tree.heading("gio", text="Giờ bay")
        tree.heading("ghe", text="Số ghế trống")
        
        # Dữ liệu Demo
        tree.insert("", "end", values=("VN213", "Hà Nội (HAN)", "TP.HCM (SGN)", "08:00 20/04/2026", "45"))
        tree.insert("", "end", values=("VJ122", "Đà Nẵng (DAD)", "Hà Nội (HAN)", "10:30 20/04/2026", "12"))
        tree.pack(fill="both", expand=True, padx=20, pady=10)

    def build_booking_tab(self):
        tk.Label(self.tab_booking, text="THÔNG TIN ĐẶT VÉ", font=("Arial", 14, "bold"), bg="white").pack(pady=10)
        
        # Form nhập liệu chia 2 cột dùng Frame
        form_frame = tk.Frame(self.tab_booking, bg="white")
        form_frame.pack(fill="x", padx=20)

        # Cột trái: Tìm kiếm
        left_col = tk.Frame(form_frame, bg="white")
        left_col.pack(side="left", fill="both", expand=True, padx=10)
        tk.Label(left_col, text="Chọn chuyến bay:", bg="white").pack(anchor="w")
        ttk.Combobox(left_col, values=["VN213 - HAN đi SGN", "VJ122 - DAD đi HAN"], font=("Arial", 12)).pack(fill="x", pady=5)
        tk.Label(left_col, text="Hạng vé:", bg="white").pack(anchor="w", pady=(10,0))
        ttk.Combobox(left_col, values=["Phổ thông", "Thương gia"], font=("Arial", 12)).pack(fill="x", pady=5)

        # Cột phải: Thông tin khách & Voucher
        right_col = tk.Frame(form_frame, bg="white")
        right_col.pack(side="right", fill="both", expand=True, padx=10)
        tk.Label(right_col, text="Họ tên hành khách:", bg="white").pack(anchor="w")
        ttk.Entry(right_col, font=("Arial", 12)).pack(fill="x", pady=5)
        tk.Label(right_col, text="CCCD / Passport:", bg="white").pack(anchor="w", pady=(10,0))
        ttk.Entry(right_col, font=("Arial", 12)).pack(fill="x", pady=5)
        
        # Khu vực Voucher
        tk.Label(right_col, text="Mã Voucher giảm giá:", bg="white", fg="red").pack(anchor="w", pady=(10,0))
        voucher_frame = tk.Frame(right_col, bg="white")
        voucher_frame.pack(fill="x", pady=5)
        ttk.Entry(voucher_frame, font=("Arial", 12)).pack(side="left", fill="x", expand=True)
        ttk.Button(voucher_frame, text="Áp dụng").pack(side="right", padx=(5,0))

        # Nút xác nhận to ở dưới cùng
        tk.Button(self.tab_booking, text="XÁC NHẬN XUẤT VÉ", bg="#48bb78", fg="white", font=("Arial", 12, "bold"), relief="flat").pack(pady=30, ipady=10, ipadx=20)


# ==========================================
# TRỤC ĐIỀU KHIỂN CHÍNH (Main Controller)
# ==========================================
class FlightApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Phần mềm Quản lý Đại lý Vé Máy bay")
        self.geometry("1000x650")
        self.center_window(1000, 650)

        # Khung chứa các màn hình đè lên nhau
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (LoginWindow, DashboardWindow):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LoginWindow")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise() # Đẩy giao diện được chọn lên trên cùng

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width/2) - (width/2))
        y = int((screen_height/2) - (height/2))
        self.geometry(f"{width}x{height}+{x}+{y}")

# Chạy ứng dụng
if __name__ == "__main__":
    app = FlightApp()
    app.mainloop()