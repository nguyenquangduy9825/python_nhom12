# models/customer.py
class Customer:
    def __init__(self, customer_id, full_name, email, phone, id_card):
        self.customer_id = customer_id
        self.full_name = full_name
        self.email = email
        self.phone = phone
        self.id_card = id_card