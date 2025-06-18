import asyncio
import json

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from ynab.models import SaveTransactionWithIdOrImportId

from .ynab_client import ynab_client

server = Server("ynab-mcp")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    """
    return [
        types.Tool(
            name="list-budgets",
            description="List all available YNAB budgets",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="list-accounts",
            description="List all accounts for a given budget",
            inputSchema={
                "type": "object",
                "properties": {
                    "budget_id": {
                        "type": "string",
                        "description": "The ID of the budget. If not provided, the default budget will be used.",
                    }
                },
            },
        ),
        types.Tool(
            name="list-transactions",
            description="List transactions for a given account",
            inputSchema={
                "type": "object",
                "properties": {
                    "budget_id": {
                        "type": "string",
                        "description": "The ID of the budget. If not provided, the default budget will be used.",
                    },
                    "account_id": {
                        "type": "string",
                        "description": "The ID of the account",
                    },
                    "since_date": {
                        "type": "string",
                        "description": "The starting date for transactions (YYYY-MM-DD)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "The maximum number of transactions to return",
                    }
                },
                "required": ["account_id"],
            },
        ),
        types.Tool(
            name="list-monthly-transactions",
            description="List all transactions for a given month, across all accounts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "month": {
                        "type": "string",
                        "description": "The month to get transactions for (YYYY-MM-DD)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "The maximum number of transactions to return",
                    },
                    "budget_id": {
                        "type": "string",
                        "description": "The ID of the budget. If not provided, the default budget will be used.",
                    },
                },
                "required": ["month"],
            },
        ),
        types.Tool(
            name="list-categories",
            description=(
                "List all categories for a given budget, including their budgeted amounts, "
                "activity, and goals."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "budget_id": {
                        "type": "string",
                        "description": (
                            "The ID of the budget. If not provided, the default budget will be used."
                        ),
                    }
                },
            },
        ),
        types.Tool(
            name="list-payees",
            description="List all payees for a given budget",
            inputSchema={
                "type": "object",
                "properties": {
                    "budget_id": {
                        "type": "string",
                        "description": "The ID of the budget. If not provided, the default budget will be used.",
                    }
                },
            },
        ),
        types.Tool(
            name="rename-payees",
            description=(
                "Update multiple payees to a single new name. "
                "This is useful for cleaning up and merging similar payees."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "payee_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "The IDs of the payees to update.",
                    },
                    "name": {
                        "type": "string",
                        "description": "The new name for the payees.",
                    },
                    "budget_id": {
                        "type": "string",
                        "description": "The ID of the budget. If not provided, the default budget will be used.",
                    },
                },
                "required": ["payee_ids", "name"],
            },
        ),
        types.Tool(
            name="move-budget-amount",
            description="Move a specific amount from one category to another in a given month.",
            inputSchema={
                "type": "object",
                "properties": {
                    "budget_id": {
                        "type": "string",
                        "description": "The ID of the budget. If not provided, the default budget will be used.",
                    },
                    "month": {
                        "type": "string",
                        "description": "The month in YYYY-MM-DD format",
                    },
                    "from_category_id": {
                        "type": "string",
                        "description": "The ID of the category to move money from",
                    },
                    "to_category_id": {
                        "type": "string",
                        "description": "The ID of the category to move money to",
                    },
                    "amount": {
                        "type": "integer",
                        "description": "The amount to move in milliunits",
                    },
                },
                "required": ["month", "from_category_id", "to_category_id", "amount"],
            },
        ),
        types.Tool(
            name="assign-budget-amount",
            description="Assign a specific amount to a category for a given month",
            inputSchema={
                "type": "object",
                "properties": {
                    "budget_id": {
                        "type": "string",
                        "description": "The ID of the budget. If not provided, the default budget will be used.",
                    },
                    "month": {
                        "type": "string",
                        "description": "The month in YYYY-MM-DD format",
                    },
                    "category_id": {
                        "type": "string",
                        "description": "The ID of the category",
                    },
                    "amount": {
                        "type": "integer",
                        "description": "The amount to assign in milliunits",
                    },
                },
                "required": ["month", "category_id", "amount"],
            },
        ),
        types.Tool(
            name="update-transactions",
            description="Update one or more transactions with new categories, payees, memos, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "budget_id": {"type": "string", "description": "The ID of the budget. If not provided, the default budget will be used."},
                    "transactions": {
                        "type": "array",
                        "description": "A list of transactions to update.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "category_id": {"type": "string"},
                                "payee_id": {"type": "string"},
                                "memo": {"type": "string"},
                                "cleared": {"type": "string", "enum": ["cleared", "uncleared", "reconciled"]},
                                "approved": {"type": "boolean"},
                                "flag_color": {"type": "string", "enum": ["red", "orange", "yellow", "green", "blue", "purple"]},
                            },
                            "required": ["id"],
                        }
                    },
                },
                "required": ["transactions"],
            },
        ),
        types.Tool(
            name="list-scheduled-transactions",
            description="List all scheduled transactions for a given budget.",
            inputSchema={
                "type": "object",
                "properties": {
                    "budget_id": {
                        "type": "string",
                        "description": "The ID of the budget. If not provided, the default budget will be used.",
                    }
                },
            },
        ),
        types.Tool(
            name="get-financial-overview",
            description=(
                "Get the current financial overview including account balances, goals, and notes"
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="update-financial-overview-section",
            description="Update a specific section of the financial overview",
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "description": (
                            "The section to update (e.g., 'goals', 'action_items', "
                            "'spending_patterns', etc.)"
                        ),
                    },
                    "data": {
                        "type": "object",
                        "description": "The new data for the section",
                    },
                },
                "required": ["section", "data"],
            },
        ),
        types.Tool(
            name="refresh-financial-overview",
            description="Automatically refresh the financial overview with latest data from YNAB",
            inputSchema={
                "type": "object",
                "properties": {
                    "budget_id": {
                        "type": "string",
                        "description": "The ID of the budget. If not provided, the default budget will be used.",
                    }
                },
            },
        ),
    ]


async def _get_budget_id(arguments: dict | None) -> str:
    """Gets the budget_id from arguments or falls back to the default budget."""
    if arguments and "budget_id" in arguments and arguments["budget_id"]:
        return arguments["budget_id"]

    budget = await ynab_client.get_default_budget()
    return budget.id


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    """
    if name == "list-budgets":
        budgets = await ynab_client.get_budgets()

        if not budgets:
            return [types.TextContent(type="text", text="No budgets found.")]

        budget_list = "\n".join(f"- {b.name} (ID: {b.id})" for b in budgets)

        return [
            types.TextContent(
                type="text",
                text=f"Here are your available budgets:\n{budget_list}",
            )
        ]
    elif name == "list-accounts":
        budget_id = await _get_budget_id(arguments)
        accounts = await ynab_client.get_accounts(budget_id=budget_id)

        if not accounts:
            return [types.TextContent(type="text", text="No accounts found for this budget.")]

        account_list = "\n".join(
            f"- {acc.name} (ID: {acc.id}): {acc.balance / 1000:.2f} (Type: {acc.type})"
            for acc in accounts
        )
        return [
            types.TextContent(
                type="text",
                text=f"Here are the accounts for budget {budget_id}:\n{account_list}",
            )
        ]
    elif name == "list-transactions":
        if not arguments or "account_id" not in arguments:
            raise ValueError("Missing account_id argument")
        budget_id = await _get_budget_id(arguments)
        account_id = arguments["account_id"]
        since_date = arguments.get("since_date")
        limit = arguments.get("limit")
        transactions = await ynab_client.get_transactions(
            budget_id=budget_id,
            account_id=account_id,
            since_date=since_date,
            limit=limit,
        )

        if not transactions:
            return [types.TextContent(type="text", text="No transactions found for this account.")]

        transaction_list = "\n".join(
            f"- {t.var_date}: {t.payee_name or 'N/A'} | "
            f"{t.category_name or 'N/A'} | {t.amount / 1000:.2f} (ID: {t.id})"
            for t in transactions
        )
        return [
            types.TextContent(
                type="text",
                text=f"Here are the latest transactions:\n{transaction_list}",
            )
        ]
    elif name == "list-monthly-transactions":
        if not arguments or "month" not in arguments:
            raise ValueError("Missing month argument")
        budget_id = await _get_budget_id(arguments)
        month = arguments["month"]
        limit = arguments.get("limit")
        transactions = await ynab_client.get_monthly_transactions(
            budget_id=budget_id,
            month=month,
            limit=limit,
        )

        if not transactions:
            return [types.TextContent(type="text", text="No transactions found for this month.")]

        monthly_list = "\n".join(
            f"- {t.var_date}: {t.payee_name or 'N/A'} | "
            f"{t.category_name or 'N/A'} | {t.account_name} | "
            f"{t.amount / 1000:.2f} (ID: {t.id})"
            for t in transactions
        )
        return [
            types.TextContent(
                type="text",
                text=f"Here are the transactions for {month}:\n{monthly_list}",
            )
        ]
    elif name == "list-categories":
        budget_id = await _get_budget_id(arguments)
        category_groups = await ynab_client.get_categories(budget_id=budget_id)

        if not category_groups:
            return [types.TextContent(type="text", text="No categories found for this budget.")]

        output = "Here are the available categories and their status for the current month:\n"
        for group in category_groups:
            if not group.hidden and group.categories:
                output += f"\n--- {group.name} ---\n"
                for cat in group.categories:
                    if not cat.hidden:
                        details = (
                            f"Budgeted: {cat.budgeted / 1000:.2f}, "
                            f"Spent: {abs(cat.activity) / 1000:.2f}, "
                            f"Balance: {cat.balance / 1000:.2f}"
                        )
                        output += f"- {cat.name} (ID: {cat.id})\n  - {details}\n"
                        if cat.goal_type:
                            goal_progress = f"{cat.goal_percentage_complete or 0}%"
                            goal_target = (
                                f"{cat.goal_target / 1000:.2f}" 
                                if cat.goal_target else "N/A"
                            )
                            output += (
                                f"  - Goal ({cat.goal_type}): Target {goal_target}, "
                                f"{goal_progress} complete\n"
                            )
        return [types.TextContent(type="text", text=output)]
    elif name == "list-payees":
        budget_id = await _get_budget_id(arguments)
        payees = await ynab_client.get_payees(budget_id=budget_id)

        if not payees:
            return [types.TextContent(type="text", text="No payees found for this budget.")]

        payee_list = "\n".join(f"- {p.name} (ID: {p.id})" for p in payees)
        return [
            types.TextContent(
                type="text",
                text=f"Here are the payees for budget {budget_id}:\n{payee_list}",
            )
        ]
    elif name == "rename-payees":
        if (
            not arguments
            or "payee_ids" not in arguments
            or "name" not in arguments
        ):
            raise ValueError("Missing required arguments payee_ids and name")

        budget_id = await _get_budget_id(arguments)
        payee_ids = arguments["payee_ids"]
        name = arguments["name"]

        await ynab_client.update_payees(
            budget_id=budget_id,
            payee_ids=payee_ids,
            name=name,
        )

        return [
            types.TextContent(
                type="text",
                text=f"Successfully renamed {len(payee_ids)} payees to '{name}'.",
            )
        ]
    elif name == "assign-budget-amount":
        if (
            not arguments
            or "month" not in arguments
            or "category_id" not in arguments
            or "amount" not in arguments
        ):
            raise ValueError("Missing required arguments")

        budget_id = await _get_budget_id(arguments)
        month = arguments["month"]
        category_id = arguments["category_id"]
        amount = arguments["amount"]

        await ynab_client.assign_budget_amount(
            budget_id=budget_id,
            month=month,
            category_id=category_id,
            amount=amount,
        )

        return [
            types.TextContent(
                type="text",
                text=f"Successfully assigned {amount / 1000:.2f} to category {category_id} for {month}.",
            )
        ]
    elif name == "update-transactions":
        if (
            not arguments
            or "transactions" not in arguments
        ):
            raise ValueError("Missing required arguments")

        budget_id = await _get_budget_id(arguments)
        transactions_to_update = arguments["transactions"]

        updates = [
            SaveTransactionWithIdOrImportId(**tx_data)
            for tx_data in transactions_to_update
        ]
        await ynab_client.update_transactions(budget_id=budget_id, transactions=updates)

        return [
            types.TextContent(
                type="text",
                text=f"Successfully updated {len(transactions_to_update)} transactions.",
            )
        ]
    elif name == "move-budget-amount":
        if (
            not arguments
            or "month" not in arguments
            or "from_category_id" not in arguments
            or "to_category_id" not in arguments
            or "amount" not in arguments
        ):
            raise ValueError("Missing required arguments")

        budget_id = await _get_budget_id(arguments)
        month = arguments["month"]
        from_category_id = arguments["from_category_id"]
        to_category_id = arguments["to_category_id"]
        amount_to_move = arguments["amount"]

        from_cat = await ynab_client.get_month_category(budget_id, month, from_category_id)
        to_cat = await ynab_client.get_month_category(budget_id, month, to_category_id)

        new_from_budgeted = from_cat.budgeted - amount_to_move
        new_to_budgeted = to_cat.budgeted + amount_to_move

        await ynab_client.assign_budget_amount(budget_id, month, from_category_id, new_from_budgeted)
        await ynab_client.assign_budget_amount(budget_id, month, to_category_id, new_to_budgeted)

        return [
            types.TextContent(
                type="text",
                text=f"Successfully moved {amount_to_move / 1000:.2f} from category {from_cat.name} to {to_cat.name} for {month}.",
            )
        ]
    elif name == "list-scheduled-transactions":
        budget_id = await _get_budget_id(arguments)
        transactions = await ynab_client.get_scheduled_transactions(budget_id=budget_id)

        if not transactions:
            return [types.TextContent(type="text", text="No scheduled transactions found.")]

        scheduled_list = "\n".join(
            f"- {t.var_date}: {t.payee_name or 'N/A'} | "
            f"{t.category_name or 'N/A'} | {t.amount / 1000:.2f} "
            f"(Frequency: {t.frequency})"
            for t in transactions
        )
        return [
            types.TextContent(
                type="text",
                text=f"Here are the scheduled transactions:\n{scheduled_list}",
            )
        ]
    elif name == "get-financial-overview":
        overview = ynab_client.notes.load_overview()
        return [
            types.TextContent(
                type="text",
                text=f"Financial Overview (Last Updated: {overview.get('last_updated', 'Never')}):\n\n"
                     f"{json.dumps(overview, indent=2)}",
            )
        ]
    elif name == "update-financial-overview-section":
        if not arguments or "section" not in arguments or "data" not in arguments:
            raise ValueError("Missing required arguments section and data")

        section = arguments["section"]
        data = arguments["data"]

        ynab_client.notes.update_overview_section(section, data)
        return [
            types.TextContent(
                type="text",
                text=f"Successfully updated the {section} section of the financial overview.",
            )
        ]
    elif name == "refresh-financial-overview":
        budget_id = await _get_budget_id(arguments)

        # Get current account balances
        accounts = await ynab_client.get_accounts(budget_id=budget_id)
        account_balances = {
            acc.name: acc.balance / 1000
            for acc in accounts
        }

        # Get current month's categories
        categories = await ynab_client.get_categories(budget_id=budget_id)

        # Calculate monthly overview
        fixed_bills = 0
        discretionary_spending = 0
        savings = 0

        for group in categories:
            if group.name == "Bills":
                fixed_bills = sum(cat.budgeted for cat in group.categories if not cat.hidden)
            elif group.name == "Wants":
                discretionary_spending = sum(cat.budgeted for cat in group.categories if not cat.hidden)
            elif group.name == "Savings":
                savings = sum(cat.budgeted for cat in group.categories if not cat.hidden)

        total_budgeted = fixed_bills + discretionary_spending + savings
        savings_rate = (savings / total_budgeted * 100) if total_budgeted > 0 else 0

        # Update the overview
        overview = ynab_client.notes.load_overview()
        overview["account_balances"] = account_balances
        overview["monthly_overview"] = {
            "fixed_bills": fixed_bills / 1000,
            "discretionary_spending": discretionary_spending / 1000,
            "savings_rate": savings_rate
        }

        # Keep existing goals, action items, etc.
        ynab_client.notes.save_overview(overview)

        return [
            types.TextContent(
                type="text",
                text="Successfully refreshed the financial overview with latest YNAB data.",
            )
        ]

    raise ValueError(f"Unknown tool: {name}")


async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ynab-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
