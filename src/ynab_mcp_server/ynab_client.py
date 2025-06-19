import asyncio
import fcntl
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import ynab
from ynab.api import (
    accounts_api,
    budgets_api,
    categories_api,
    months_api,
    payees_api,
    payee_locations_api,
    scheduled_transactions_api,
    transactions_api,
    user_api,
)
from ynab.models import (
    NewTransaction,
    PatchMonthCategoryWrapper,
    PatchPayeeWrapper,
    PatchTransactionsWrapper,
    PostScheduledTransactionWrapper,
    PostTransactionsWrapper,
    PutScheduledTransactionWrapper,
    SaveMonthCategory,
    SavePayee,
    SaveScheduledTransaction,
    SaveTransactionsResponse,
    SaveTransactionWithIdOrImportId,
)

from .settings import settings


class NotesManager:
    def __init__(self):
        # Use XDG data directory or fall back to /tmp
        self.data_dir = Path(os.environ.get('XDG_DATA_HOME', '/tmp/ynab-mcp'))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.financial_overview_path = self.data_dir / "financial_overview.json"
        self.sync_state_path = self.data_dir / "sync_state.json"
        self._ensure_files_exist()

    def _ensure_files_exist(self):
        """Ensure the overview and sync state files exist with initial structure"""
        if not self.financial_overview_path.exists():
            initial_overview = {
                "last_updated": self._get_timestamp(),
                "account_balances": {},
                "monthly_overview": {
                    "fixed_bills": 0,
                    "discretionary_spending": 0,
                    "savings_rate": 0
                },
                "goals": [],
                "action_items": [],
                "spending_patterns": [],
                "recommendations": [],
                "context_notes": []
            }
            self.save_overview(initial_overview)

        if not self.sync_state_path.exists():
            initial_state = {
                "accounts": None,
                "categories": None,
                "payees": None,
                "transactions": None
            }
            self._save_state(initial_state)

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now().isoformat()

    def _with_file_lock(self, file_path: Path, mode: str, callback):
        """Execute callback with a file lock to prevent concurrent access"""
        with open(file_path, mode) as f:
            try:
                # Get exclusive lock
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                result = callback(f)
                return result
            finally:
                # Release lock
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def load_overview(self) -> dict:
        """Load the financial overview data with file locking"""
        if not self.financial_overview_path.exists():
            return {}

        def read_file(f):
            return json.load(f)

        return self._with_file_lock(self.financial_overview_path, 'r', read_file)

    def save_overview(self, data: dict):
        """Save the financial overview data with file locking"""
        # First write to temporary file
        temp_path = self.financial_overview_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(data, f, indent=2)

        # Then atomically move it to the real location
        temp_path.replace(self.financial_overview_path)

    def update_overview_section(self, section: str, data: dict | list):
        """Update a specific section of the overview with proper locking"""
        overview = self.load_overview()
        overview[section] = data
        overview["last_updated"] = self._get_timestamp()
        self.save_overview(overview)

    def _load_state(self) -> dict:
        """Load the sync state data with file locking"""
        if not self.sync_state_path.exists():
            return {}

        def read_file(f):
            return json.load(f)

        return self._with_file_lock(self.sync_state_path, 'r', read_file)

    def _save_state(self, data: dict):
        """Save the sync state data with file locking"""
        temp_path = self.sync_state_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(data, f, indent=2)
        temp_path.replace(self.sync_state_path)

    def get_cursor(self, key: str) -> int | None:
        """Get the cursor for a specific endpoint."""
        state = self._load_state()
        return state.get(key)

    def set_cursor(self, key: str, value: int):
        """Set the cursor for a specific endpoint."""
        state = self._load_state()
        state[key] = value
        self._save_state(state)


class YNABClient:
    def __init__(self, token: str):
        configuration = ynab.Configuration(access_token=token)
        self.api_client = ynab.ApiClient(configuration)
        self._budgets_api = budgets_api.BudgetsApi(self.api_client)
        self._accounts_api = accounts_api.AccountsApi(self.api_client)
        self._categories_api = categories_api.CategoriesApi(self.api_client)
        self._transactions_api = transactions_api.TransactionsApi(self.api_client)
        self._payees_api = payees_api.PayeesApi(self.api_client)
        self._scheduled_transactions_api = (
            scheduled_transactions_api.ScheduledTransactionsApi(self.api_client)
        )
        self._months_api = months_api.MonthsApi(self.api_client)
        self._user_api = user_api.UserApi(self.api_client)
        self._payee_locations_api = payee_locations_api.PayeeLocationsApi(
            self.api_client
        )
        self.notes = NotesManager()

    async def _run_sync(self, func, *args, **kwargs):
        """Run a synchronous function in a separate thread."""
        return await asyncio.to_thread(func, *args, **kwargs)

    async def get_user(self) -> ynab.User:
        response = await self._run_sync(self._user_api.get_user)
        return response.data.user

    async def get_budgets(self) -> list[ynab.BudgetSummary]:
        response = await self._run_sync(self._budgets_api.get_budgets)
        return response.data.budgets

    async def get_account_by_id(self, budget_id: str, account_id: str) -> ynab.Account:
        response = await self._run_sync(
            self._accounts_api.get_account_by_id, budget_id, account_id
        )
        return response.data.account

    async def get_accounts(self, budget_id: str) -> list[ynab.Account]:
        response = await self._run_sync(self._accounts_api.get_accounts, budget_id)
        return response.data.accounts

    async def get_transactions(
        self,
        budget_id: str,
        account_id: str,
        since_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[ynab.TransactionDetail]:
        # Note: The SDK's get_transactions_by_account doesn't support a limit.
        # We fetch all and then slice if a limit is provided.
        response = await self._run_sync(
            self._transactions_api.get_transactions_by_account,
            budget_id,
            account_id,
            since_date=since_date,
        )
        transactions = response.data.transactions
        if limit:
            return transactions[:limit]
        return transactions

    async def get_monthly_transactions(
        self,
        budget_id: str,
        month: str,
        limit: Optional[int] = None,
    ) -> list[ynab.TransactionDetail]:
        # The 'since_date' will be the first day of the specified month.
        response = await self._run_sync(
            self._transactions_api.get_transactions_by_month,
            budget_id,
            month,
        )
        transactions = response.data.transactions
        if limit:
            return transactions[:limit]
        return transactions

    async def get_categories(
        self, budget_id: str
    ) -> list[ynab.CategoryGroupWithCategories]:
        response = await self._run_sync(self._categories_api.get_categories, budget_id)
        return response.data.category_groups

    async def get_category_by_id(
        self, budget_id: str, category_id: str
    ) -> ynab.Category:
        response = await self._run_sync(
            self._categories_api.get_category_by_id, budget_id, category_id
        )
        return response.data.category

    async def get_month_category(
        self, budget_id: str, month: str, category_id: str
    ) -> ynab.Category:
        response = await self._run_sync(
            self._categories_api.get_month_category_by_id,
            budget_id,
            month,
            category_id
        )
        return response.data.category

    async def get_scheduled_transactions(
        self, budget_id: str
    ) -> list[ynab.ScheduledTransactionDetail]:
        response = await self._run_sync(
            self._scheduled_transactions_api.get_scheduled_transactions,
            budget_id
        )
        return response.data.scheduled_transactions

    async def create_scheduled_transaction(
        self, budget_id: str, transaction: SaveScheduledTransaction
    ):
        wrapper = PostScheduledTransactionWrapper(scheduled_transaction=transaction)
        return await self._run_sync(
            self._scheduled_transactions_api.create_scheduled_transaction,
            budget_id,
            wrapper,
        )

    async def update_scheduled_transaction(
        self, budget_id: str, transaction_id: str, transaction: SaveScheduledTransaction
    ):
        wrapper = PutScheduledTransactionWrapper(scheduled_transaction=transaction)
        return await self._run_sync(
            self._scheduled_transactions_api.update_scheduled_transaction,
            budget_id,
            transaction_id,
            wrapper,
        )

    async def delete_scheduled_transaction(self, budget_id: str, transaction_id: str):
        return await self._run_sync(
            self._scheduled_transactions_api.delete_scheduled_transaction,
            budget_id,
            transaction_id,
        )

    async def get_payees(self, budget_id: str) -> list[ynab.Payee]:
        response = await self._run_sync(self._payees_api.get_payees, budget_id)
        return response.data.payees

    async def get_payee_by_id(self, budget_id: str, payee_id: str) -> ynab.Payee:
        response = await self._run_sync(
            self._payees_api.get_payee_by_id, budget_id, payee_id
        )
        return response.data.payee

    async def update_payee(self, budget_id: str, payee_id: str, name: str):
        payee = SavePayee(name=name)
        update_wrapper = PatchPayeeWrapper(payee=payee)
        return await self._run_sync(
            self._payees_api.update_payee, budget_id, payee_id, update_wrapper
        )

    async def update_payees(self, budget_id: str, payee_ids: list[str], name: str):
        """Updates multiple payees to the same name."""
        tasks = [self.update_payee(budget_id, payee_id, name) for payee_id in payee_ids]
        await asyncio.gather(*tasks)

    async def assign_budget_amount(
        self, budget_id: str, month: str, category_id: str, amount: int
    ):
        month_category = SaveMonthCategory(budgeted=amount)
        update_wrapper = PatchMonthCategoryWrapper(category=month_category)
        return await self._run_sync(
            self._categories_api.update_month_category,
            budget_id,
            month,
            category_id,
            update_wrapper
        )

    async def update_transactions(
        self, budget_id: str, transactions: list[SaveTransactionWithIdOrImportId]
    ):
        update_wrapper = PatchTransactionsWrapper(transactions=transactions)
        return await self._run_sync(
            self._transactions_api.update_transactions, budget_id, update_wrapper
        )

    async def create_transaction(
        self, budget_id: str, transaction: NewTransaction
    ) -> ynab.TransactionDetail:
        response = await self._run_sync(
            self._transactions_api.create_transaction,
            budget_id,
            PostTransactionsWrapper(transaction=transaction),
        )
        return response.data.transaction

    async def create_transactions(
        self, budget_id: str, transactions: list[NewTransaction]
    ) -> ynab.SaveTransactionsResponseData:
        response = await self._run_sync(
            self._transactions_api.create_transaction,
            budget_id,
            PostTransactionsWrapper(transactions=transactions),
        )
        return response.data

    async def delete_transaction(self, budget_id: str, transaction_id: str):
        return await self._run_sync(
            self._transactions_api.delete_transaction, budget_id, transaction_id
        )

    async def get_budget_months(self, budget_id: str) -> list[ynab.MonthSummary]:
        response = await self._run_sync(self._months_api.get_budget_months, budget_id)
        return response.data.months

    async def get_budget_month(self, budget_id: str, month: str) -> ynab.MonthDetail:
        response = await self._run_sync(
            self._months_api.get_budget_month, budget_id, month
        )
        return response.data.month

    async def get_payee_locations(self, budget_id: str) -> list[ynab.PayeeLocation]:
        response = await self._run_sync(
            self._payee_locations_api.get_payee_locations, budget_id
        )
        return response.data.payee_locations

    async def get_payee_location_by_id(
        self, budget_id: str, payee_location_id: str
    ) -> ynab.PayeeLocation:
        response = await self._run_sync(
            self._payee_locations_api.get_payee_location_by_id,
            budget_id,
            payee_location_id,
        )
        return response.data.payee_location

    async def get_payee_locations_by_payee(
        self, budget_id: str, payee_id: str
    ) -> list[ynab.PayeeLocation]:
        response = await self._run_sync(
            self._payee_locations_api.get_payee_locations_by_payee,
            budget_id,
            payee_id,
        )
        return response.data.payee_locations

    async def get_default_budget(self) -> ynab.BudgetSummary:
        """Gets the first available budget, assuming only one is used."""
        budgets = await self.get_budgets()
        return budgets[0]


ynab_client = YNABClient(token=settings.ynab_api_token)
