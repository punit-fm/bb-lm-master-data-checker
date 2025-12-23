"""
Streamlit PostgreSQL Data Viewer
A modern web application to fetch and display data from PostgreSQL databases.
"""

import streamlit as st
import pandas as pd
from database.db_utils import (
    test_connection,
    get_table_list,
    get_table_data,
    get_table_info,
    get_fund_datagroup_matrix,
    get_fund_datagroup_details,
    get_fund_datagroup_key_matrix,
    get_missing_descriptions_stats,
    close_all_connections
)

# Page configuration
st.set_page_config(
    page_title="Fund-Datagroup Matrix Viewer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern styling
st.markdown("""
    <style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main container */
    .main {
        background: black;
        padding: 1rem;
    }
    
    /* Card styling */
    .stApp {
        background: black;
    }
    
    /* Header styling */
    h1 {
        color: #ffffff;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 0.5rem;
    }
    
    h2, h3 {
        color: #ffffff;
        font-weight: 600;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: white;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background-color: rgba(255,255,255,0.9);
        border-radius: 8px;
    }
    
    /* DataFrame styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 8px;
        backdrop-filter: blur(10px);
        background-color: rgba(255,255,255,0.9) !important;
    }
    
    /* Success/Error messages */
    .element-container div[data-testid="stMarkdownContainer"] p {
        color: #ffffff;
    }
    
    /* Card container */
    .card {
        background: rgba(255,255,255,0.95);
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    /* Status indicator */
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }
    
    .status-connected {
        background-color: #10b981;
    }
    
    .status-disconnected {
        background-color: #ef4444;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Loading animation */
    .stSpinner > div {
        border-color: #667eea !important;
    }
    </style>
""", unsafe_allow_html=True)


def format_formula(formula):
    """
    Format a formula string with indentation and line breaks for better readability.
    """
    if not formula:
        return ""
    
    # Basic indentation logic
    formatted = ""
    indent_level = 0
    lines = []
    current_line = ""
    
    # Tokenize simple parts (this is a basic heuristic)
    formula = str(formula).replace("\n", " ").strip()
    
    i = 0
    while i < len(formula):
        char = formula[i]
        
        if char == '(':
            lines.append("  " * indent_level + current_line.strip() + "(")
            current_line = ""
            indent_level += 1
        elif char == ')':
            if current_line.strip():
                lines.append("  " * indent_level + current_line.strip())
            indent_level -= 1
            lines.append("  " * indent_level + ")")
            current_line = ""
        elif char == ',':
            lines.append("  " * indent_level + current_line.strip() + ",")
            current_line = ""
        else:
            current_line += char
        i += 1
        
    if current_line.strip():
        lines.append("  " * indent_level + current_line.strip())
        
    return "\n".join([line for line in lines if line.strip()])


def main():
    """Main application function."""
    
    # Header
    st.markdown("# Fund-Datagroup Matrix Viewer")
    
    # Main content
    try:
        # Test connection first
        success, message = test_connection()
        
        # Connection status
        col1, col2 = st.columns([3, 1])
        with col1:
            if success:
                st.markdown(
                    '<span class="status-indicator status-connected"></span>'
                    '<span style="color: white; font-weight: 600;">Connected to Database</span>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<span class="status-indicator status-disconnected"></span>'
                    '<span style="color: white; font-weight: 600;">Not Connected</span>',
                    unsafe_allow_html=True
                )
        
        if not success:
            st.error(f"⚠️ {message}")
            st.info("💡 Please check your `.env` file and ensure database credentials are correct.")
            return
        
        # Main section: Fund-Datagroup Matrix
        try:
            # Load reviewed items
            from review_tracker import load_reviewed_items, save_reviewed_item
            reviewed_items = load_reviewed_items()
            
            with st.spinner("Loading matrices..."):
                matrix_df = get_fund_datagroup_matrix()
                key_matrix_df = get_fund_datagroup_key_matrix()
                description_stats = get_missing_descriptions_stats()
            
            if matrix_df.empty:
                st.warning("No fund-datagroup data found. Please check if the tables `lm_funds` and `lm_datagroup_metadata_master` exist and contain data.")
            else:
                # Reset index to get fund_id and fund_name as columns
                matrix_df_display = matrix_df.reset_index()
                
                # Convert all numeric columns to integers (remove decimals)
                for col in matrix_df_display.columns:
                    if col not in ['fund_name']:  # Skip fund_name column
                        matrix_df_display[col] = matrix_df_display[col].apply(
                            lambda x: int(x) if pd.notna(x) and x != '' else x
                        )
                
                # Add S.No as first column
                matrix_df_display.insert(0, 'S.No', range(1, len(matrix_df_display) + 1))
                
                # Display metrics
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("🏢 Total Funds", len(matrix_df))
                with col2:
                    st.metric("📋 Total Datagroups", len(matrix_df.columns))
                with col3:
                    st.metric("✅ Reviewed", len(reviewed_items))
                with col4:
                    st.metric("📊 Total Records", description_stats['datagroup_total'])
                with col5:
                    st.metric("⚠️ No Description", description_stats['datagroup_missing'])
                
                st.markdown("### Fund-Datagroup Grid")
                st.markdown("*Rows represent funds, columns represent datagroups. Numbers show the datagroup metadata ID.*")
                st.markdown("*🟢 Green: Has key metadata | 🟠 Orange: Missing key metadata | ⚪ Grey: Reviewed*")
                
                # Checkbox to toggle reviewed highlighting
                show_reviewed = st.checkbox("Show Reviewed Status", value=True, help="If enabled, reviewed cells will be shown in grey. Otherwise, they will show their status (Green/Orange).")
                
                # Create a comparison matrix to check if key metadata exists
                # Reset key matrix index for comparison
                if not key_matrix_df.empty:
                    key_matrix_df_reset = key_matrix_df.reset_index()
                else:
                    key_matrix_df_reset = pd.DataFrame()
                
                def apply_conditional_styling(row):
                    """Apply styling to entire row based on comparison with key matrix and review status"""
                    styles = [''] * len(row)
                    
                    # Get fund_id and fund_name from this row
                    fund_id = row.get('fund_id')
                    fund_name = row.get('fund_name')
                    
                    # Find matching row in key matrix
                    if not key_matrix_df_reset.empty and fund_id is not None:
                        key_row = key_matrix_df_reset[
                            (key_matrix_df_reset['fund_id'] == fund_id) & 
                            (key_matrix_df_reset['fund_name'] == fund_name)
                        ]
                    else:
                        key_row = pd.DataFrame()
                    
                    # Apply styling to each datagroup column
                    for idx, col in enumerate(row.index):
                        if col not in ['S.No', 'fund_id', 'fund_name']:
                            val = row[col]
                            if val != '' and str(val) != 'nan' and pd.notna(val):
                                # Check if this combination is reviewed
                                is_reviewed_item = (fund_name, col) in reviewed_items
                                
                                if show_reviewed and is_reviewed_item:
                                    # Grey for reviewed items
                                    styles[idx] = 'background-color: #9ca3af; color: white; font-weight: bold;'
                                else:
                                    # Check if this datagroup has key metadata
                                    has_key_metadata = False
                                    if not key_row.empty and col in key_row.columns:
                                        key_val = key_row[col].iloc[0]
                                        has_key_metadata = (key_val != '' and str(key_val) != 'nan' and pd.notna(key_val))
                                    
                                    if has_key_metadata:
                                        styles[idx] = 'background-color: #10b981; color: white; font-weight: bold;'  # Green
                                    else:
                                        styles[idx] = 'background-color: #f97316; color: white; font-weight: bold;'  # Orange
                    
                    return styles
                
                # Display the matrix with conditional styling
                styled_df = matrix_df_display.style.apply(apply_conditional_styling, axis=1)
                
                st.dataframe(
                    styled_df,
                    use_container_width=True,
                    height=min(600, len(matrix_df_display) * 35 + 50)
                )
        
        except Exception as e:
            st.error(f"❌ Error loading fund-datagroup matrix: {str(e)}")
            st.info("💡 Make sure the tables `lm_funds` and `lm_datagroup_metadata_master` exist in your database.")
        
        # Second Matrix: Key Metadata Matrix
        st.markdown("---")
        
        try:
            if key_matrix_df.empty:
                st.warning("No key metadata found. Please check if the table `lm_key_metadata_master` exists and contains data.")
            else:
                # Reset index to get fund_id and fund_name as columns
                key_matrix_df_display = key_matrix_df.reset_index()
                
                # Convert all numeric columns to integers (remove decimals)
                for col in key_matrix_df_display.columns:
                    if col not in ['fund_name']:  # Skip fund_name column
                        key_matrix_df_display[col] = key_matrix_df_display[col].apply(
                            lambda x: int(x) if pd.notna(x) and x != '' else x
                        )
                
                # Add S.No as first column
                key_matrix_df_display.insert(0, 'S.No', range(1, len(key_matrix_df_display) + 1))
                
                # Display metrics in two rows for better readability
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🏢 Total Funds", len(key_matrix_df))
                with col2:
                    st.metric("📋 Total Datagroups", len(key_matrix_df.columns))
                with col3:
                    st.metric("📊 Total Records", description_stats['key_total'])
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("⚠️ No Description", description_stats['key_missing'])
                with col2:
                    st.metric("🧱 Raw Keys", description_stats['key_raw'])
                with col3:
                    st.metric("🧮 Calculated", description_stats['key_calculated'])
                with col4:
                    st.metric("❌ Missing Formula", description_stats['key_missing_formula'])
                
                st.markdown("### Key Metadata Grid")
                st.markdown("*Rows represent funds, columns represent datagroups. Numbers show the count of keys defined for each fund-datagroup combination.*")
                
                # Apply styling function
                def highlight_cells(val):
                    """Apply green background to cells with data"""
                    if val != '' and str(val) != 'nan' and pd.notna(val):
                        return 'background-color: #10b981; color: white; font-weight: bold;'
                    return ''
                
                # Display the matrix with styling
                styled_key_df = key_matrix_df_display.style.applymap(
                    highlight_cells,
                    subset=key_matrix_df_display.columns[3:]  # Apply to all columns except S.No, fund_id, and fund_name
                )
                
                st.dataframe(
                    styled_key_df,
                    use_container_width=True,
                    height=min(600, len(key_matrix_df_display) * 35 + 50)
                )
                
                # Interactive selection for detailed view
                st.markdown("---")
                st.markdown("### 🔍 View Key Metadata Details")
                st.markdown("*Select a fund and datagroup to view detailed key metadata information*")
                st.markdown("*Review formula, is_raw, is_calculated, data_type, unit, description, calculation_level, key_display_name*")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    # Create fund display names: "Fund Name (Fund ID)"
                    fund_options = []
                    fund_id_map = {} # Maps display name back to actual fund name
                    
                    # Get unique fund_id and fund_name pairs from matrix_df
                    fund_info = matrix_df.index.to_frame(index=False)
                    for _, row in fund_info.iterrows():
                        display_name = f"{row['fund_name']} ({int(row['fund_id'])})"
                        fund_options.append(display_name)
                        fund_id_map[display_name] = (row['fund_name'], row['fund_id'])
                    
                    selected_fund_display = st.selectbox(
                        "Select Fund:",
                        options=fund_options,
                        key="detail_fund_selector"
                    )
                    selected_fund, selected_fund_id = fund_id_map.get(selected_fund_display, (None, None))
                
                with col2:
                    # Get list of datagroups (columns excluding S.No, fund_id, fund_name)
                    datagroup_columns = [col for col in matrix_df.columns]
                    
                    # Create datagroup display names with IDs for the selected fund
                    datagroup_options = []
                    datagroup_name_map = {} # Maps display name back to actual datagroup name
                    
                    if selected_fund is not None:
                        # Get the row for the selected fund from matrix_df (which contains the datagroup metadata IDs)
                        fund_row = matrix_df.loc[(selected_fund_id, selected_fund)]
                        
                        for dg_name in datagroup_columns:
                            dg_id = fund_row[dg_name]
                            if dg_id != '' and pd.notna(dg_id):
                                display_name = f"{dg_name} ({int(dg_id)})"
                                datagroup_options.append(display_name)
                                datagroup_name_map[display_name] = dg_name
                    
                    selected_datagroup_display = st.selectbox(
                        "Select Datagroup:",
                        options=datagroup_options,
                        key="detail_datagroup_selector"
                    )
                    selected_datagroup = datagroup_name_map.get(selected_datagroup_display)
                
                with col3:
                    reviewer_name = st.text_input(
                        "Reviewer Name:",
                        key="reviewer_name_input",
                        placeholder="Enter your name"
                    )
                
                # Mark as reviewed button
                col1, col2 = st.columns([4, 1])
                with col2:
                    if st.button("✅ Mark Reviewed", use_container_width=True):
                        if selected_fund and selected_datagroup and reviewer_name:
                            if save_reviewed_item(selected_fund, selected_datagroup, reviewer_name):
                                st.success(f"Marked **{selected_fund}** - **{selected_datagroup}** as reviewed by **{reviewer_name}**!")
                                st.rerun()
                            else:
                                st.info("This combination is already marked as reviewed.")
                        elif not reviewer_name:
                            st.warning("Please enter reviewer name.")
                
                # Display review details if the selected combination is reviewed
                if selected_fund and selected_datagroup:
                    from review_tracker import get_review_details
                    review_details = get_review_details(selected_fund, selected_datagroup)
                    
                    if review_details:
                        st.markdown("---")
                        st.markdown("### 📝 Review Details")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown(f"**Fund:** {review_details['fund_name']}")
                        with col2:
                            st.markdown(f"**Datagroup:** {review_details['datagroup_name']}")
                        with col3:
                            st.markdown(f"**Status:** ✅ Reviewed")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Reviewed by:** {review_details.get('reviewer_name', 'Unknown')}")
                        with col2:
                            reviewed_at = review_details.get('reviewed_at', '')
                            if reviewed_at:
                                from datetime import datetime
                                try:
                                    dt = datetime.fromisoformat(reviewed_at)
                                    formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                                    st.markdown(f"**Reviewed at:** {formatted_date}")
                                except:
                                    st.markdown(f"**Reviewed at:** {reviewed_at}")
                
                # Fetch and display detailed key metadata
                    with st.spinner("Loading key metadata details..."):
                        from database.db_utils import get_key_metadata_details
                        details_df = get_key_metadata_details(selected_fund, selected_datagroup)
                    
                    if not details_df.empty:
                        st.markdown(f"#### Key Metadata for **{selected_fund}** - **{selected_datagroup}**")
                        st.markdown(f"*Found {len(details_df)} key(s)*")
                        
                        # Display the details table with selection enabled
                        selection_event = st.dataframe(
                            details_df,
                            use_container_width=True,
                            height=min(400, len(details_df) * 35 + 50),
                            on_select="rerun",
                            selection_mode="single-row"
                        )
                        
                        # Show formula if a row is selected
                        if selection_event and selection_event.selection and selection_event.selection.rows:
                            selected_row_idx = selection_event.selection.rows[0]
                            selected_row = details_df.iloc[selected_row_idx]
                            formula = selected_row.get('formula')
                            key_name = selected_row.get('key_display_name')
                            
                            st.markdown("---")
                            st.markdown(f"#### 🧪 Visual Formula Viewer: **{key_name}**")
                            
                            if formula:
                                formatted_formula = format_formula(formula)
                                st.info("Formatted Formula Structure:")
                                st.code(formatted_formula, language="sql")
                                
                                # Show original as well for reference
                                with st.expander("Show Original Formula"):
                                    st.text(formula)
                            else:
                                st.warning("No formula defined for this key.")
                    else:
                        st.info(f"No key metadata found for **{selected_fund}** - **{selected_datagroup}**")
        
        except Exception as e:
            st.error(f"❌ Error loading key metadata matrix: {str(e)}")
            st.info("💡 Make sure the table `lm_key_metadata_master` exists in your database.")
    
    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
        st.info("💡 Please check your database connection and try again.")
    
    finally:
        # Cleanup (optional - connection pool will handle this)
        pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        st.info("Application stopped by user.")
        close_all_connections()
