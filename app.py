# app.py

import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import os

# ---------------------------#
#         Page Config         #
# ---------------------------#

st.set_page_config(page_title="📚 LibTech Database", layout="wide")

# ---------------------------#
#       Database Setup        #
# ---------------------------#

#TO BE CHANGED ACCORDING TO EACH PERSON'S.

DB_HOST = "127.0.0.1"
DB_PORT = "5432"
DB_NAME = "xxx"
DB_USER = "xxx"
DB_PASSWORD = "xxx"
ENCRYPTION_KEY = "s3cUr3!kEy#2023@P0stgreSQL^"

@st.cache_resource
def get_connection():
    """
    Establishes a connection to the PostgreSQL database using provided credentials.
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        st.error(f"Error connecting to the database: {e}")
        return None

conn = get_connection()

# ---------------------------#
#       Helper Functions      #
# ---------------------------#

def run_query(_query, params=None):
    """
    Executes a SQL query and returns the result as a pandas DataFrame.
    """
    if conn is None:
        st.error("No database connection.")
        return pd.DataFrame()
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(_query, params)
            records = cur.fetchall()
            if records:
                df = pd.DataFrame(records)
            else:
                df = pd.DataFrame()
            return df
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return pd.DataFrame()

def execute_query(query, params=None, suppress_success=False):
    """
    Executes a SQL query that does not return data (e.g., CREATE, INSERT, UPDATE).
    Optionally suppresses the success message.
    """
    if conn is None:
        st.error("No database connection.")
        return
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()
        if not suppress_success:
            st.success("Operation executed successfully.")
    except Exception as e:
        st.error(f"Error executing operation: {e}")
        conn.rollback()

def call_procedure(proc_name, params):
    """
    Calls a stored procedure with the given name and parameters.
    """
    if conn is None:
        st.error("No database connection.")
        return
    try:
        with conn.cursor() as cur:
            cur.callproc(proc_name, params)
            conn.commit()
        st.success(f"Procedure '{proc_name}' executed successfully.")
    except Exception as e:
        st.error(f"Error executing procedure '{proc_name}': {e}")
        conn.rollback()

# ---------------------------#
#         App Layout         #
# ---------------------------#

with st.container():
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("logo.jpg", width=100)  # Adjust the path if your logo is elsewhere
    with col2:
        st.title("LibTech Database Management")

# Define query categories and their respective queries
query_categories = {
    "Book Rentals & Branch Performance": {
        "Top 5 Borrowed Books in the Last Year": {
            "query": """
                SELECT br.title, COUNT(b.bookid) AS borrow_count
                FROM borrows b
                JOIN books_for_rent br ON b.bookid = br.bookid
                WHERE b.date_out >= CURRENT_DATE - INTERVAL '1 year'
                GROUP BY br.title
                ORDER BY borrow_count DESC
                LIMIT 5;
            """,
            "requires_params": False
        },
        "Customers with Unreturned Books Past Due Date": {
            "query": """
                SELECT 
                    c.username, 
                    c.first_name, 
                    c.last_name, 
                    b.bookid, 
                    br.title, 
                    b.due_date, 
                    b.penalty,
                    (b.penalty + (CURRENT_DATE - b.due_date) * 0.5) AS fine_amount
                FROM borrows b
                JOIN customer c ON b.username = c.username
                JOIN books_for_rent br ON b.bookid = br.bookid
                WHERE b.status = 'Borrowed'
                AND b.due_date < CURRENT_DATE;
            """,
            "requires_params": False
        },
        "Branch with the Highest Number of Rentals": {
            "query": """
                SELECT b.branchid, COUNT(br.bookid) AS rentals_count
                FROM borrows br
                JOIN books_for_rent b ON br.bookid = b.bookid
                GROUP BY b.branchid
                ORDER BY rentals_count DESC
                LIMIT 1;
            """,
            "requires_params": False
        }
    },
    "Customer Insights": {
        "Total Amount Spent by Each Customer & Favorite Branch": {
            "query": """
                SELECT 
                    c.username,
                    c.first_name,
                    c.last_name,
                    COALESCE(SUM(b.quantity * bs.price), 0) AS total_book_spending,
                    COALESCE(SUM(i.quantity * it.price), 0) AS total_item_spending,
                    (SELECT branchid 
                     FROM buys_books b2 
                     WHERE b2.username = c.username 
                     GROUP BY branchid 
                     ORDER BY COUNT(*) DESC 
                     LIMIT 1) AS favorite_branch
                FROM 
                    customer c
                LEFT JOIN buys_books b ON c.username = b.username
                LEFT JOIN books_for_sale bs ON b.isbn = bs.isbn
                LEFT JOIN purchases_items i ON c.username = i.username
                LEFT JOIN items it ON i.barcode = it.barcode
                GROUP BY 
                    c.username, c.first_name, c.last_name;
            """,
            "requires_params": False
        },
        "Categorize Customers into Segments": {
            "query": """
                WITH customer_spend AS ( 
                    SELECT 
                        c.username, 
                        COALESCE(SUM(b.quantity * bs.price), 0) + COALESCE(SUM(i.quantity * it.price), 0) AS total_spending
                    FROM 
                        customer c
                    LEFT JOIN buys_books b ON c.username = b.username
                    LEFT JOIN books_for_sale bs ON b.isbn = bs.isbn
                    LEFT JOIN purchases_items i ON c.username = i.username
                    LEFT JOIN items it ON i.barcode = it.barcode
                    GROUP BY c.username
                )
                SELECT 
                    username, 
                    CASE 
                        WHEN total_spending > 500 THEN 'High Spender'
                        WHEN total_spending BETWEEN 200 AND 500 THEN 'Medium Spender'
                        ELSE 'Low Spender'
                    END AS customer_segment
                FROM 
                    customer_spend;
            """,
            "requires_params": False
        },
        "View Customers With Penalties": {
            "query": """
                SELECT * FROM Customers_With_Penalties;
            """,
            "requires_params": False
        }
    },
    "Supplier & Revenue Analysis": {
        "Top 5 Suppliers by Revenue": {
            "query": """
                SELECT 
                    s.supp_name, 
                    SUM(i.price * p.quantity) AS total_revenue
                FROM 
                    purchases_items p
                JOIN 
                    items i ON p.barcode = i.barcode
                JOIN 
                    supplier s ON i.supp_name = s.supp_name
                GROUP BY 
                    s.supp_name
                ORDER BY 
                    total_revenue DESC
                LIMIT 5;
            """,
            "requires_params": False
        },
        "Total Revenue from Book and Item Sales by Library Branch": {
            "query": """
                SELECT 
                    l.branchid,
                    COALESCE(SUM(bb.quantity * bfs.price), 0) AS book_sales_revenue,
                    COALESCE(SUM(pi.quantity * i.price), 0) AS item_sales_revenue,
                    COALESCE(SUM(bb.quantity * bfs.price), 0) + COALESCE(SUM(pi.quantity * i.price), 0) AS total_revenue
                FROM 
                    libraryy l
                LEFT JOIN buys_books bb ON l.branchid = bb.branchid
                LEFT JOIN books_for_sale bfs ON bb.isbn = bfs.isbn
                LEFT JOIN purchases_items pi ON l.branchid = pi.branchid
                LEFT JOIN items i ON pi.barcode = i.barcode
                GROUP BY l.branchid
                ORDER BY total_revenue DESC;
            """,
            "requires_params": False
        },
        "View Supplier Supply Summary": {
            "query": """
                SELECT * FROM Supplier_Supply_Summary;
            """,
            "requires_params": False
        }
    },
    "Staff & Inventory Management": {
        "Staff Managing Libraries with Highest Number of Items": {
            "query": """
                SELECT s.first_name, s.last_name, s.branchid, SUM(si.qty_stored) AS total_items
                FROM staff s
                JOIN stores_items si ON s.branchid = si.branchid
                WHERE s.post = 'Manager'
                GROUP BY s.first_name, s.last_name, s.branchid
                ORDER BY total_items DESC
                LIMIT 1;
            """,
            "requires_params": False
        },
        "Library Branches Running Low on Inventory": {
            "query": """
                SELECT si.branchid, l.address, SUM(si.qty_stored) AS total_items, SUM(sb.number_of_copies) AS total_books
                FROM stores_items si
                JOIN libraryy l ON si.branchid = l.branchid
                JOIN stores_booksforsale sb ON si.branchid = sb.branchid
                GROUP BY si.branchid, l.address
                HAVING SUM(si.qty_stored) + SUM(sb.number_of_copies) < 40;
            """,
            "requires_params": False
        },
        "Customers Who Borrowed and Bought the Same Book Title": {
            "query": """
                SELECT DISTINCT 
                    bo.username, 
                    bfr.title, 
                    bb.date_time AS purchase_date, 
                    bo.date_out AS borrow_date
                FROM 
                    borrows bo
                JOIN books_for_rent bfr ON bo.bookid = bfr.bookid
                JOIN buys_books bb ON bo.username = bb.username AND bfr.isbn = bb.isbn;
            """,
            "requires_params": False
        },
        "Retrieve Librarians Working the Most Hours Across All Branches": {
            "query": """
                SELECT s.first_name, s.last_name, s.branchid, s.hours
                FROM staff s
                WHERE s.post = 'Librarian'
                ORDER BY s.hours DESC
                LIMIT 5;
            """,
            "requires_params": False
        },
        "Check Book Availability": {
            "query": """
                SELECT check_book_availability(%s, %s);
            """,
            "requires_params": True,
            "params": ["Book Title", "Branch ID"]
        },
        "Calculate Total Inventory Value": {
            "query": """
                SELECT total_inventory_value(%s);
            """,
            "requires_params": True,
            "params": ["Branch ID"]
        },
        "Transfer Book Stock Between Branches": {
            "query": """
                CALL transfer_book_stock(%s, %s, %s, %s);
            """,
            "requires_params": True,
            "params": ["From Branch ID", "To Branch ID", "Book ISBN", "Transfer Quantity"]
        },
        "Track Borrowing Chains for a Book": {
            "query": """
                WITH RECURSIVE Borrowing_Chain AS (
                    -- Base Case: Get all borrowers of the book
                    SELECT 
                        b.username, 
                        c.first_name, 
                        c.last_name, 
                        b.bookid, 
                        b.date_out, 
                        b.due_date, 
                        b.penalty,
                        1 AS chain_level
                    FROM borrows b
                    JOIN customer c ON b.username = c.username
                    WHERE b.bookid = %s

                    UNION ALL

                    -- Recursive Case: Find the next borrower after the previous one returned the book
                    SELECT 
                        next_borrower.username, 
                        c.first_name, 
                        c.last_name, 
                        next_borrower.bookid, 
                        next_borrower.date_out, 
                        next_borrower.due_date, 
                        next_borrower.penalty,
                        bc.chain_level + 1
                    FROM borrows next_borrower
                    JOIN Borrowing_Chain bc 
                        ON next_borrower.bookid = bc.bookid 
                        AND next_borrower.date_out > bc.due_date
                    JOIN customer c ON next_borrower.username = c.username
                )
                SELECT 
                    username, 
                    first_name, 
                    last_name, 
                    bookid, 
                    date_out, 
                    due_date, 
                    penalty, 
                    chain_level
                FROM Borrowing_Chain
                ORDER BY chain_level, date_out;
            """,
            "requires_params": True,
            "params": ["Book ID (Format: ISBN#ID)"]
        }
    }
}

# Define tables for "View All" buttons per category
view_all_tables = {
    "Book Rentals & Branch Performance": ["authentication_system", "books_for_rent", "libraryy"],
    "Customer Insights": ["customer", "authentication_system"],
    "Supplier & Revenue Analysis": ["supplier", "publisher", "items", "books_for_sale"],
    "Staff & Inventory Management": ["staff", "dependents"],
}

# Sidebar for Navigation with Dropdown
st.sidebar.title("Navigation")
categories = list(query_categories.keys()) + ["Add Data", "About"]
selected_category = st.sidebar.selectbox("Select a Category", categories)

# Main Content Area
if selected_category not in ["About", "Add Data"]:
    st.header(f"🔍 {selected_category}")
    
    queries = query_categories[selected_category]
    
    # If the category has queries
    if queries:
        query_names = list(queries.keys())
        selected_query = st.selectbox("Select a Query", query_names)
        
        query_details = queries[selected_query]
        query_sql = query_details["query"]
        requires_params = query_details.get("requires_params", False)
        
        if requires_params:
            # Display input fields based on expected parameters
            with st.form(f"form_{selected_query.replace(' ', '_')}", clear_on_submit=True):
                params = {}
                for param in query_details.get("params", []):
                    if param == "Book Title":
                        params["book_title"] = st.text_input("Book Title")
                    elif param == "Branch ID":
                        params["branch_id"] = st.text_input("Branch ID")
                    elif param == "From Branch ID":
                        params["from_branch_id"] = st.text_input("From Branch ID")
                    elif param == "To Branch ID":
                        params["to_branch_id"] = st.text_input("To Branch ID")
                    elif param == "Book ISBN":
                        params["book_isbn"] = st.text_input("Book ISBN (13 characters)")
                    elif param == "Transfer Quantity":
                        params["transfer_qty"] = st.number_input("Transfer Quantity", min_value=1, step=1)
                    elif param == "Book ID (Format: ISBN#ID)":
                        params["book_id"] = st.text_input("Book ID (Format: ISBN#ID)")
                submit_button = st.form_submit_button("Execute")
            
            if submit_button:
                # Validate inputs
                missing_params = [p for p in params if not params[p]]
                if missing_params:
                    st.warning(f"Please provide: {', '.join(missing_params)}")
                else:
                    if selected_query == "Check Book Availability":
                        # Execute the function and display availability
                        df = run_query(query_sql, (params["book_title"], params["branch_id"]))
                        if not df.empty and df.iloc[0,0]:
                            availability = "Yes"
                        else:
                            availability = "No"
                        st.write(f"**Book Title:** {params['book_title']}")
                        st.write(f"**Branch ID:** {params['branch_id']}")
                        st.write(f"**Availability:** {availability}")
                    
                    elif selected_query == "Calculate Total Inventory Value":
                        # Execute the function and display total inventory value
                        df = run_query(query_sql, (params["branch_id"],))
                        if not df.empty:
                            total_value = df.iloc[0,0]
                            st.write(f"**Branch ID:** {params['branch_id']}")
                            st.write(f"**Total Inventory Value:** {total_value}")
                        else:
                            st.warning("No data returned.")
                    
                    elif selected_query == "Transfer Book Stock Between Branches":
                        # Call the stored procedure
                        call_procedure(proc_name="transfer_book_stock", params=(
                            params["from_branch_id"],
                            params["to_branch_id"],
                            params["book_isbn"],
                            params["transfer_qty"]
                        ))
                    
                    elif selected_query == "Track Borrowing Chains for a Book":
                        # Execute the recursive query and plot
                        df = run_query(query_sql, (params["book_id"],))
                        if not df.empty:
                            st.write(f"**Borrowing Chain for Book ID:** {params['book_id']}")
                            st.dataframe(df)
                            
                            # Plotting the borrowing chain
                            fig = px.bar(
                                df, 
                                x='chain_level', 
                                y='username', 
                                orientation='h',
                                title="Borrowing Chain Levels",
                                labels={'chain_level': 'Chain Level', 'username': 'Username'},
                                color='chain_level',
                                color_continuous_scale='Viridis'
                            )
                            fig.update_layout(showlegend=False)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("No borrowing chain data available for the provided Book ID.")
        
        else:
            # Queries that do not require parameters
            with st.form(f"form_{selected_query.replace(' ', '_')}", clear_on_submit=True):
                submit_button = st.form_submit_button("Run Query")
            
            if submit_button:
                df = run_query(query_sql)
                
                if not df.empty:
                    st.subheader(selected_query)
                    st.dataframe(df)
                    
                    # Plotting with Plotly for better customization
                    if selected_category == "Book Rentals & Branch Performance":
                        if selected_query == "Top 5 Borrowed Books in the Last Year":
                            if 'title' in df.columns and 'borrow_count' in df.columns:
                                fig = px.bar(
                                    df, 
                                    x='title', 
                                    y='borrow_count', 
                                    title="Top 5 Borrowed Books in the Last Year",
                                    labels={'title': 'Book Title', 'borrow_count': 'Borrow Count'},
                                    color='borrow_count',
                                    color_continuous_scale='Viridis'
                                )
                                fig.update_layout(showlegend=False)
                                st.plotly_chart(fig, use_container_width=True)
                        elif selected_query == "Branch with the Highest Number of Rentals":
                            if 'branchid' in df.columns and 'rentals_count' in df.columns:
                                fig = px.bar(
                                    df, 
                                    x='branchid', 
                                    y='rentals_count',
                                    title="Branch with the Highest Number of Rentals",
                                    labels={'branchid': 'Branch ID', 'rentals_count': 'Rentals Count'},
                                    color='rentals_count',
                                    color_continuous_scale='Blues'
                                )
                                fig.update_layout(showlegend=False)
                                st.plotly_chart(fig, use_container_width=True)
                    
                    elif selected_category == "Customer Insights":
                        if selected_query == "Categorize Customers into Segments":
                            if 'customer_segment' in df.columns:
                                segment_counts = df['customer_segment'].value_counts().reset_index()
                                segment_counts.columns = ['Customer Segment', 'Count']
                                fig = px.pie(
                                    segment_counts, 
                                    names='Customer Segment', 
                                    values='Count',
                                    title="Customer Segments",
                                    color='Customer Segment',
                                    color_discrete_sequence=px.colors.sequential.RdBu
                                )
                                st.plotly_chart(fig, use_container_width=True)
                        elif selected_query == "View Customers With Penalties":
                            if 'username' in df.columns and 'total_penalty' in df.columns:
                                fig = px.bar(
                                    df, 
                                    x='username', 
                                    y='total_penalty',
                                    title="Customers With Outstanding Penalties",
                                    labels={'username': 'Username', 'total_penalty': 'Total Penalty'},
                                    color='total_penalty',
                                    color_continuous_scale='Reds'
                                )
                                fig.update_layout(showlegend=False)
                                st.plotly_chart(fig, use_container_width=True)
                    
                    elif selected_category == "Supplier & Revenue Analysis":
                        if selected_query == "Top 5 Suppliers by Revenue":
                            if 'supp_name' in df.columns and 'total_revenue' in df.columns:
                                fig = px.bar(
                                    df, 
                                    x='supp_name', 
                                    y='total_revenue',
                                    title="Top 5 Suppliers by Revenue",
                                    labels={'supp_name': 'Supplier Name', 'total_revenue': 'Total Revenue'},
                                    color='total_revenue',
                                    color_continuous_scale='Greens'
                                )
                                fig.update_layout(showlegend=False)
                                st.plotly_chart(fig, use_container_width=True)
                        elif selected_query == "Total Revenue from Book and Item Sales by Library Branch":
                            if 'branchid' in df.columns and 'total_revenue' in df.columns:
                                fig = px.bar(
                                    df, 
                                    x='branchid', 
                                    y='total_revenue',
                                    title="Total Revenue from Book and Item Sales by Library Branch",
                                    labels={'branchid': 'Branch ID', 'total_revenue': 'Total Revenue'},
                                    color='total_revenue',
                                    color_continuous_scale='Oranges'
                                )
                                fig.update_layout(showlegend=False)
                                st.plotly_chart(fig, use_container_width=True)
                        elif selected_query == "View Supplier Supply Summary":
                            if 'supp_name' in df.columns and 'items_name' in df.columns and 'total_supplied' in df.columns:
                                fig = px.bar(
                                    df, 
                                    x='items_name', 
                                    y='total_supplied',
                                    color='supp_name',
                                    barmode='group',
                                    title="Supplier Supply Summary",
                                    labels={'items_name': 'Item Name', 'total_supplied': 'Total Supplied', 'supp_name': 'Supplier Name'},
                                    color_discrete_sequence=px.colors.qualitative.Set1
                                )
                                st.plotly_chart(fig, use_container_width=True)
                    
                    elif selected_category == "Staff & Inventory Management":
                        if selected_query == "Staff Managing Libraries with Highest Number of Items":
                            if 'branchid' in df.columns and 'total_items' in df.columns:
                                fig = px.bar(
                                    df, 
                                    x='branchid', 
                                    y='total_items',
                                    title="Staff Managing Libraries with Highest Number of Items",
                                    labels={'branchid': 'Branch ID', 'total_items': 'Total Items'},
                                    color='total_items',
                                    color_continuous_scale='Purples'
                                )
                                fig.update_layout(showlegend=False)
                                st.plotly_chart(fig, use_container_width=True)
                        elif selected_query == "Library Branches Running Low on Inventory":
                            if 'branchid' in df.columns and 'total_items' in df.columns:
                                fig = px.bar(
                                    df, 
                                    x='branchid', 
                                    y='total_items',
                                    title="Library Branches Running Low on Inventory",
                                    labels={'branchid': 'Branch ID', 'total_items': 'Total Items'},
                                    color='total_items',
                                    color_continuous_scale='Reds'
                                )
                                fig.update_layout(showlegend=False)
                                st.plotly_chart(fig, use_container_width=True)
                        elif selected_query == "Customers Who Borrowed and Bought the Same Book Title":
                            if 'username' in df.columns and 'title' in df.columns and 'purchase_date' in df.columns and 'borrow_date' in df.columns:
                                fig = px.scatter(
                                    df, 
                                    x='borrow_date', 
                                    y='purchase_date',
                                    color='username',
                                    hover_data=['title'],
                                    title="Customers Who Borrowed and Bought the Same Book Title",
                                    labels={'borrow_date': 'Borrow Date', 'purchase_date': 'Purchase Date'},
                                    color_discrete_sequence=px.colors.qualitative.Set2
                                )
                                st.plotly_chart(fig, use_container_width=True)
                        elif selected_query == "Retrieve Librarians Working the Most Hours Across All Branches":
                            if 'first_name' in df.columns and 'hours' in df.columns and 'branchid' in df.columns:
                                fig = px.bar(
                                    df, 
                                    x='first_name', 
                                    y='hours',
                                    color='branchid',
                                    title="Librarians Working the Most Hours",
                                    labels={'first_name': 'First Name', 'hours': 'Hours', 'branchid': 'Branch ID'},
                                    color_discrete_sequence=px.colors.qualitative.Dark2
                                )
                                fig.update_layout(showlegend=True)
                                st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No data available for the selected query.")
    
        # View All Tables Buttons with Toggle Functionality
        tables = view_all_tables.get(selected_category, [])
        if tables:
            st.subheader("🔍 View All Tables")
            for table in tables:
                toggle_key = f"toggle_{table}"
                if toggle_key not in st.session_state:
                    st.session_state[toggle_key] = False
                if st.button(f"View All {table.replace('_', ' ').title()}", key=f"button_{table}"):
                    st.session_state[toggle_key] = not st.session_state[toggle_key]
                if st.session_state[toggle_key]:
                    with st.expander(f"All Records from {table.replace('_', ' ').title()}"):
                        # Safely construct the SQL query with proper casing
                        view_all_query = sql.SQL("SELECT * FROM {}").format(sql.Identifier(table))
                        try:
                            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                                cur.execute(view_all_query)
                                records = cur.fetchall()
                                if records:
                                    df_all = pd.DataFrame(records)
                                    st.dataframe(df_all)
                                    
                                    # Optional: Add Plotly visualizations based on the table
                                    # (Include your plotting code here if needed)
                                else:
                                    st.warning(f"No data available in {table.replace('_', ' ').title()} table.")
                        except Exception as e:
                            st.error(f"Error fetching data from {table.replace('_', ' ').title()}: {e}")

elif selected_category == "Add Data":
    st.header("📝 Add Data")
    
    # Subcategories for adding data
    add_data_categories = [
        "Authentication_System",
        "Customer",
        "Libraryy",
        "Staff",
        "Dependents",
        "Supplier",
        "Publisher",
        "Items",
        "Books_for_Sale",
        "Books_for_Rent",
        "Authors_BookSale",
        "Authors_BookRent",
        "Stores_Items",
        "Stores_Booksforsale",
        "Buys_Books",
        "Purchases_Items",
        "Borrows",
        "Sale_to_Rent",
        "Update Borrows Status"
    ]
    
    selected_add_category = st.selectbox("Select a Table to Add/Update Data", add_data_categories)
    
    if selected_add_category == "Authentication_System":
        st.subheader("Add Authentication System Data")
        with st.form("add_authentication_system", clear_on_submit=True):
            email = st.text_input("Email")
            passcode = st.text_input("Passcode", type="password")
            submit = st.form_submit_button("Add")
        if submit:
            if email and passcode:
                # Encrypt the passcode using pgp_sym_encrypt
                insert_sql = """
                    INSERT INTO authentication_system (email, passcode)
                    VALUES (%s, pgp_sym_encrypt(%s, %s))
                    ON CONFLICT (email) 
                    DO NOTHING;
                """
                execute_query(insert_sql, (email, passcode, ENCRYPTION_KEY))
            else:
                st.warning("Please fill in all fields.")
    
    elif selected_add_category == "Customer":
        st.subheader("Add Customer Data")
        with st.form("add_customer", clear_on_submit=True):
            username = st.text_input("Username")
            phone_number = st.text_input("Phone Number (e.g., 12/345678)")
            address = st.text_area("Address")
            sex = st.selectbox("Sex", ["M", "F"])
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            ct_email = st.text_input("Ct_Email (Authentication_System Email)")
            submit = st.form_submit_button("Add")
        if submit:
            if username and phone_number and sex and first_name and last_name:
                insert_sql = """
                    INSERT INTO customer (username, phone_number, address, sex, first_name, last_name, ct_email)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (username) 
                    DO NOTHING;
                """
                execute_query(insert_sql, (username, phone_number, address, sex, first_name, last_name, ct_email))
            else:
                st.warning("Please fill in all required fields.")
    
    elif selected_add_category == "Libraryy":
        st.subheader("Add Library Branch Data")
        with st.form("add_libraryy", clear_on_submit=True):
            branch_id = st.text_input("Branch ID (e.g., LIBTECH01)")
            address = st.text_area("Address")
            phone_number = st.text_input("Phone Number (e.g., 12/345678)")
            submit = st.form_submit_button("Add")
        if submit:
            if branch_id and address and phone_number:
                insert_sql = """
                    INSERT INTO libraryy (branchid, address, phone_number)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (branchid) 
                    DO NOTHING;
                """
                execute_query(insert_sql, (branch_id, address, phone_number))
            else:
                st.warning("Please fill in all fields.")
    
    elif selected_add_category == "Staff":
        st.subheader("Add Staff Data")
        with st.form("add_staff", clear_on_submit=True):
            ssn = st.text_input("SSN")
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            dob = st.date_input("Date of Birth")
            blood_type = st.selectbox("Blood Type", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
            address = st.text_area("Address")
            salary = st.number_input("Salary", min_value=0.01, step=0.01)
            post = st.selectbox("Post", ["Manager", "Librarian", "Assistant"])
            super_ssn = st.text_input("Supervisor SSN")
            st_email = st.text_input("Staff Email (Authentication_System Email)")
            branch_id = st.text_input("Branch ID")
            hours = st.number_input("Hours Worked", min_value=0, step=1)
            submit = st.form_submit_button("Add")
        if submit:
            if ssn and first_name and last_name and blood_type and address and salary and post and st_email and branch_id and hours is not None:
                insert_sql = """
                    INSERT INTO staff (ssn, first_name, last_name, dob, blood_type, address, salary, post, super_ssn, st_email, branchid, hours)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ssn) 
                    DO NOTHING;
                """
                execute_query(insert_sql, (ssn, first_name, last_name, dob, blood_type, address, salary, post, super_ssn, st_email, branch_id, hours))
            else:
                st.warning("Please fill in all required fields.")
    
    elif selected_add_category == "Dependents":
        st.subheader("Add Dependents Data")
        with st.form("add_dependents", clear_on_submit=True):
            ssn = st.text_input("Staff SSN")
            dep_name = st.text_input("Dependent Name")
            relationship = st.selectbox("Relationship", ["Spouse", "Child", "Parent", "Other"])
            sex = st.selectbox("Sex", ["M", "F"])
            submit = st.form_submit_button("Add")
        if submit:
            if ssn and dep_name and relationship and sex:
                insert_sql = """
                    INSERT INTO dependents (ssn, dep_name, relationship, sex)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (ssn, dep_name) 
                    DO NOTHING;
                """
                execute_query(insert_sql, (ssn, dep_name, relationship, sex))
            else:
                st.warning("Please fill in all fields.")
    
    elif selected_add_category == "Supplier":
        st.subheader("Add Supplier Data")
        with st.form("add_supplier", clear_on_submit=True):
            supp_name = st.text_input("Supplier Name")
            address = st.text_area("Address")
            phone_number = st.text_input("Phone Number (e.g., 12/345678)")
            submit = st.form_submit_button("Add")
        if submit:
            if supp_name and address and phone_number:
                insert_sql = """
                    INSERT INTO supplier (supp_name, address, phone_number)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (supp_name, address) 
                    DO NOTHING;
                """
                execute_query(insert_sql, (supp_name, address, phone_number))
            else:
                st.warning("Please fill in all fields.")
    
    elif selected_add_category == "Publisher":
        st.subheader("Add Publisher Data")
        with st.form("add_publisher", clear_on_submit=True):
            publisher_name = st.text_input("Publisher Name")
            address = st.text_area("Address")
            phone_number = st.text_input("Phone Number (e.g., 12/345678)")
            submit = st.form_submit_button("Add")
        if submit:
            if publisher_name and address and phone_number:
                insert_sql = """
                    INSERT INTO publisher (publisher_name, address, phone_number)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (publisher_name) 
                    DO NOTHING;
                """
                execute_query(insert_sql, (publisher_name, address, phone_number))
            else:
                st.warning("Please fill in all fields.")
    
    elif selected_add_category == "Items":
        st.subheader("Add Items Data")
        with st.form("add_items", clear_on_submit=True):
            barcode = st.text_input("Barcode")
            items_name = st.text_input("Item Name")
            age_group = st.text_input("Age Group")
            price = st.number_input("Price", min_value=0.01, step=0.01)
            genre = st.text_input("Genre")
            supp_name = st.text_input("Supplier Name")
            supp_address = st.text_input("Supplier Address")
            qty_supplied = st.number_input("Quantity Supplied", min_value=0, step=1)
            date_supplied = st.date_input("Date Supplied")
            submit = st.form_submit_button("Add")
        if submit:
            if barcode and items_name and price:
                insert_sql = """
                    INSERT INTO items (barcode, items_name, age_group, price, genre, supp_name, supp_address, qty_supplied, date_supplied)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (barcode) 
                    DO NOTHING;
                """
                execute_query(insert_sql, (barcode, items_name, age_group, price, genre, supp_name, supp_address, qty_supplied, date_supplied))
            else:
                st.warning("Please fill in all required fields.")
    
    elif selected_add_category == "Books_for_Sale":
        st.subheader("Add Books for Sale Data")
        with st.form("add_books_for_sale", clear_on_submit=True):
            isbn = st.text_input("ISBN (13 characters)")
            title = st.text_input("Title")
            genre = st.text_input("Genre")
            price = st.number_input("Price", min_value=0.01, step=0.01)
            translator = st.text_input("Translator")
            edition = st.number_input("Edition", min_value=1, step=1)
            pages = st.number_input("Pages", min_value=1, step=1)
            lang = st.text_input("Language")
            publisher_name = st.text_input("Publisher Name")
            submit = st.form_submit_button("Add")
        if submit:
            if isbn and title and genre and price and edition and pages and lang:
                insert_sql = """
                    INSERT INTO books_for_sale (isbn, title, genre, price, translator, edition, pages, lang, publisher_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (isbn) 
                    DO NOTHING;
                """
                execute_query(insert_sql, (isbn, title, genre, price, translator, edition, pages, lang, publisher_name))
            else:
                st.warning("Please fill in all required fields.")
    
    elif selected_add_category == "Books_for_Rent":
        st.subheader("Add Books for Rent Data")
        with st.form("add_books_for_rent", clear_on_submit=True):
            book_id = st.text_input("Book ID (Format: ISBN#ID)")
            isbn = st.text_input("ISBN (13 characters)")
            title = st.text_input("Title")
            genre = st.text_input("Genre")
            price = st.number_input("Price", min_value=0.01, step=0.01)
            translator = st.text_input("Translator")
            edition = st.number_input("Edition", min_value=1, step=1)
            pages = st.number_input("Pages", min_value=1, step=1)
            lang = st.text_input("Language")
            publisher_name = st.text_input("Publisher Name")
            shelf_no = st.number_input("Shelf Number", min_value=1, step=1)
            row_no = st.number_input("Row Number", min_value=1, step=1)
            branch_id = st.text_input("Branch ID")
            submit = st.form_submit_button("Add")
        if submit:
            if book_id and isbn and title and genre and price and edition and pages and lang and shelf_no and row_no and branch_id:
                insert_sql = """
                    INSERT INTO books_for_rent (bookid, isbn, title, genre, price, translator, edition, pages, lang, publisher_name, shelf_no, row_no, branchid)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (bookid) 
                    DO NOTHING;
                """
                execute_query(insert_sql, (book_id, isbn, title, genre, price, translator, edition, pages, lang, publisher_name, shelf_no, row_no, branch_id))
            else:
                st.warning("Please fill in all required fields.")
    
    elif selected_add_category == "Authors_BookSale":
        st.subheader("Add Authors for Book Sale Data")
        with st.form("add_authors_booksale", clear_on_submit=True):
            isbn = st.text_input("ISBN (13 characters)")
            author_name = st.text_input("Author Name")
            submit = st.form_submit_button("Add")
        if submit:
            if isbn and author_name:
                insert_sql = """
                    INSERT INTO authors_booksale (isbn, author_name)
                    VALUES (%s, %s)
                    ON CONFLICT (isbn, author_name) 
                    DO NOTHING;
                """
                execute_query(insert_sql, (isbn, author_name))
            else:
                st.warning("Please fill in all fields.")
    
    elif selected_add_category == "Authors_BookRent":
        st.subheader("Add Authors for Book Rent Data")
        with st.form("add_authors_bookrent", clear_on_submit=True):
            book_id = st.text_input("Book ID (Format: ISBN#ID)")
            author_name = st.text_input("Author Name")
            submit = st.form_submit_button("Add")
        if submit:
            if book_id and author_name:
                insert_sql = """
                    INSERT INTO authors_bookrent (bookid, author_name)
                    VALUES (%s, %s)
                    ON CONFLICT (bookid, author_name) 
                    DO NOTHING;
                """
                execute_query(insert_sql, (book_id, author_name))
            else:
                st.warning("Please fill in all fields.")
    
    elif selected_add_category == "Stores_Items":
        st.subheader("Add Stores Items Data")
        with st.form("add_stores_items", clear_on_submit=True):
            branch_id = st.text_input("Branch ID")
            barcode = st.text_input("Barcode")
            qty_stored = st.number_input("Quantity Stored", min_value=0, step=1)
            submit = st.form_submit_button("Add")
        if submit:
            if branch_id and barcode and qty_stored is not None:
                insert_sql = """
                    INSERT INTO stores_items (branchid, barcode, qty_stored)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (branchid, barcode) 
                    DO UPDATE SET qty_stored = stores_items.qty_stored + EXCLUDED.qty_stored;
                """
                execute_query(insert_sql, (branch_id, barcode, qty_stored))
            else:
                st.warning("Please fill in all fields.")
    
    elif selected_add_category == "Stores_Booksforsale":
        st.subheader("Add Stores Booksforsale Data")
        with st.form("add_stores_booksforsale", clear_on_submit=True):
            branch_id = st.text_input("Branch ID")
            isbn = st.text_input("ISBN (13 characters)")
            number_of_copies = st.number_input("Number of Copies", min_value=0, step=1)
            submit = st.form_submit_button("Add")
        if submit:
            if branch_id and isbn and number_of_copies is not None:
                insert_sql = """
                    INSERT INTO stores_booksforsale (branchid, isbn, number_of_copies)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (branchid, isbn) 
                    DO UPDATE SET number_of_copies = stores_booksforsale.number_of_copies + EXCLUDED.number_of_copies;
                """
                execute_query(insert_sql, (branch_id, isbn, number_of_copies))
            else:
                st.warning("Please fill in all fields.")
    
    elif selected_add_category == "Buys_Books":
        st.subheader("Add Buys Books Data")
        with st.form("add_buys_books", clear_on_submit=True):
            username = st.text_input("Username")
            branch_id = st.text_input("Branch ID")
            isbn = st.text_input("ISBN (13 characters)")
            quantity = st.number_input("Quantity", min_value=0, step=1)
            date_time = st.date_input("Date and Time")
            submit = st.form_submit_button("Add")
        if submit:
            if username and branch_id and isbn and quantity is not None and date_time:
                insert_sql = """
                    INSERT INTO buys_books (username, branchid, isbn, quantity, date_time)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (username, branchid, isbn, date_time) 
                    DO NOTHING;
                """
                execute_query(insert_sql, (username, branch_id, isbn, quantity, date_time))
            else:
                st.warning("Please fill in all required fields.")
    
    elif selected_add_category == "Purchases_Items":
        st.subheader("Add Purchases Items Data")
        with st.form("add_purchases_items", clear_on_submit=True):
            username = st.text_input("Username")
            branch_id = st.text_input("Branch ID")
            barcode = st.text_input("Barcode")
            quantity = st.number_input("Quantity", min_value=0, step=1)
            date_time = st.date_input("Date and Time")
            submit = st.form_submit_button("Add")
        if submit:
            if username and branch_id and barcode and quantity is not None and date_time:
                insert_sql = """
                    INSERT INTO purchases_items (username, branchid, barcode, quantity, date_time)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (username, branchid, barcode, date_time) 
                    DO NOTHING;
                """
                execute_query(insert_sql, (username, branch_id, barcode, quantity, date_time))
            else:
                st.warning("Please fill in all required fields.")
    
    elif selected_add_category == "Borrows":
        st.subheader("Add Borrows Data")
        with st.form("add_borrows", clear_on_submit=True):
            username = st.text_input("Username")
            book_id = st.text_input("Book ID (Format: ISBN#ID)")
            date_out = st.date_input("Date Out")
            due_date = st.date_input("Due Date")
            penalty = st.number_input("Penalty", min_value=0.0, step=0.01)
            status = st.selectbox("Status", ["Borrowed", "Returned"])
            submit = st.form_submit_button("Add")
        if submit:
            if username and book_id and date_out and due_date and status:
                insert_sql = """
                    INSERT INTO borrows (username, bookid, date_out, due_date, penalty, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (username, bookid, date_out) 
                    DO NOTHING;
                """
                execute_query(insert_sql, (username, book_id, date_out, due_date, penalty, status))
            else:
                st.warning("Please fill in all required fields.")
    
    elif selected_add_category == "Sale_to_Rent":
        st.subheader("Add Sale to Rent Data")
        with st.form("add_sale_to_rent", clear_on_submit=True):
            book_id = st.text_input("Book ID (Format: ISBN#ID)")
            isbn = st.text_input("ISBN (13 characters)")
            date_moved = st.date_input("Date Moved")
            discount = st.number_input("Discount (%)", min_value=0.0, max_value=100.0, step=0.01)
            submit = st.form_submit_button("Add")
        if submit:
            if book_id and isbn and date_moved is not None:
                insert_sql = """
                    INSERT INTO sale_to_rent (bookid, isbn, date_moved, discount)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (bookid, isbn) 
                    DO NOTHING;
                """
                execute_query(insert_sql, (book_id, isbn, date_moved, discount))
            else:
                st.warning("Please fill in all required fields.")
    
    elif selected_add_category == "Update Borrows Status":
        st.subheader("Update Borrows Status")
        with st.form("update_borrows_status_form", clear_on_submit=True):
            username = st.text_input("Username")
            book_id = st.text_input("Book ID (Format: ISBN#ID)")
            date_out = st.date_input("Date Out")
            new_status = st.selectbox("New Status", ["Borrowed", "Returned"])
            submit = st.form_submit_button("Update Status")
        if submit:
            if username and book_id and date_out and new_status:
                update_sql = """
                    UPDATE borrows
                    SET status = %s
                    WHERE username = %s AND bookid = %s AND date_out = %s;
                """
                execute_query(update_sql, (new_status, username, book_id, date_out))
                st.success("Borrow status updated successfully.")
            else:
                st.warning("Please fill in all required fields.")



# About Section
elif selected_category == "About":
    st.header("ℹ️ About")
    st.markdown("""
    ### LibTech Database GUI

    This application provides a user-friendly interface to interact with our LibTech database using predefined queries, views, functions, and stored procedures. 
    This database is part of our EECE433 project that is prepared for Prof. Hussein Bakri.

    #### Features:
    - **Book Rentals & Branch Performance:** Analyze top borrowed books, branch rentals, and overdue books.
    - **Customer Insights:** Understand customer spending, segmentation, and purchasing behaviors.
    - **Supplier & Revenue Analysis:** Evaluate supplier performance and overall revenue by branch.
    - **Staff & Inventory Management:** Manage staff performance and monitor inventory levels.
    - **Interactive Visualizations:** View data in tables and charts with colors and legends for better insights.
    - **View All Tables:** Easily view complete data from key tables in the database.
    - **Advanced Operations:** Perform operations like checking book availability, calculating inventory value, transferring book stock between branches, and tracking borrowing chains.
    - **Add Data:** Insert new records into the database and update existing ones.
    - **Security Mechanisms:** Enhanced security with encryption of passwords.
    #### How to Use:
    1. **Select a Category:** Use the sidebar to navigate between different query categories.
    2. **Choose a Query:** Within each category, select the specific query you want to execute from the dropdown.
    3. **Run Query:** Click the "Run Query" button to execute and view results along with visualizations.
    4. **View All Tables:** Click on the "View All [Table]" buttons to see complete data from specific tables.
    5. **Add Data:** Navigate to the "Add Data" section to insert new records into the database and update existing ones.
    6. **Track Borrowing Chains:** Use the dedicated form to track the borrowing history of a specific book.

    #### Setup Instructions:
    1. **Clone the Repository:** [Your Repository Link]
    2. **Install Dependencies:** `pip install -r requirements.txt`
    3. **Configure Database Connection:** Ensure the connection parameters in `app.py` are correct or use `secrets.toml`.
    4. **Run the App:** `streamlit run app.py`

    #### Contact:
    For any questions or support, please contact our Team Leader [myh17@mail.aub.edu].

    #### Always make sure to enjoy the journey
    ~ Mohamad Hamdan ~ Tia El Khoury ~ Zakaria Labban
    """)
