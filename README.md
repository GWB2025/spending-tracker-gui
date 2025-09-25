# Spending Tracker GUI

A desktop GUI application for tracking personal spending using PySide6, with optional Google Sheets integration for data synchronisation across devices.

## Features

- 💰 **Expense Tracking**: Record and categorise your spending with an intuitive interface
- 📊 **Visual Dashboard**: Charts and graphs to visualise spending patterns  
- 🔄 **Google Sheets Integration**: Optional synchronisation with Google Sheets
- 📧 **Email Reports**: Automated monthly spending summaries via email
- 🏷️ **Category Management**: Organise expenses with customisable categories
- 📈 **Budget Monitoring**: Track spending against set budgets
- 🔁 **Recurring Expenses**: Automatically add recurring transactions
- 💷 **Multi-Currency**: Support for multiple currencies (defaults to GBP)

## Requirements

- Python 3.8 or higher
- Windows 10/11 (tested platform)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/spending-tracker-gui.git
   cd spending-tracker-gui
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

### Option 1: Using the Command Script (Windows)
Double-click `SpendingTracker.cmd` or run it from the command line.

### Option 2: Running with Python
```bash
python src/main.py
```

## Configuration

The application uses `config/config.yaml` for settings. Key configurations include:

- **Currency**: Default is GBP (£), but supports USD, EUR, JPY, CAD, AUD, INR, CNY
- **Categories**: Customisable expense categories
- **Email Settings**: SMTP configuration for reports
- **Google Sheets**: Spreadsheet integration settings

## Google Sheets Integration (Optional)

To enable Google Sheets synchronisation:

1. **Create Google Cloud Project:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the Google Sheets API

2. **Create Credentials:**
   - Go to "Credentials" in the API & Services section
   - Create OAuth 2.0 client ID for desktop application
   - Download the credentials JSON file

3. **Setup Credentials:**
   - Copy the downloaded file to `config/credentials.json`
   - Or use the template in `config/credentials.json.template`

4. **First Run:**
   - The app will prompt you to authenticate with Google
   - Grant permission to access Google Sheets
   - Create or specify a Google Sheets spreadsheet

## Project Structure

```
spending-tracker-gui/
├── src/                    # Application source code
│   ├── config/            # Configuration management
│   ├── controllers/       # Business logic controllers  
│   ├── gui/              # PySide6 GUI components
│   ├── models/           # Data models
│   ├── services/         # External service integrations
│   └── main.py           # Application entry point
├── config/               # Configuration files
│   ├── config.yaml       # Main configuration
│   └── credentials.json.template  # Google API credentials template
├── data/                 # Local data storage
│   └── expenses.json     # Local expense data
├── requirements.txt      # Python dependencies
└── SpendingTracker.cmd   # Windows launch script
```

## Usage

### Adding Expenses
1. Launch the application
2. Click "Add Expense" 
3. Enter amount, category, description, and date
4. Click "Save"

### Viewing Reports  
- Access charts and summaries from the main dashboard
- Export data to CSV for external analysis
- View spending by category, time period, or custom filters

### Email Reports
Configure SMTP settings in `config.yaml` to receive automated monthly reports.

### Factory Reset
Use the "Factory Reset" option in settings to clear all local data and start fresh.

## Development

### Running Tests
```bash
# Install test dependencies if not already installed
pip install pytest pytest-cov

# Run tests (when test files are present)
python -m pytest tests/
```

### Code Style
The project follows PEP8 guidelines. Format code using:
```bash
black src/
flake8 src/
```

## Troubleshooting

### Common Issues

**"Missing required dependencies" error:**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

**Google Sheets authentication fails:**
- Check `credentials.json` file exists and is valid
- Ensure Google Sheets API is enabled in Google Cloud Console
- Try deleting `config/token.json` to re-authenticate

**App shows old data after factory reset:**
- This may occur if Google Sheets sync is active
- Disconnect from Google Sheets or clear the spreadsheet manually

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)  
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support or questions, please open an issue in the GitHub repository.