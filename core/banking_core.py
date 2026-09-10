import json
import random
import re
from datetime import datetime
from pathlib import Path


class ValidationError(ValueError):
    pass


class BankingSystem:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.customers_file = self.data_dir / "customers.json"
        self.customers = self._load_customers()

    def _load_customers(self):
        if not self.customers_file.exists():
            self.customers_file.write_text("{}", encoding="utf-8")
            return {}

        try:
            with self.customers_file.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            self.customers_file.write_text("{}", encoding="utf-8")
            return {}

    def _save_customers(self):
        with self.customers_file.open("w", encoding="utf-8") as fh:
            json.dump(self.customers, fh, indent=2)

    @staticmethod
    def _now_iso():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def mask_ssn(ssn):
        digits = re.sub(r"\D", "", ssn)
        if len(digits) != 9:
            return ssn
        return f"***-**-{digits[-4:]}"

    @staticmethod
    def _normalize_date(value):
        if value is None:
            return ""

        value = str(value).strip()
        if not value:
            return ""

        for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt).strftime("%m/%d/%Y")
            except ValueError:
                continue
        return ""

    @staticmethod
    def _valid_date(value):
        return bool(BankingSystem._normalize_date(value))

    @staticmethod
    def _generate_account_number(existing_numbers):
        while True:
            number = str(random.randint(100000, 999999))
            if number not in existing_numbers:
                return number

    def _build_account(self, account_type, account_number, opening_balance=0.0):
        return {
            "account_type": account_type,
            "account_number": account_number,
            "balance": round(float(opening_balance), 2),
            "transactions": [],
        }

    def add_customer(self, first_name, last_name, dob, address, ssn, initial_amount):
        first_name = (first_name or "").strip()
        last_name = (last_name or "").strip()
        dob = self._normalize_date(dob)
        address = (address or "").strip()
        ssn = (ssn or "").strip()

        if not first_name or not last_name:
            raise ValidationError("First name and last name are required.")
        if not dob:
            raise ValidationError("Date of birth must be in MM/DD/YYYY format.")
        if len(address) < 3:
            raise ValidationError("Address must be at least 3 characters long.")
        if not re.fullmatch(r"\d{9}", ssn):
            raise ValidationError("SSN must contain exactly 9 numeric digits.")

        try:
            parsed_amount = float(initial_amount)
        except (TypeError, ValueError):
            raise ValidationError("Initial deposit must be a valid number.")

        if parsed_amount < 0:
            raise ValidationError("Initial amount cannot be negative.")

        used_numbers = set()
        for customer in self.customers.values():
            used_numbers.add(customer["checking_account"]["account_number"])
            used_numbers.add(customer["savings_account"]["account_number"])

        checking_number = self._generate_account_number(used_numbers)
        used_numbers.add(checking_number)
        savings_number = self._generate_account_number(used_numbers)

        customer = {
            "customer_id": max((int(customer["customer_id"]) for customer in self.customers.values()), default=0) + 1,
            "first_name": first_name,
            "last_name": last_name,
            "dob": dob,
            "address": address,
            "ssn": self.mask_ssn(ssn),
            "checking_account": self._build_account("Checking", checking_number, parsed_amount),
            "savings_account": self._build_account("Savings", savings_number, 0.0),
        }

        customer["checking_account"]["transactions"].append(
            {
                "type": "deposit",
                "amount": round(parsed_amount, 2),
                "description": "Initial deposit",
                "timestamp": self._now_iso(),
            }
        )

        self.customers[str(customer["customer_id"])] = customer
        self._save_customers()
        return customer

    def search_customer(self, first_name=None, last_name=None):
        if not first_name and not last_name:
            return None

        first_name = (first_name or "").strip().lower()
        last_name = (last_name or "").strip().lower()

        for customer in self.customers.values():
            first_match = not first_name or customer["first_name"].lower() == first_name
            last_match = not last_name or customer["last_name"].lower() == last_name
            if first_match and last_match:
                return customer
        return None

    def search_customer_by_account(self, account_number):
        account_number = (account_number or "").strip()
        if not account_number:
            return None

        for customer in self.customers.values():
            if customer["checking_account"]["account_number"] == account_number:
                return customer
            if customer["savings_account"]["account_number"] == account_number:
                return customer
        return None

    def deposit_to_account(self, account_number, amount, account_type):
        account_number = (account_number or "").strip()
        account_type = (account_type or "").strip().lower()

        try:
            deposit_amount = float(amount)
        except (TypeError, ValueError):
            raise ValidationError("Deposit amount must be a valid number.")

        if deposit_amount <= 0:
            raise ValidationError("Deposit amount must be greater than zero.")

        customer = self.search_customer_by_account(account_number)
        if not customer:
            raise ValidationError("Account not found.")

        target_account = customer["checking_account"] if account_type == "checking" else customer["savings_account"]
        if target_account["account_number"] != account_number:
            if account_type in {"saving", "savings"}:
                target_account = customer["savings_account"]
            elif account_type in {"checking", "check"}:
                target_account = customer["checking_account"]
            else:
                raise ValidationError("Account type must be either Checking or Savings.")

        target_account["balance"] = round(target_account["balance"] + deposit_amount, 2)
        target_account["transactions"].append(
            {
                "type": "deposit",
                "amount": round(deposit_amount, 2),
                "description": f"Deposit to {target_account['account_type']} account",
                "timestamp": self._now_iso(),
            }
        )
        self._save_customers()
        return customer

    def list_customers(self):
        return list(self.customers.values())

    def delete_customer(self, customer_id):
        customer_key = str(customer_id)
        customer = self.customers.pop(customer_key, None)
        if customer is None:
            return None

        self._save_customers()
        return customer
