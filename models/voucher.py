# models/voucher.py
class Voucher:
    def __init__(self, voucher_id, code, discount_percent, max_discount, usage_limit, used_count, expiry_date):
        self.voucher_id = voucher_id
        self.code = code
        self.discount_percent = discount_percent
        self.max_discount = max_discount
        self.usage_limit = usage_limit
        self.used_count = used_count
        self.expiry_date = expiry_date