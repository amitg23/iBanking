import argparse
import json

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ModuleNotFoundError:  # pragma: no cover - GUI-only dependency
    tk = None
    messagebox = None
    ttk = None

from core.banking_core import BankingSystem, ValidationError


class BankingApp:
    def __init__(self, root):
        if tk is None or ttk is None:
            raise RuntimeError("Tkinter is required to run the GUI application.")
        self.root = root
        self.system = BankingSystem(data_dir="data")
        self.root.title("iBanking")
        self.root.geometry("1100x700")
        self.root.minsize(980, 600)
        self.root.configure(bg="#edf3ff")

        self._apply_theme()
        self._build_ui()
        self._refresh_customer_list()

    def _apply_theme(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background="#edf3ff")
        style.configure("TNotebook", background="#edf3ff", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(16, 8), background="#dfeaf7", foreground="#334155", borderwidth=0, focusthickness=0, font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#f8fbff"), ("active", "#e5edf8")], foreground=[("selected", "#0f172a")])

        style.configure("Card.TLabelframe", background="#ffffff", relief="flat", borderwidth=1)
        style.configure("Card.TLabelframe.Label", background="#ffffff", foreground="#0f172a", font=("Segoe UI", 10, "bold"))
        style.configure("Panel.TFrame", background="#ffffff")

        style.configure("TEntry", fieldbackground="#ffffff", background="#ffffff", foreground="#0f172a", borderwidth=1)
        style.map("TEntry", fieldbackground=[("focus", "#ffffff"), ("!disabled", "#ffffff")], foreground=[("disabled", "#64748b")])

        style.configure("Accent.TButton", background="#1d72e8", foreground="#ffffff", padding=(12, 7), font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#185fce"), ("pressed", "#1451b8")], foreground=[("active", "#ffffff")])

        style.configure("Secondary.TButton", background="#e2e8f0", foreground="#0f172a", padding=(10, 6), font=("Segoe UI", 10, "bold"))
        style.map("Secondary.TButton", background=[("active", "#cbd5e1")])

        style.configure("TCombobox", fieldbackground="#ffffff", background="#ffffff", foreground="#0f172a", borderwidth=1, padding=(8, 4), arrowsize=14)
        style.map("TCombobox", fieldbackground=[("readonly", "#ffffff"), ("focus", "#ffffff")], selectbackground=[("readonly", "#dbeafe")], selectforeground=[("readonly", "#0f172a")])

        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", foreground="#0f172a", rowheight=28, font=("Segoe UI", 10))
        style.map("Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", "#0f172a")])
        style.configure("Treeview.Heading", background="#e2e8f0", foreground="#0f172a", font=("Segoe UI", 10, "bold"))
        style.map("Treeview.Heading", background=[("active", "#cbd5e1")])

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=16)
        main.pack(fill="both", expand=True)

        header = ttk.Frame(main, style="Panel.TFrame")
        header.pack(fill="x", pady=(0, 12))
        header.columnconfigure(0, weight=1)

        tk.Label(header, text="iBanking", bg="#ffffff", fg="#0f172a", font=("Segoe UI", 22, "bold")).grid(row=0, column=0, sticky="w", padx=(18, 0), pady=(18, 4))
        tk.Label(header, text="Customer portal", bg="#ffffff", fg="#64748b", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", padx=(18, 0), pady=(0, 18))

        self.tabs = ttk.Notebook(main)
        self.tabs.pack(fill="both", expand=True)

        create_tab = ttk.Frame(self.tabs, padding=12, style="TFrame")
        search_tab = ttk.Frame(self.tabs, padding=12, style="TFrame")
        self.tabs.add(create_tab, text="Create Customer")
        self.tabs.add(search_tab, text="Search Customer")

        customer_form = ttk.LabelFrame(create_tab, text="Customer Information", padding=16, style="Card.TLabelframe")
        customer_form.pack(anchor="nw", fill="x")

        self.fields = {}
        field_specs = [
            ("First Name", "first_name"),
            ("Last Name", "last_name"),
            ("Date of Birth (MM/DD/YYYY)", "dob"),
            ("Address", "address"),
            ("SSN (9 digits)", "ssn"),
            ("Initial Deposit", "initial_amount"),
        ]

        for label_text, key in field_specs:
            row = ttk.Frame(customer_form, style="TFrame")
            row.pack(fill="x", pady=6)
            tk.Label(row, text=label_text, width=22, anchor="w", bg="#ffffff", fg="#334155", font=("Segoe UI", 10, "bold")).pack(side="left")
            entry = tk.Entry(
                row,
                width=28,
                bg="#ffffff",
                fg="#0f172a",
                insertbackground="#0f172a",
                highlightthickness=0,
                highlightbackground="#ffffff",
                highlightcolor="#1d72e8",
                relief="solid",
                bd=1,
                borderwidth=1,
                font=("Segoe UI", 10),
            )
            entry.pack(side="left", padx=(8, 0))
            self.fields[key] = entry

        add_customer_btn = tk.Button(
            customer_form,
            text="Add Customer",
            command=self._add_customer,
            bg="#1d72e8",
            fg="#070606",
            activebackground="#3D3F41",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=18,
            pady=7,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            highlightthickness=0,
        )
        add_customer_btn.bind("<ButtonPress>", lambda event, b=add_customer_btn: self._animate_button_press(b, "#185fce"))
        add_customer_btn.bind("<ButtonRelease>", lambda event, b=add_customer_btn: self._animate_button_press(b, "#1d72e8"))
        add_customer_btn.pack(anchor="w", pady=(12, 0))

        search_panel = ttk.LabelFrame(search_tab, text="Search", padding=16, style="Card.TLabelframe")
        search_panel.pack(fill="x", pady=(0, 12))

        self.search_first = tk.Entry(search_panel, width=28, bg="#ffffff", fg="#0f172a", insertbackground="#0f172a", highlightthickness=0, highlightbackground="#ffffff", highlightcolor="#1d72e8", relief="solid", bd=1, borderwidth=1, font=("Segoe UI", 10))
        self.search_last = tk.Entry(search_panel, width=28, bg="#ffffff", fg="#0f172a", insertbackground="#0f172a", highlightthickness=0, highlightbackground="#ffffff", highlightcolor="#1d72e8", relief="solid", bd=1, borderwidth=1, font=("Segoe UI", 10))
        self.search_account = tk.Entry(search_panel, width=28, bg="#ffffff", fg="#0f172a", insertbackground="#0f172a", highlightthickness=0, highlightbackground="#ffffff", highlightcolor="#1d72e8", relief="solid", bd=1, borderwidth=1, font=("Segoe UI", 10))

        search_fields = [
            ("First Name", self.search_first),
            ("Last Name", self.search_last),
            ("Account Number", self.search_account),
        ]
        search_panel.columnconfigure(1, weight=1)
        for row_index, (label_text, widget) in enumerate(search_fields):
            tk.Label(search_panel, text=label_text, width=16, anchor="w", bg="#ffffff", fg="#334155", font=("Segoe UI", 10, "bold")).grid(
                row=row_index, column=0, sticky="w", pady=6
            )
            widget.grid(row=row_index, column=1, sticky="w", padx=(8, 0), pady=6)

        search_btn = tk.Button(
            search_panel,
            text="Search",
            command=self._search_customer,
            bg="#1d72e8",
            fg="#070606",
            activebackground="#3D3F41",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=16,
            pady=6,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            highlightthickness=0,
        )
        search_btn.bind("<ButtonPress>", lambda event, b=search_btn: self._animate_button_press(b, "#3D3F41"))
        search_btn.bind("<ButtonRelease>", lambda event, b=search_btn: self._animate_button_press(b, "#1d72e8"))
        search_btn.grid(row=len(search_fields), column=1, sticky="w", pady=(8, 0))

        content = ttk.Frame(search_tab, style="TFrame")
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)
        content.rowconfigure(1, weight=1)

        results_box = ttk.LabelFrame(content, text="Customers", padding=10, style="Card.TLabelframe")
        results_box.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 8))

        self.customer_tree = ttk.Treeview(results_box, columns=("first", "last", "checking", "savings"), show="headings", height=12)
        self.customer_tree.heading("first", text="First Name")
        self.customer_tree.heading("last", text="Last Name")
        self.customer_tree.heading("checking", text="Checking")
        self.customer_tree.heading("savings", text="Savings")
        self.customer_tree.pack(fill="both", expand=True)
        self.customer_tree.bind("<<TreeviewSelect>>", self._select_customer)

        delete_btn = tk.Button(
            results_box,
            text="Delete Selected Customer",
            command=self._delete_selected_customer,
            bg="#1d72e8",
            fg="#070606",
            activebackground="#3D3F41",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            highlightthickness=0,
        )
        delete_btn.bind("<ButtonPress>", lambda event, b=delete_btn: self._animate_button_press(b, "#3D3F41"))
        delete_btn.bind("<ButtonRelease>", lambda event, b=delete_btn: self._animate_button_press(b, "#1d72e8"))
        delete_btn.pack(anchor="w", pady=(10, 0))

        detail_box = ttk.LabelFrame(content, text="Customer Details", padding=12, style="Card.TLabelframe")
        detail_box.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))

        self.customer_details = tk.Text(detail_box, height=12, state="disabled", bg="#f8fafc", fg="#0f172a", relief="flat", padx=10, pady=8, wrap="word", font=("Segoe UI", 10))
        self.customer_details.pack(fill="both", expand=True)

        account_panel = ttk.LabelFrame(content, text="Deposit", padding=14, style="Card.TLabelframe")
        account_panel.grid(row=1, column=1, sticky="new", padx=(8, 0), pady=(0, 0))

        deposit_row = ttk.Frame(account_panel, style="TFrame")
        deposit_row.pack(fill="x")
        tk.Label(deposit_row, text="Amount", width=12, anchor="w", bg="#ffffff", fg="#334155", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.deposit_amount = tk.Entry(deposit_row, width=18, bg="#ffffff", fg="#0f172a", insertbackground="#0f172a", highlightthickness=0, highlightbackground="#ffffff", highlightcolor="#1d72e8", relief="solid", bd=1, borderwidth=1, font=("Segoe UI", 10))
        self.deposit_amount.pack(side="left", padx=(8, 12))

        self.account_choice = ttk.Combobox(account_panel, values=["Checking", "Savings"], state="readonly", width=15, justify="center")
        self.account_choice.pack(anchor="w", pady=(10, 0))
        self.account_choice.current(0)

        deposit_btn = tk.Button(
            account_panel,
            text="Deposit",
            command=self._deposit_to_selected_account,
            bg="#1d72e8",
            fg="#070606",
            activebackground="#3D3F41",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=18,
            pady=7,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            highlightthickness=0,
        )
        deposit_btn.bind("<ButtonPress>", lambda event, b=deposit_btn: self._animate_button_press(b, "#3D3F41"))
        deposit_btn.bind("<ButtonRelease>", lambda event, b=deposit_btn: self._animate_button_press(b, "#1d72e8"))        
        deposit_btn.pack(anchor="w", pady=(12, 0))

    def _animate_button_press(self, button, color):
        button.configure(bg=color)
        button.configure(activebackground=color)

    def _clear_placeholder(self, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)

    def _restore_placeholder(self, entry, placeholder):
        if not entry.get().strip():
            entry.delete(0, tk.END)
            entry.insert(0, placeholder)

    def _add_customer(self):
        payload = {
            "first_name": self.fields["first_name"].get().strip(),
            "last_name": self.fields["last_name"].get().strip(),
            "dob": self.fields["dob"].get().strip(),
            "address": self.fields["address"].get().strip(),
            "ssn": self.fields["ssn"].get().strip(),
            "initial_amount": self.fields["initial_amount"].get().strip(),
        }

        try:
            customer = self.system.add_customer(**payload)
            self._refresh_customer_list()
            self._show_customer_details(customer)
            self._select_row_by_customer(customer)
            self.tabs.select(1)
            messagebox.showinfo("Success", f"Customer {customer['first_name']} {customer['last_name']} added successfully.")
            for entry in self.fields.values():
                entry.delete(0, tk.END)
        except ValidationError as exc:
            messagebox.showerror("Validation Error", str(exc))

    def _search_customer(self):
        first = self.search_first.get().strip()
        last = self.search_last.get().strip()
        account = self.search_account.get().strip()

        if first == "First Name":
            first = ""
        if last == "Last Name":
            last = ""
        if account == "Account Number":
            account = ""

        if account:
            customer = self.system.search_customer_by_account(account)
        else:
            customer = self.system.search_customer(first, last)

        if customer is None:
            messagebox.showerror("Not Found", "Customer or account not found.")
            self._clear_customer_details()
            return

        self._show_customer_details(customer)
        self._refresh_customer_list()
        self._select_row_by_customer(customer)

    def _refresh_customer_list(self):
        for row in self.customer_tree.get_children():
            self.customer_tree.delete(row)

        for customer in self.system.list_customers():
            self.customer_tree.insert(
                "",
                "end",
                values=(
                    customer["first_name"],
                    customer["last_name"],
                    customer["checking_account"]["account_number"],
                    customer["savings_account"]["account_number"],
                ),
                iid=str(customer["customer_id"]),
            )

    def _select_row_by_customer(self, customer):
        for row_id in self.customer_tree.get_children():
            if row_id == str(customer["customer_id"]):
                self.customer_tree.selection_set(row_id)
                self.customer_tree.focus(row_id)
                return

    def _select_customer(self, event):
        selected = self.customer_tree.selection()
        if not selected:
            return
        customer_id = selected[0]
        customer = self.system.customers.get(customer_id)
        if customer:
            self._show_customer_details(customer)

    def _show_customer_details(self, customer):
        self.customer_details.config(state="normal")
        self.customer_details.delete("1.0", tk.END)
        details = [
            f"Name: {customer['first_name']} {customer['last_name']}",
            f"DOB: {customer['dob']}",
            f"Address: {customer['address']}",
            f"SSN: {customer['ssn']}",
            "",
            "Checking Account",
            f"  Account Number: {customer['checking_account']['account_number']}",
            f"  Balance: ${customer['checking_account']['balance']:.2f}",
            "",
            "Savings Account",
            f"  Account Number: {customer['savings_account']['account_number']}",
            f"  Balance: ${customer['savings_account']['balance']:.2f}",
            "",
            "Transactions",
        ]

        for account_name in ("checking_account", "savings_account"):
            for transaction in customer[account_name]["transactions"]:
                details.append(
                    f"  - {account_name.replace('_account','').title()}: "
                    f"{transaction['type']} ${transaction['amount']:.2f} at {transaction['timestamp']}"
                )

        self.customer_details.insert("1.0", "\n".join(details))
        self.customer_details.config(state="disabled")

    def _clear_customer_details(self):
        self.customer_details.config(state="normal")
        self.customer_details.delete("1.0", tk.END)
        self.customer_details.config(state="disabled")

    def _delete_selected_customer(self):
        selected = self.customer_tree.selection()
        if not selected:
            messagebox.showerror("No customer selected", "Please select a customer first.")
            return

        customer = self.system.customers.get(selected[0])
        if not customer:
            return

        customer_name = f"{customer['first_name']} {customer['last_name']}"
        confirmed = messagebox.askyesno(
            "Delete customer",
            f"Delete {customer_name} and all of their accounts?",
        )
        if not confirmed:
            return

        self.system.delete_customer(selected[0])
        self._refresh_customer_list()
        self._clear_customer_details()
        messagebox.showinfo("Customer deleted", f"Customer {customer_name} was deleted.")

    def _deposit_to_selected_account(self):
        selected = self.customer_tree.selection()
        if not selected:
            messagebox.showerror("No customer selected", "Please select a customer first.")
            return

        customer_id = selected[0]
        customer = self.system.customers.get(customer_id)
        if not customer:
            return

        amount_value = self.deposit_amount.get().strip()
        account_name = self.account_choice.get().strip()
        account_type = account_name.lower()

        try:
            selected_account = customer["checking_account"] if account_name == "Checking" else customer["savings_account"]
            updated_customer = self.system.deposit_to_account(selected_account["account_number"], amount_value, account_type)
            self._show_customer_details(updated_customer)
            self._refresh_customer_list()
            self.deposit_amount.delete(0, tk.END)
            messagebox.showinfo("Success", f"Deposit of ${float(amount_value):.2f} applied to {account_name} account.")
        except ValidationError as exc:
            messagebox.showerror("Deposit error", str(exc))


def _account_lookup(account_number, output_json=False):
    system = BankingSystem(data_dir="data")
    customer = system.search_customer_by_account(account_number)
    if customer is None:
        print(f"Account not found: {account_number}")
        return 1

    if output_json:
        print(json.dumps(customer, indent=2))
    else:
        print(f"Customer: {customer['first_name']} {customer['last_name']}")
        for account_name in ("checking_account", "savings_account"):
            account = customer[account_name]
            print(f"{account['account_type']} Account: {account['account_number']}")
            print(f"{account['account_type']} Balance: ${account['balance']:.2f}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="iBanking desktop application")
    parser.add_argument("--account", help="Look up an account without opening the GUI")
    parser.add_argument("--json", action="store_true", dest="output_json", help="Output account lookup as JSON")
    args = parser.parse_args()

    if args.account:
        raise SystemExit(_account_lookup(args.account, args.output_json))

    if tk is None:
        raise RuntimeError("Tkinter is required to run the GUI application.")
    root = tk.Tk()
    BankingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
