# YNAB MCP Server

[![PyPI version](https://badge.fury.io/py/ynab-mcp-server.svg)](https://badge.fury.io/py/ynab-mcp-server)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Model Context Protocol (MCP) server for seamless integration with You Need A Budget (YNAB). This server enables AI assistants to interact with your YNAB budgets, providing powerful automation and analysis capabilities.

## Quick Installation (Claude Desktop)
```json
{
  "mcpServers": {
    "ynab-mcp": {
      "command": "uvx",
      "args": ["ynab-mcp-server"],
      "env": {
        "YNAB_PAT": "your_token_here",
      }
    }
  }
}
```
Optional environment variables:
```json
"env": {
  "YNAB_DEFAULT_BUDGET_ID": "your_budget_id",
  "YNAB_READ_ONLY": "true"
}
```
## Features

- **Complete Budget Management**
  - View and manage multiple budgets
  - Track account balances and transactions
  - Monitor category spending and goals
  
- **Transaction Control**
  - List and search transactions
  - Update transaction details
  - Manage payees and categories
  
- **Financial Analysis**
  - Get comprehensive financial overviews
  - Track spending patterns
  - Monitor budget progress

## Table of Contents

- [Installation](#installation)
- [Platform-Specific Setup](#platform-specific-setup)
- [Configuration](#configuration)
- [Available Tools](#available-tools)
- [Usage Examples](#usage-examples)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Installation & Usage

No installation needed when using `uvx`:

```bash
# Run directly (recommended)
uvx ynab-mcp-server

# Or with specific version
uvx ynab-mcp-server@0.1.1
```

For development:
```bash
# Clone and run from source
git clone https://github.com/yourusername/ynab-mcp-server.git
cd ynab-mcp-server
uv run ynab-mcp-server
```

## Platform-Specific Setup

### Claude Desktop

1. Locate your configuration file:
   - **MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. Add the YNAB MCP server configuration:
```json
{
  "mcpServers": {
    "ynab-mcp": {
      "command": "uvx",
      "args": ["ynab-mcp-server"],
      "env": {
        "YNAB_PAT": "your_token_here"
      }
    }
  }
}
```
Optional environment variables:
```json
env: {
  "YNAB_DEFAULT_BUDGET_ID": "your_budget_id",
  "YNAB_READ_ONLY": "true"
}
```

### Goose

1. Open Goose settings
2. Navigate to the MCP Servers section
3. Add a new server with:
   - Name: `ynab-mcp`
   - Command: `uvx ynab-mcp-server`
   - Environment Variables:
     - YNAB_PAT: your_token_here

### Other Platforms

For other MCP-compatible platforms, configure using these parameters:
- Server Name: `ynab-mcp`
- Command: `uvx`
- Arguments: `ynab-mcp-server`
- Required Environment Variable: `YNAB_PAT`

## Configuration

Your server can be configured using environment variables. You can place these in a `.env` file in the project root or set them in your shell.

| Variable | Required | Description |
|---|---|---|
| `YNAB_PAT` | **Yes** | Your YNAB Personal Access Token. |
| `YNAB_DEFAULT_BUDGET_ID` | No | If set, the server operates in single-budget mode, always using this budget ID. The `list-budgets` tool will be hidden. |
| `YNAB_READ_ONLY` | No | Set to `true` to disable all tools that make changes to your YNAB data. |

### Getting Your YNAB Token

1. **Get Your YNAB Token**
   - Go to [YNAB Developer Settings](https://app.ynab.com/settings/developer)
   - Create a new Personal Access Token
   - Copy the token value

2. **Set Up Environment**
   
   Create a `.env` file in your working directory:
   ```
   YNAB_PAT="your_token_here"
   YNAB_DEFAULT_BUDGET_ID="your_budget_id"
   YNAB_READ_ONLY="true"
   ```
   
   Or set the environment variable directly:
   ```bash
   export YNAB_PAT="your_token_here"
   ```

## Available Tools

The server provides a suite of tools for interacting with your YNAB data. The descriptions explain the purpose and recommended usage for each tool.

| Tool | Description |
|---|---|
| `manage-financial-overview` | Get, update, or refresh a high-level financial overview. **This is the best starting point for any analysis**, providing account balances, goals, and important context notes. |
| `list-accounts` | List all accounts for a given budget. Useful for getting account IDs for other tools. |
| `get-month-info` | Get detailed budget information for a single month, including age of money and total amounts budgeted, spent, and available. **Call this to check the monthly budget's status before making changes.** |
| `list-categories` | List all categories, groups, and their budgeting details. **Call this before managing budgeted amounts** to see what's available and what's already been allocated. |
| `list-transactions` | List transactions for a specific account or an entire month. Use this to **investigate spending patterns** identified in the financial overview. |
| `list-scheduled-transactions` | List all upcoming scheduled transactions. Useful for **forecasting upcoming bills**. |
| `manage-budgeted-amount` | Assign a budgeted amount to a category or move money between categories. This is the **primary tool for allocating funds**. (Write operations disabled in read-only mode) |
| `bulk-manage-transactions` | Create, update, or delete multiple transactions at once. More efficient than making single changes. (Write operations disabled in read-only mode) |
| `manage-scheduled-transaction`| Create, update, or delete a single scheduled (recurring) transaction. Use this to **manage recurring bills or savings transfers**. (Write operations disabled in read-only mode) |
| `list-payees` | List all payees for a given budget. Good for finding payee IDs or identifying messy payee data that needs to be merged. |
| `manage-payees` | Merge multiple payee names into a single name. Use this to **clean up payee data**. (Write operations disabled in read-only mode) |
| `lookup-entity-by-id` | Look up the name and details of a specific account, category, or payee by its ID. A utility for when you have an ID but need the full context. |
| `lookup-payee-locations` | Look up geographic locations associated with a payee. |
| `list-budgets` | List all available YNAB budgets (Not available in single-budget mode). |

## Development

### Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ynab-mcp-server.git
   cd ynab-mcp-server
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Run the server:
   ```bash
   uv run ynab-mcp-server
   ```

### Debugging

Use the MCP Inspector for debugging:
```bash
npx @modelcontextprotocol/inspector uvx ynab-mcp-server
```

For local development debugging:
```bash
cd path/to/ynab-mcp-server
npx @modelcontextprotocol/inspector uv run ynab-mcp-server
```

You can also view logs with:
```bash
tail -n 20 -f ~/Library/Logs/Claude/mcp*.log
```

### Building and Publishing
```bash
# Build package
uv build

# Publish to PyPI
uv publish
```

## Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure your PR:
- Follows the existing code style
- Includes appropriate tests
- Updates documentation as needed

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [YNAB API](https://api.ynab.com/) for providing the core functionality
- [Model Context Protocol](https://github.com/modelcontextprotocol/protocol) for enabling AI assistant integration