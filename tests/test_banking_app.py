import os

import pytest

from banking_app import BankingSystem, ValidationError


@pytest.fixture
def system(tmp_path):
    return BankingSystem(data_dir=str(tmp_path))


def test_add_customer_generates_account_and_masked_ssn(system):
    customer = system.add_customer(
        first_name="Alice",
        last_name="Johnson",
        dob="05/15/1990",
        address="123 Main St",
        ssn="123456789",
        initial_amount=2500.00,
    )

    assert customer["first_name"] == "Alice"
    assert customer["dob"] == "05/15/1990"
    assert customer["ssn"] == "***-**-6789"
    assert len(customer["checking_account"]["account_number"]) == 6
    assert customer["checking_account"]["balance"] == 2500.00


def test_validation_errors_for_invalid_customer_inputs(system):
    with pytest.raises(ValidationError):
        system.add_customer(
            first_name="",
            last_name="Doe",
            dob="01/01/1990",
            address="123 Main St",
            ssn="123456789",
            initial_amount=100,
        )

    with pytest.raises(ValidationError):
        system.add_customer(
            first_name="Jane",
            last_name="Doe",
            dob="01/01/1990",
            address="123 Main St",
            ssn="123",
            initial_amount=-10,
        )


def test_search_customer_by_name_and_account(system):
    system.add_customer(
        first_name="Bob",
        last_name="Smith",
        dob="11/02/1988",
        address="9 River Rd",
        ssn="987654321",
        initial_amount=500.00,
    )

    result = system.search_customer("Bob", "Smith")
    assert result is not None
    assert result["last_name"] == "Smith"

    account_number = next(iter(system.customers.values()))["checking_account"]["account_number"]
    found = system.search_customer_by_account(account_number)
    assert found is not None
    assert found["checking_account"]["account_number"] == account_number


def test_transaction_history_and_deposit(system):
    customer = system.add_customer(
        first_name="Carol",
        last_name="Lee",
        dob="03/20/1975",
        address="77 Park Ave",
        ssn="111223333",
        initial_amount=1000.00,
    )

    account_number = customer["checking_account"]["account_number"]
    customer = system.deposit_to_account(account_number, 250.75, "Checking")
    assert customer["checking_account"]["balance"] == 1250.75
    assert customer["checking_account"]["transactions"][-1]["type"] == "deposit"
    assert customer["checking_account"]["transactions"][-1]["amount"] == 250.75


def test_customer_not_found_returns_none(system):
    assert system.search_customer("Missing", "User") is None
    assert system.search_customer_by_account("000000") is None


def test_delete_customer_removes_and_persists_customer(system):
    first_customer = system.add_customer(
        first_name="Dana",
        last_name="Brown",
        dob="07/10/1992",
        address="12 Oak Street",
        ssn="222334444",
        initial_amount=75.00,
    )
    second_customer = system.add_customer(
        first_name="Evan",
        last_name="Brown",
        dob="08/11/1993",
        address="13 Oak Street",
        ssn="333445555",
        initial_amount=80.00,
    )

    deleted = system.delete_customer(first_customer["customer_id"])

    assert deleted["first_name"] == "Dana"
    replacement = system.add_customer(
        first_name="Fran",
        last_name="Brown",
        dob="09/12/1994",
        address="14 Oak Street",
        ssn="444556666",
        initial_amount=85.00,
    )
    assert replacement["customer_id"] > second_customer["customer_id"]
    reloaded = type(system)(data_dir=str(system.data_dir))
    assert len(reloaded.list_customers()) == 2
    assert system.delete_customer(first_customer["customer_id"]) is None
