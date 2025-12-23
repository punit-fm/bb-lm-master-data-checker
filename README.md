# Streamlit PostgreSQL Data Viewer

A modern, beautiful web application built with Streamlit to connect to PostgreSQL databases, fetch data, and display it in an interactive UI.

![PostgreSQL + Streamlit](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

## ✨ Features

- 🎨 **Modern UI** - Beautiful gradient design with smooth animations
- 🔌 **Database Connection** - Easy PostgreSQL connection with status indicators
- 📊 **Table Browser** - Browse all tables in your database
- 🔍 **Search & Filter** - Real-time search across all columns
- 📈 **Data Metrics** - View row counts, column info, and memory usage
- 💾 **Export Data** - Download table data as CSV
- ℹ️ **Table Info** - View column names, data types, and constraints
- 🔄 **Auto-refresh** - Refresh data with a single click

## 📋 Prerequisites

- Python 3.8 or higher
- PostgreSQL database (local or remote)
- Database credentials (host, port, database name, username, password)

## 🚀 Installation

1. **Navigate to the project directory:**
   ```bash
   cd streamlit-postgres-app
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure database credentials:**
   
   Copy the `.env.example` file to `.env`:
   ```bash
   copy .env.example .env
   ```
   
   Edit the `.env` file with your PostgreSQL credentials:
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=your_database_name
   DB_USER=your_username
   DB_PASSWORD=your_password
   ```

## 🎯 Usage

1. **Run the application:**
   ```bash
   streamlit run app.py
   ```

2. **Open your browser:**
   
   The application will automatically open at `http://localhost:8501`

3. **Test connection:**
   
   Click the "🔌 Test Connection" button in the sidebar to verify your database connection

4. **Browse data:**
   
   - Select a table from the dropdown
   - View data in the "Data" tab
   - Check column information in the "Table Info" tab
   - Use the search box to filter data
   - Download data as CSV

## 📁 Project Structure

```
streamlit-postgres-app/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .env.example          # Example environment variables
├── .env                  # Your database credentials (create this)
├── database/
│   └── db_utils.py       # Database connection utilities
└── README.md             # This file
```

## 🛠️ Customization

### Modify the UI Theme

Edit the custom CSS in `app.py` to change colors, fonts, and styling:

```python
st.markdown("""
    <style>
    /* Your custom CSS here */
    </style>
""", unsafe_allow_html=True)
```

### Add Custom Queries

Extend `database/db_utils.py` to add custom query functions:

```python
def custom_query(param):
    query = "SELECT * FROM table WHERE column = %s"
    return execute_query(query, (param,))
```

### Change Row Limits

Modify the row limit options in `app.py`:

```python
row_limit = st.selectbox(
    "Rows to display:",
    options=[10, 50, 100, 500, 1000],  # Customize these values
    index=2
)
```

## 🔒 Security Notes

- ⚠️ **Never commit your `.env` file** to version control
- The `.env` file contains sensitive database credentials
- Add `.env` to your `.gitignore` file
- Use environment-specific credentials for production

## 🐛 Troubleshooting

### Connection Failed

- Verify database credentials in `.env`
- Check if PostgreSQL server is running
- Ensure your IP is allowed to connect to the database
- Check firewall settings

### Module Not Found

- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Activate your virtual environment if using one

### Port Already in Use

- Streamlit default port is 8501
- Run on a different port: `streamlit run app.py --server.port 8502`

## 📝 License

This project is open source and available for personal and commercial use.

## 🤝 Contributing

Feel free to fork this project and customize it for your needs!

## 📧 Support

For issues or questions, please check the troubleshooting section or consult the Streamlit and psycopg2 documentation.

---

**Built with ❤️ using Streamlit and PostgreSQL**
