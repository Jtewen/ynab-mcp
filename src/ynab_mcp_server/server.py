import asyncio
import json
from datetime import datetime

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from ynab.models import NewTransaction, SaveTransactionWithIdOrImportId, SaveScheduledTransaction

from .tool_models import (
    BulkManageTransactionsInput,
    ListAccountsInput,
    ListCategoriesInput,
    ListPayeesInput,
    ListTransactionsInput,
    ManageScheduledTransactionInput,
    LookupEntityByIdInput,
    GetMonthInfoInput,
    LookupPayeeLocationsInput,
    ManageBudgetedAmountInput,
    ManageFinancialOverviewInput,
    ManagePayeesInput,
)
from .ynab_client import ynab_client
from .settings import settings

server = Server("ynab-mcp")

READ_ONLY_TOOLS = {
    "list-budgets",
    "list-accounts",
    "list-transactions",
    "list-categories",
    "list-payees",
    "list-scheduled-transactions",
    "get-financial-overview",
    "get-month-info",
    "lookup-payee-locations",
}


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    """
    all_tools = [
        types.Tool(
            name="list-budgets",
            description="List all available YNAB budgets",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="list-accounts",
            description="List all accounts for a given budget. Useful for getting account IDs for other tools.",
            inputSchema=ListAccountsInput.model_json_schema(),
        ),
        types.Tool(
            name="list-transactions",
            description="List transactions for a specific account or an entire month. Use this to investigate spending patterns identified in the financial overview.",
            inputSchema=ListTransactionsInput.model_json_schema(),
        ),
        types.Tool(
            name="list-categories",
            description=(
                "List all categories, groups, and their budgeting details for a given budget. "
                "Call this before managing budgeted amounts to see what's available and what's already been allocated."
            ),
            inputSchema=ListCategoriesInput.model_json_schema(),
        ),
        types.Tool(
            name="list-payees",
            description="List all payees for a given budget. Good for finding payee IDs or identifying messy payee data that needs to be merged.",
            inputSchema=ListPayeesInput.model_json_schema(),
        ),
        types.Tool(
            name="manage-payees",
            description="Merge multiple payee names into a single name. Use this to clean up payee data, for example, by renaming 'STARBUCKS #123' and 'Starbucks Coffee' to just 'Starbucks'.",
            inputSchema=ManagePayeesInput.model_json_schema(),
        ),
        types.Tool(
            name="manage-budgeted-amount",
            description="Assign a budgeted amount to a category or move money between categories for a specific month. This is the primary tool for allocating funds.",
            inputSchema=ManageBudgetedAmountInput.model_json_schema(),
        ),
        types.Tool(
            name="bulk-manage-transactions",
            description="Create, update, or delete multiple transactions at once. More efficient than making single changes.",
            inputSchema=BulkManageTransactionsInput.model_json_schema(),
        ),
        types.Tool(
            name="list-scheduled-transactions",
            description="List all upcoming scheduled transactions for a given budget. Useful for forecasting upcoming bills.",
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
            name="manage-financial-overview",
            description="Get, update, or refresh a high-level financial overview. This is the best starting point for any analysis, providing account balances, goals, and important context notes.",
            inputSchema=ManageFinancialOverviewInput.model_json_schema(),
        ),
        types.Tool(
            name="manage-scheduled-transaction",
            description="Create, update, or delete a single scheduled (recurring) transaction. Use this to manage recurring bills or savings transfers.",
            inputSchema=ManageScheduledTransactionInput.model_json_schema(),
        ),
        types.Tool(
            name="lookup-entity-by-id",
            description="Look up the name and details of a specific account, category, or payee by its ID. A utility for when you have an ID but need the full context.",
            inputSchema=LookupEntityByIdInput.model_json_schema(),
        ),
        types.Tool(
            name="get-month-info",
            description="Get detailed budget information for a single month, including age of money and total amounts budgeted, spent, and available. Call this to check the monthly budget's status before making changes.",
            inputSchema=GetMonthInfoInput.model_json_schema(),
        ),
        types.Tool(
            name="lookup-payee-locations",
            description="Look up geographic locations associated with a payee.",
            inputSchema=LookupPayeeLocationsInput.model_json_schema(),
        ),
    ]

    tools = all_tools
    if settings.ynab_read_only:
        tools = [tool for tool in tools if tool.name in READ_ONLY_TOOLS]
    
    if settings.ynab_default_budget_id:
        tools = [tool for tool in tools if tool.name != "list-budgets"]

    return tools


async def _get_budget_id(arguments: dict | None) -> str:
    """Gets the budget_id from arguments, settings, or falls back to the default budget."""
    if settings.ynab_default_budget_id:
        return settings.ynab_default_budget_id

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
    if settings.ynab_read_only and name not in READ_ONLY_TOOLS:
        raise ValueError(
            "The server is in read-only mode. Write operations are disabled."
        )

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
        args = ListAccountsInput.model_validate(arguments or {})
        budget_id = await _get_budget_id(args.model_dump())
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
        args = ListTransactionsInput.model_validate(arguments or {})
        budget_id = await _get_budget_id(args.model_dump())
        
        limit = int(args.limit) if args.limit is not None else None
        
        if args.account_id:
            transactions = await ynab_client.get_transactions(
                budget_id=budget_id,
                account_id=args.account_id,
                since_date=args.since_date,
                limit=limit,
            )
            header = f"Here are the latest transactions for account {args.account_id}:"
        elif args.month:
            transactions = await ynab_client.get_monthly_transactions(
                budget_id=budget_id,
                month=args.month,
                limit=limit,
            )
            header = f"Here are the transactions for {args.month}:"
        else:
            # This case should be prevented by the model validator
            raise ValueError("Either 'account_id' or 'month' must be provided.")

        if not transactions:
            return [types.TextContent(type="text", text="No transactions found.")]

        transaction_list = "\n".join(
            f"- {t.var_date}: {t.payee_name or 'N/A'} | "
            f"{t.category_name or 'N/A'} | {t.amount / 1000:.2f} (ID: {t.id})"
            for t in transactions
        )
        return [
            types.TextContent(
                type="text",
                text=f"{header}\n{transaction_list}",
            )
        ]
    elif name == "list-categories":
        args = ListCategoriesInput.model_validate(arguments or {})
        budget_id = await _get_budget_id(args.model_dump())
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
        args = ListPayeesInput.model_validate(arguments or {})
        budget_id = await _get_budget_id(args.model_dump())
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
    elif name == "manage-payees":
        args = ManagePayeesInput.model_validate(arguments or {})
        budget_id = await _get_budget_id(args.model_dump())

        if args.action == "rename":
            await ynab_client.update_payees(
                budget_id=budget_id,
                payee_ids=args.payee_ids,
                name=args.name,
            )
            return [
                types.TextContent(
                    type="text",
                    text=f"Successfully renamed {len(args.payee_ids)} payees to '{args.name}'.",
                )
            ]
    elif name == "manage-budgeted-amount":
        args = ManageBudgetedAmountInput.model_validate(arguments or {})
        budget_id = await _get_budget_id(args.model_dump())
        amount = int(args.amount)
        month = args.month
        
        if args.action == "assign":
            await ynab_client.assign_budget_amount(
                budget_id=budget_id,
                month=month,
                category_id=args.to_category_id,
                amount=amount,
            )
            return [
                types.TextContent(
                    type="text",
                    text=f"Successfully assigned {amount / 1000:.2f} to category {args.to_category_id} for {month}.",
                )
            ]
        elif args.action == "move":
            from_cat = await ynab_client.get_month_category(budget_id, month, args.from_category_id)
            to_cat = await ynab_client.get_month_category(budget_id, month, args.to_category_id)

            new_from_budgeted = from_cat.budgeted - amount
            new_to_budgeted = to_cat.budgeted + amount

            await ynab_client.assign_budget_amount(budget_id, month, args.from_category_id, new_from_budgeted)
            await ynab_client.assign_budget_amount(budget_id, month, args.to_category_id, new_to_budgeted)
            
            return [
                types.TextContent(
                    type="text",
                    text=f"Successfully moved {amount / 1000:.2f} from category {from_cat.name} to {to_cat.name} for {month}.",
                )
            ]
    elif name == "bulk-manage-transactions":
        args = BulkManageTransactionsInput.model_validate(arguments or {})
        budget_id = await _get_budget_id(args.model_dump())

        if args.action == "create":
            new_transactions = []
            for tx in args.create_transactions:
                tx_data = {k: v for k, v in tx.model_dump().items() if v is not None}
                if "amount" in tx_data:
                    tx_data["amount"] = int(tx_data["amount"])
                new_transactions.append(NewTransaction(**tx_data))
            
            result = await ynab_client.create_transactions(
                budget_id=budget_id, transactions=new_transactions
            )

            created_ids = ", ".join(result.transaction_ids)
            duplicate_ids = ", ".join(result.duplicate_import_ids)

            response_text = f"Successfully processed bulk transaction request. Server Knowledge: {result.server_knowledge}\n"
            if created_ids:
                response_text += f"Created transaction IDs: {created_ids}\n"
            if duplicate_ids:
                response_text += f"Duplicate import IDs (skipped): {duplicate_ids}\n"
            
            return [types.TextContent(type="text", text=response_text.strip())]
        
        elif args.action == "update":
            updates = []
            for tx in args.update_transactions:
                tx_data = {k: v for k, v in tx.model_dump().items() if v is not None}
                if "amount" in tx_data:
                    tx_data["amount"] = int(tx_data["amount"])
                updates.append(SaveTransactionWithIdOrImportId(**tx_data))
            await ynab_client.update_transactions(budget_id=budget_id, transactions=updates)

            return [
                types.TextContent(
                    type="text",
                    text=f"Successfully updated {len(args.update_transactions)} transactions.",
                )
            ]

        elif args.action == "delete":
            deleted_ids = []
            for tx_id in args.delete_transaction_ids:
                await ynab_client.delete_transaction(
                    budget_id=budget_id, transaction_id=tx_id
                )
                deleted_ids.append(tx_id)
            
            return [
                types.TextContent(
                    type="text",
                    text=f"Successfully deleted {len(deleted_ids)} transactions: {', '.join(deleted_ids)}",
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
    elif name == "manage-financial-overview":
        args = ManageFinancialOverviewInput.model_validate(arguments or {})
        
        if args.action == "get":
            overview = ynab_client.notes.load_overview()
            return [
                types.TextContent(
                    type="text",
                    text=f"Financial Overview (Last Updated: {overview.get('last_updated', 'Never')}):\n\n"
                         f"{json.dumps(overview, indent=2)}",
                )
            ]
        elif args.action == "update":
            ynab_client.notes.update_overview_section(args.section, args.data)
            return [
                types.TextContent(
                    type="text",
                    text=f"Successfully updated the {args.section} section of the financial overview.",
                )
            ]
        elif args.action == "refresh":
            budget_id = await _get_budget_id(args.model_dump())
            accounts = await ynab_client.get_accounts(budget_id=budget_id)
            account_balances = {
                acc.name: acc.balance / 1000
                for acc in accounts
            }
            categories = await ynab_client.get_categories(budget_id=budget_id)
            fixed_bills, discretionary_spending, savings = 0, 0, 0
            for group in categories:
                if "bills" in group.name.lower():
                    fixed_bills = sum(cat.budgeted for cat in group.categories if not cat.hidden)
                elif "wants" in group.name.lower() or "spending" in group.name.lower():
                    discretionary_spending = sum(cat.budgeted for cat in group.categories if not cat.hidden)
                elif "savings" in group.name.lower():
                    savings = sum(cat.budgeted for cat in group.categories if not cat.hidden)
            total_budgeted = fixed_bills + discretionary_spending + savings
            savings_rate = (savings / total_budgeted * 100) if total_budgeted > 0 else 0
            overview = ynab_client.notes.load_overview()
            overview["account_balances"] = account_balances
            overview["monthly_overview"] = {
                "fixed_bills": fixed_bills / 1000,
                "discretionary_spending": discretionary_spending / 1000,
                "savings_rate": savings_rate
            }
            ynab_client.notes.save_overview(overview)
            return [
                types.TextContent(
                    type="text",
                    text="Successfully refreshed the financial overview with latest YNAB data.",
                )
            ]
    elif name == "manage-scheduled-transaction":
        args = ManageScheduledTransactionInput.model_validate(arguments or {})
        budget_id = await _get_budget_id(args.model_dump())

        action = args.action
        if action == "create":
            transaction_data = {
                k: v for k, v in args.transaction_data.model_dump().items() if v is not None
            }
            if "amount" in transaction_data:
                transaction_data["amount"] = int(transaction_data["amount"])
            
            await ynab_client.create_scheduled_transaction(
                budget_id=budget_id, transaction=SaveScheduledTransaction(**transaction_data)
            )
            return [
                types.TextContent(
                    type="text",
                    text="Successfully created scheduled transaction.",
                )
            ]
        elif action == "update":
            transaction_data = {
                k: v for k, v in args.transaction_data.model_dump().items() if v is not None
            }
            if "amount" in transaction_data:
                transaction_data["amount"] = int(transaction_data["amount"])

            await ynab_client.update_scheduled_transaction(
                budget_id=budget_id,
                transaction_id=args.transaction_id,
                transaction=SaveScheduledTransaction(**transaction_data),
            )
            return [
                types.TextContent(
                    type="text",
                    text=f"Successfully updated scheduled transaction {args.transaction_id}.",
                )
            ]
        elif action == "delete":
            await ynab_client.delete_scheduled_transaction(
                budget_id=budget_id, transaction_id=args.transaction_id
            )
            return [
                types.TextContent(
                    type="text",
                    text=f"Successfully deleted scheduled transaction {args.transaction_id}.",
                )
            ]
    elif name == "lookup-entity-by-id":
        args = LookupEntityByIdInput.model_validate(arguments or {})
        budget_id = await _get_budget_id(args.model_dump())

        entity = None
        if args.entity_type == "account":
            entity = await ynab_client.get_account_by_id(budget_id, args.entity_id)
        elif args.entity_type == "category":
            entity = await ynab_client.get_category_by_id(budget_id, args.entity_id)
        elif args.entity_type == "payee":
            entity = await ynab_client.get_payee_by_id(budget_id, args.entity_id)

        if not entity:
            return [
                types.TextContent(
                    type="text",
                    text=f"No {args.entity_type} found with ID {args.entity_id}.",
                )
            ]

        entity_dict = entity.to_dict()
        return [
            types.TextContent(
                type="text",
                text=f"Found {args.entity_type}:\n{json.dumps(entity_dict, indent=2, default=str)}",
            )
        ]
    elif name == "get-month-info":
        args = GetMonthInfoInput.model_validate(arguments or {})
        budget_id = await _get_budget_id(args.model_dump())

        if args.month:
            # Get a single month
            month_detail = await ynab_client.get_budget_month(budget_id, args.month)
            result_dict = month_detail.to_dict()
            text_output = f"Details for month {args.month}:\n{json.dumps(result_dict, indent=2, default=str)}"
        else:
            # List all months
            months = await ynab_client.get_budget_months(budget_id)
            month_list = "\n".join(
                f"- Month: {m.month}, Budgeted: {m.budgeted / 1000:.2f}, Activity: {m.activity / 1000:.2f}, To Be Budgeted: {m.to_be_budgeted / 1000:.2f}"
                for m in months
            )
            text_output = f"Available months for budget {budget_id}:\n{month_list}"

        return [types.TextContent(type="text", text=text_output)]
    elif name == "lookup-payee-locations":
        args = LookupPayeeLocationsInput.model_validate(arguments or {})
        budget_id = await _get_budget_id(args.model_dump())
        locations = []
        if args.location_id:
            location = await ynab_client.get_payee_location_by_id(
                budget_id, args.location_id
            )
            locations = [location] if location else []
        elif args.payee_id:
            locations = await ynab_client.get_payee_locations_by_payee(
                budget_id, args.payee_id
            )
        else:
            locations = await ynab_client.get_payee_locations(budget_id)

        if not locations:
            return [types.TextContent(type="text", text="No payee locations found.")]

        locations_dict = [loc.to_dict() for loc in locations]
        return [
            types.TextContent(
                type="text",
                text=f"Found {len(locations)} payee locations:\n{json.dumps(locations_dict, indent=2, default=str)}",
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
