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
    payees_api,
    scheduled_transactions_api,
    transactions_api,
)
from ynab.models import (
    PatchMonthCategoryWrapper,
    PatchPayeeWrapper,
    PatchTransactionsWrapper,
    SaveMonthCategory,
    SavePayee,
    SaveTransactionWithIdOrImportId,
)

from .settings import settings


class NotesManager:
    def __init__(self):
        # Use XDG data directory or fall back to /tmp
        self.data_dir = Path(os.environ.get('XDG_DATA_HOME', '/tmp/ynab-mcp'))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.financial_overview_path = self.data_dir / "financial_overview.json"
        self._ensure_overview_exists()

    def _ensure_overview_exists(self):
        """Ensure the overview file exists with initial structure"""
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
        self.notes = NotesManager()

    async def _run_sync(self, func, *args, **kwargs):
        """Run a synchronous function in a separate thread."""
        return await asyncio.to_thread(func, *args, **kwargs)

    async def get_budgets(self) -> list[ynab.BudgetSummary]:
        response = await self._run_sync(self._budgets_api.get_budgets)
        return response.data.budgets

    async def get_default_budget(self) -> ynab.BudgetSummary:
        """Gets the first available budget, assuming only one is used."""
        budgets = await self.get_budgets()
        if not budgets:
            raise ValueError("No budgets found in YNAB account.")
        return budgets[0]

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

    async def get_payees(self, budget_id: str) -> list[ynab.Payee]:
        response = await self._run_sync(self._payees_api.get_payees, budget_id)
        return response.data.payees

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


ynab_client = YNABClient(token=settings.ynab_api_token)
