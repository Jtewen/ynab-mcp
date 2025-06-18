# YNAB MCP Server

[![PyPI version](https://badge.fury.io/py/ynab-mcp-server.svg)](https://badge.fury.io/py/ynab-mcp-server)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Model Context Protocol (MCP) server for seamless integration with You Need A Budget (YNAB). This server enables AI assistants to interact with your YNAB budgets, providing powerful automation and analysis capabilities.

## 📦 Quick Installation (Claude Desktop)
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

## 🌟 Features

- 📊 **Complete Budget Management**
  - View and manage multiple budgets
  - Track account balances and transactions
  - Monitor category spending and goals
  
- 💰 **Transaction Control**
  - List and search transactions
  - Update transaction details
  - Manage payees and categories
  
- 📈 **Financial Analysis**
  - Get comprehensive financial overviews
  - Track spending patterns
  - Monitor budget progress

## 📋 Table of Contents

- [Installation](#installation)
- [Platform-Specific Setup](#platform-specific-setup)
- [Configuration](#configuration)
- [Available Tools](#available-tools)
- [Usage Examples](#usage-examples)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Installation & Usage

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

## 🔧 Platform-Specific Setup

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

## ⚙️ Configuration

1. **Get Your YNAB Token**
   - Go to [YNAB Developer Settings](https://app.ynab.com/settings/developer)
   - Create a new Personal Access Token
   - Copy the token value

2. **Set Up Environment**
   
   Create a `.env` file in your working directory:
   ```
   YNAB_PAT="your_token_here"
   ```
   
   Or set the environment variable directly:
   ```bash
   export YNAB_PAT="your_token_here"
   ```

## 🛠️ Available Tools

### Budget Management
| Tool | Description |
|------|-------------|
| `list-budgets` | List all available YNAB budgets |
| `list-accounts` | List all accounts for a given budget |
| `list-categories` | List categories with budgeted amounts |

### Transaction Management
| Tool | Description |
|------|-------------|
| `list-transactions` | List account transactions |
| `list-monthly-transactions` | List transactions by month |
| `update-transactions` | Update transaction details |

### Financial Overview
| Tool | Description |
|------|-------------|
| `get-financial-overview` | Get current financial status |
| `refresh-financial-overview` | Update overview with latest data |

### Budget Planning
| Tool | Description |
|------|-------------|
| `move-budget-amount` | Transfer between categories |
| `assign-budget-amount` | Set category budget |

## 📝 Usage Examples

### Basic Budget Overview
```python
# List all budgets
result = await handle_call_tool("list-budgets", {})

# View current month's transactions
result = await handle_call_tool("list-monthly-transactions", {
    "month": "2024-03-01"
})
```

### Category Management
```python
# Move funds between categories
result = await handle_call_tool("move-budget-amount", {
    "month": "2024-03-01",
    "from_category_id": "11111111-2222-3333-4444-555555555555",  # Example: Dining Out
    "to_category_id": "66666666-7777-8888-9999-000000000000",    # Example: Groceries
    "amount": 5000  # $50.00 (amounts are in milliunits)
})
```

### Transaction Updates
```python
# Update transaction details
result = await handle_call_tool("update-transactions", {
    "transactions": [{
        "id": "12345678-90ab-cdef-ghij-klmnopqrstuv",  # Example UUID
        "category_id": "98765432-fedc-ba98-7654-321012345678",  # Example category UUID
        "memo": "Updated grocery shopping description"
    }]
})
```

## 🔨 Development

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

## 👥 Contributing

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

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [YNAB API](https://api.ynab.com/) for providing the core functionality
- [Model Context Protocol](https://github.com/modelcontextprotocol/protocol) for enabling AI assistant integration