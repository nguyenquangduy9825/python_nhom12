# models/user.py

class User:
    def __init__(self, user_id, username, role, customer_id=None):
        """
        Khởi tạo đối tượng User đại diện cho người dùng đang đăng nhập.
        - user_id: ID của tài khoản trong bảng Users
        - username: Tên đăng nhập
        - role: Quyền hạn (ADMIN, STAFF, USER, GUEST)
        - customer_id: ID liên kết với bảng Customers (để truy xuất lịch sử vé)
        """
        self.user_id = user_id
        self.username = username
        self.role = role
        self.customer_id = customer_id

    def __str__(self):
        return f"<User: {self.username} - Role: {self.role} - CustomerID: {self.customer_id}>"