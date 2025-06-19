from typing import List, Optional

from pydantic import BaseModel, Field


class BudgetIdInput(BaseModel):
    budget_id: Optional[str] = Field(
        None,
        description="The ID of the budget. If not provided, the default budget will be used.",
    )


class ListAccountsInput(BudgetIdInput):
    pass


class ListCategoriesInput(BudgetIdInput):
    pass


class ListPayeesInput(BudgetIdInput):
    pass


class ListMonthlyTransactionsInput(BudgetIdInput):
    month: str = Field(
        ..., description="The month to get transactions for (YYYY-MM-DD)"
    )
    limit: Optional[int] = Field(
        None, description="The maximum number of transactions to return"
    )


class CreateTransactionInput(BudgetIdInput):
    account_id: str = Field(..., description="The ID of the account for the transaction.")
    date: str = Field(..., description="The transaction date in YYYY-MM-DD format.")
    amount: int = Field(..., description="The transaction amount in milliunits.")
    payee_id: Optional[str] = Field(None, description="The ID of the payee.")
    payee_name: Optional[str] = Field(
        None, description="The name of the payee. If not provided, a new payee will be created."
    )
    category_id: Optional[str] = Field(
        None, description="The ID of the category for the transaction."
    )
    memo: Optional[str] = Field(None, description="A memo for the transaction.")
    cleared: Optional[str] = Field(
        None, description="The cleared status of the transaction.",
    )
    approved: bool = Field(False, description="Whether or not the transaction is approved.")
    flag_color: Optional[str] = Field(
        None, description="The flag color of the transaction.",
    )
    import_id: Optional[str] = Field(
        None, description="A unique import ID for the transaction. Use for idempotency."
    )


class TransactionUpdate(BaseModel):
    id: str = Field(..., description="The ID of the transaction to update.")
    account_id: Optional[str] = Field(None, description="The ID of the account.")
    date: Optional[str] = Field(None, description="The transaction date in YYYY-MM-DD format.")
    amount: Optional[int] = Field(None, description="The transaction amount in milliunits.")
    category_id: Optional[str] = Field(
        None, description="The ID of the category for the transaction."
    )
    payee_id: Optional[str] = Field(None, description="The ID of the payee.")
    memo: Optional[str] = Field(None, description="A memo for the transaction.")
    cleared: Optional[str] = Field(
        None, description="The cleared status of the transaction.",
    )
    approved: Optional[bool] = Field(None, description="Whether or not the transaction is approved.")
    flag_color: Optional[str] = Field(
        None, description="The flag color of the transaction.",
    )


class UpdateTransactionsInput(BudgetIdInput):
    transactions: List[TransactionUpdate] = Field(
        ..., description="A list of transactions to update."
    )


class DeleteTransactionInput(BudgetIdInput):
    transaction_id: str = Field(..., description="The ID of the transaction to delete.")


class ListTransactionsInput(BudgetIdInput):
    account_id: str = Field(..., description="The ID of the account")
    since_date: Optional[str] = Field(
        None, description="The starting date for transactions (YYYY-MM-DD)"
    )
    limit: Optional[int] = Field(
        None, description="The maximum number of transactions to return"
    ) 