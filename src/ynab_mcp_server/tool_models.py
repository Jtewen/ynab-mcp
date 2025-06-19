from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field, conint, model_validator, field_validator


class BudgetIdInput(BaseModel):
    budget_id: Optional[str] = Field(
        None,
        description="The ID of the budget. If not provided, the default budget will be used.",
    )


class ManageFinancialOverviewAction(str, Enum):
    GET = "get"
    UPDATE = "update"
    REFRESH = "refresh"


class ManageFinancialOverviewInput(BudgetIdInput):
    action: ManageFinancialOverviewAction = Field(..., description="The action to perform.")
    section: Optional[str] = Field(None, description="The section to update (e.g., 'goals', 'action_items'). Required for 'update' action.")
    data: Optional[dict] = Field(None, description="The new data for the section. Required for 'update' action.")

    @model_validator(mode='before')
    @classmethod
    def check_fields_for_action(cls, values):
        action = values.get('action')
        if not action:
            raise ValueError("'action' is a required field.")

        if action == 'update':
            if not values.get('section') or not values.get('data'):
                raise ValueError("'section' and 'data' are required for the 'update' action.")
        
        return values


class ManageBudgetedAmountAction(str, Enum):
    ASSIGN = "assign"
    MOVE = "move"


class ManageBudgetedAmountInput(BudgetIdInput):
    action: ManageBudgetedAmountAction = Field(..., description="The action to perform.")
    amount: float = Field(..., description="The amount in milliunits.")
    month: str = Field(..., description="The month to apply the action to (YYYY-MM-DD).")
    from_category_id: Optional[str] = Field(None, description="The ID of the category to move money from. Required for 'move' action.")
    to_category_id: Optional[str] = Field(None, description="The ID of the category to move money to, or the category to assign to.")

    @model_validator(mode='before')
    @classmethod
    def check_fields_for_action(cls, values):
        action = values.get('action')
        if not action:
            raise ValueError("'action' is a required field.")

        if action == 'assign':
            if not values.get('to_category_id'):
                raise ValueError("'to_category_id' is required for the 'assign' action.")
            if values.get('from_category_id'):
                raise ValueError("'from_category_id' should not be provided for the 'assign' action.")
        elif action == 'move':
            if not values.get('from_category_id') or not values.get('to_category_id'):
                raise ValueError("'from_category_id' and 'to_category_id' are required for the 'move' action.")
        
        return values 


class ManagePayeesAction(str, Enum):
    RENAME = "rename"


class ManagePayeesInput(BudgetIdInput):
    action: ManagePayeesAction = Field(..., description="The action to perform.")
    payee_ids: List[str] = Field(..., description="The IDs of the payees to affect.")
    name: Optional[str] = Field(None, description="The new name for the payees. Required for 'rename' action.")

    @model_validator(mode='before')
    @classmethod
    def check_fields_for_action(cls, values):
        action = values.get('action')
        if not action:
            raise ValueError("'action' is a required field.")

        if action == 'rename':
            if not values.get('name'):
                raise ValueError("'name' is required for the 'rename' action.")
        
        return values 


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
    limit: Optional[float] = Field(
        None, description="The maximum number of transactions to return"
    )


class CreateTransactionInput(BudgetIdInput):
    account_id: str = Field(..., description="The ID of the account for the transaction.")
    date: str = Field(..., description="The transaction date in YYYY-MM-DD format.")
    amount: float = Field(..., description="The transaction amount in milliunits.")
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
    since_date: Optional[str] = Field(
        None, description="The starting date for transactions (YYYY-MM-DD)"
    )
    limit: Optional[float] = Field(
        None, description="The maximum number of transactions to return"
    )


class NewTransactionModel(BaseModel):
    account_id: str = Field(..., description="The ID of the account for the transaction.")
    date: str = Field(..., description="The transaction date in YYYY-MM-DD format.")
    amount: float = Field(..., description="The transaction amount in milliunits.")
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
    amount: Optional[float] = Field(None, description="The transaction amount in milliunits.")
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


class BulkManageTransactionsAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class BulkManageTransactionsInput(BudgetIdInput):
    action: BulkManageTransactionsAction = Field(..., description="The action to perform.")
    create_transactions: Optional[List[NewTransactionModel]] = Field(None, description="A list of transactions to create. Required for 'create' action.")
    update_transactions: Optional[List[TransactionUpdate]] = Field(None, description="A list of transactions to update. Required for 'update' action.")
    delete_transaction_ids: Optional[List[str]] = Field(None, description="A list of transaction IDs to delete. Required for 'delete' action.")

    @model_validator(mode='before')
    @classmethod
    def check_fields_for_action(cls, values):
        action = values.get('action')
        if not action:
            raise ValueError("'action' is a required field.")

        if action == 'create':
            if not values.get('create_transactions'):
                raise ValueError("'create_transactions' is required for the 'create' action.")
        elif action == 'update':
            if not values.get('update_transactions'):
                raise ValueError("'update_transactions' is required for the 'update' action.")
        elif action == 'delete':
            if not values.get('delete_transaction_ids'):
                raise ValueError("'delete_transaction_ids' is required for the 'delete' action.")
        
        return values


class BulkCreateTransactionsInput(BudgetIdInput):
    transactions: List[NewTransactionModel] = Field(..., description="A list of transactions to create.")


class UpdateTransactionsInput(BudgetIdInput):
    transactions: List[TransactionUpdate] = Field(
        ..., description="A list of transactions to update."
    )


class DeleteTransactionInput(BudgetIdInput):
    transaction_id: str = Field(..., description="The ID of the transaction to delete.")


class ListTransactionsInput(BudgetIdInput):
    account_id: Optional[str] = Field(None, description="The ID of the account to fetch transactions for.")
    month: Optional[str] = Field(None, description="The month to fetch transactions for (YYYY-MM-DD format).")
    since_date: Optional[str] = Field(
        None, description="The starting date for transactions (YYYY-MM-DD). Only valid if 'account_id' is provided."
    )
    limit: Optional[float] = Field(
        None, description="The maximum number of transactions to return."
    )

    @model_validator(mode='before')
    @classmethod
    def check_exclusive_fields(cls, values):
        if not values.get('account_id') and not values.get('month'):
            raise ValueError('Either "account_id" or "month" must be provided.')
        if values.get('month') and values.get('since_date'):
            raise ValueError('"since_date" is not applicable when "month" is provided.')
        return values


class ScheduledTransaction(BaseModel):
    account_id: str = Field(..., description="The ID of the account for the transaction.")
    date: str = Field(..., description="The transaction date in YYYY-MM-DD format.")
    amount: float = Field(..., description="The transaction amount in milliunits.")
    frequency: str = Field(..., description="The frequency of the scheduled transaction (e.g. 'daily', 'weekly', 'monthly').")
    payee_id: Optional[str] = Field(None, description="The ID of the payee.")
    payee_name: Optional[str] = Field(
        None, description="The name of the payee. If not provided, a new payee will be created."
    )
    category_id: Optional[str] = Field(
        None, description="The ID of the category for the transaction."
    )
    memo: Optional[str] = Field(None, description="A memo for the transaction.")
    flag_color: Optional[str] = Field(
        None, description="The flag color of the transaction.",
    )
    import_id: Optional[str] = Field(
        None, description="A unique import ID for the transaction. Use for idempotency."
    )


class ManageScheduledTransactionAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class ManageScheduledTransactionInput(BudgetIdInput):
    action: ManageScheduledTransactionAction = Field(..., description="The action to perform.")
    transaction_id: Optional[str] = Field(None, description="The ID of the scheduled transaction to update or delete.")
    transaction_data: Optional[ScheduledTransaction] = Field(None, description="The data for the scheduled transaction to create or update.")

    @model_validator(mode='before')
    @classmethod
    def check_fields_for_action(cls, values):
        action = values.get('action')
        if not action:
            raise ValueError("'action' is a required field.")

        transaction_id = values.get('transaction_id')
        transaction_data = values.get('transaction_data')

        if action == 'create':
            if not transaction_data:
                raise ValueError("'transaction_data' is required for the 'create' action.")
            if transaction_id:
                raise ValueError("'transaction_id' should not be provided for the 'create' action.")
        elif action == 'update':
            if not transaction_id or not transaction_data:
                raise ValueError("'transaction_id' and 'transaction_data' are required for the 'update' action.")
        elif action == 'delete':
            if not transaction_id:
                raise ValueError("'transaction_id' is required for the 'delete' action.")
            if transaction_data:
                raise ValueError("'transaction_data' should not be provided for the 'delete' action.")
        
        return values


class CreateScheduledTransactionInput(BudgetIdInput, ScheduledTransaction):
    pass


class UpdateScheduledTransactionInput(BudgetIdInput):
    transaction_id: str = Field(..., description="The ID of the scheduled transaction to update.")
    transaction: ScheduledTransaction


class DeleteScheduledTransactionInput(BudgetIdInput):
    transaction_id: str = Field(..., description="The ID of the scheduled transaction to delete.")


class EntityType(str, Enum):
    ACCOUNT = "account"
    CATEGORY = "category"
    PAYEE = "payee"


class LookupEntityByIdInput(BudgetIdInput):
    entity_type: EntityType = Field(..., description="The type of entity to look up.")
    entity_id: str = Field(..., description="The ID of the entity to look up.")


class GetMonthInfoInput(BudgetIdInput):
    month: Optional[str] = Field(
        None, description="The month to retrieve in YYYY-MM-DD format. If not provided, all months will be listed."
    )


class LookupPayeeLocationsInput(BudgetIdInput):
    location_id: Optional[str] = Field(
        None, description="The ID of a specific payee location to retrieve."
    )
    payee_id: Optional[str] = Field(
        None, description="The ID of a payee to list locations for."
    )