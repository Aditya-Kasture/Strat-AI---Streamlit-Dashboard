import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re
from datetime import datetime
import io


# ===== CONFIGURATION =====
st.set_page_config(page_title="KPI Dashboard - Strat AI Solutions", layout="wide")


# ===== FILENAME VALIDATION =====
def is_valid_filename(fname):
    """
    Validates filename against pattern: <ClientName>_<DealID>_<DocType>_<YYYYMMDD>.<ext>
    Example: AcmeCorp_DEAL123_IDProof_20251005.pdf
    """
    pattern = r'^[A-Za-z0-9]+_[A-Za-z0-9]+_[A-Za-z]+_\d{8}\.(pdf|jpg|png|docx)$'
    return bool(re.match(pattern, fname))


def parse_filename(fname):
    """Extract components from valid filename"""
    if not is_valid_filename(fname):
        return None
    parts = fname.split('_')
    date_ext = parts[3].split('.')
    return {
        'client': parts[0],
        'deal_id': parts[1],
        'doc_type': parts[2],
        'date': date_ext[0],
        'extension': date_ext[1]
    }


# ===== DATA LOADING WITH TEST SCENARIOS =====
def load_log_data(test_scenario='happy_path'):
    """
    Load synthetic test data for different scenarios
    test_scenario options: 'happy_path', 'missing_docs', 'rename', 'error_retry'
    """
    
    if test_scenario == 'happy_path':
        # All metrics optimal, no issues
        data = {
            'Date': ['2025-10-01', '2025-10-02', '2025-10-03', '2025-10-04', '2025-10-05'],
            'Client': ['AcmeCorp', 'BetaTech', 'Zenith', 'AcmeCorp', 'BetaTech'],
            'DealID': ['DEAL123', 'DEAL007', 'DEAL221', 'DEAL123', 'DEAL007'],
            'Doc_Cycle_Time': [5, 4, 3, 3, 2],  # Improving
            'Run_Success_Rate': [0.95, 0.97, 0.98, 0.99, 1.0],  # Perfect
            'Missing_Items': [0, 0, 0, 0, 0],  # None missing
            'Onboarding_Duration': [24, 20, 18, 16, 12],  # Fast
            'Status': ['GREEN', 'GREEN', 'GREEN', 'GREEN', 'GREEN']
        }
    
    elif test_scenario == 'missing_docs':
        # High missing items, lower success rates
        data = {
            'Date': ['2025-10-01', '2025-10-02', '2025-10-03', '2025-10-04', '2025-10-05'],
            'Client': ['AcmeCorp', 'BetaTech', 'Zenith', 'AcmeCorp', 'BetaTech'],
            'DealID': ['DEAL123', 'DEAL007', 'DEAL221', 'DEAL456', 'DEAL789'],
            'Doc_Cycle_Time': [15, 18, 20, 22, 25],  # Worsening
            'Run_Success_Rate': [0.60, 0.55, 0.50, 0.45, 0.40],  # Declining
            'Missing_Items': [8, 10, 12, 15, 18],  # Increasing
            'Onboarding_Duration': [72, 84, 96, 108, 120],  # Very slow
            'Status': ['RED', 'RED', 'RED', 'RED', 'RED']
        }
    
    elif test_scenario == 'rename':
        # Files with naming issues requiring renaming
        data = {
            'Date': ['2025-10-01', '2025-10-02', '2025-10-03', '2025-10-04', '2025-10-05'],
            'Client': ['AcmeCorp', 'AcmeCorp', 'BetaTech', 'Zenith', 'Zenith'],
            'DealID': ['DEAL123', 'DEAL123', 'DEAL007', 'DEAL221', 'DEAL221'],
            'Doc_Cycle_Time': [12, 10, 8, 6, 5],  # Improving after fixes
            'Run_Success_Rate': [0.70, 0.75, 0.82, 0.90, 0.95],  # Recovering
            'Missing_Items': [5, 4, 3, 1, 0],  # Decreasing
            'Onboarding_Duration': [60, 50, 40, 30, 24],  # Improving
            'Status': ['RED', 'RED', 'GREEN', 'GREEN', 'GREEN']
        }
    
    elif test_scenario == 'error_retry':
        # System errors requiring retries
        data = {
            'Date': ['2025-10-01', '2025-10-02', '2025-10-03', '2025-10-04', '2025-10-05'],
            'Client': ['AcmeCorp', 'BetaTech', 'Zenith', 'AcmeCorp', 'BetaTech'],
            'DealID': ['DEAL123', 'DEAL007', 'DEAL221', 'DEAL123', 'DEAL007'],
            'Doc_Cycle_Time': [20, 18, 15, 10, 7],  # Improving after retries
            'Run_Success_Rate': [0.50, 0.65, 0.75, 0.85, 0.92],  # Recovering
            'Missing_Items': [3, 2, 2, 1, 1],  # Some persist
            'Onboarding_Duration': [80, 70, 55, 40, 30],  # Better
            'Status': ['RED', 'RED', 'GREEN', 'GREEN', 'GREEN']
        }
    
    return pd.DataFrame(data)


def load_file_registry(test_scenario='happy_path'):
    """Load file registry based on test scenario"""
    
    if test_scenario == 'happy_path':
        files = [
            'AcmeCorp_DEAL123_IDProof_20251005.pdf',
            'BetaTech_DEAL007_TaxDocs_20251006.pdf',
            'Zenith_DEAL221_PartnerAgreements_20251006.pdf',
            'AcmeCorp_DEAL123_Contract_20251007.pdf',
            'BetaTech_DEAL007_FinancialStatements_20251008.pdf'
        ]
    
    elif test_scenario == 'missing_docs':
        files = [
            'AcmeCorp_DEAL123_IDProof_20251005.pdf',
            # Simulating missing documents - only 1 file instead of expected 5+
        ]
    
    elif test_scenario == 'rename':
        files = [
            'AcmeCorp DEAL123 IDProof.pdf',  # Invalid: spaces
            'invalid_file_name.pdf',  # Invalid: missing structure
            'BetaTech_DEAL007_TaxDocs_2025-10-06.pdf',  # Invalid: date format with dashes
            'Zenith-DEAL221-Agreement.docx',  # Invalid: dashes instead of underscores
            'AcmeCorp_DEAL123_IDProof_20251005.pdf',  # Valid after rename
            'BetaTech_DEAL007_TaxDocs_20251006.pdf',  # Valid after rename
            'Zenith_DEAL221_Agreement_20251007.docx'  # Valid after rename
        ]
    
    elif test_scenario == 'error_retry':
        files = [
            'AcmeCorp_DEAL123_IDProof_20251005.pdf',
            'BetaTech_DEAL007_TaxDocs_20251006.pdf',
            'Zenith_DEAL221_Contract_20251007.pdf',
            'AcmeCorp_DEAL123_Financials_20251008.pdf'
        ]
    
    registry = []
    for fname in files:
        parsed = parse_filename(fname)
        registry.append({
            'Filename': fname,
            'Valid': is_valid_filename(fname),
            'Client': parsed['client'] if parsed else 'N/A',
            'DealID': parsed['deal_id'] if parsed else 'N/A',
            'DocType': parsed['doc_type'] if parsed else 'N/A',
            'Date': parsed['date'] if parsed else 'N/A'
        })
    
    return pd.DataFrame(registry)


# ===== PYARROW-FREE DISPLAY FUNCTIONS =====
def display_dataframe_as_table(df, title=None):
    """Display dataframe as static table without pyarrow"""
    if title:
        st.subheader(title)
    st.table(df)


def display_dataframe_as_html(df, title=None):
    """Display dataframe as HTML table without pyarrow"""
    if title:
        st.subheader(title)
    
    html_table = df.to_html(index=False, escape=False, table_id="custom-table")
    st.markdown(html_table, unsafe_allow_html=True)


def display_colored_registry(file_df):
    """Display file registry with color coding using HTML"""
    html_content = """
    <style>
    .file-table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
    }
    .file-table th, .file-table td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    .file-table th {
        background-color: #f2f2f2;
        font-weight: bold;
    }
    .valid-row {
        background-color: #d4edda;
    }
    .invalid-row {
        background-color: #f8d7da;
    }
    </style>
    
    <table class="file-table">
        <thead>
            <tr>
                <th>Filename</th>
                <th>Valid</th>
                <th>Client</th>
                <th>Deal ID</th>
                <th>Doc Type</th>
                <th>Date</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for _, row in file_df.iterrows():
        row_class = "valid-row" if row['Valid'] else "invalid-row"
        valid_symbol = "✅" if row['Valid'] else "❌"
        
        html_content += f"""
            <tr class="{row_class}">
                <td>{row['Filename']}</td>
                <td>{valid_symbol}</td>
                <td>{row['Client']}</td>
                <td>{row['DealID']}</td>
                <td>{row['DocType']}</td>
                <td>{row['Date']}</td>
            </tr>
        """
    
    html_content += """
        </tbody>
    </table>
    """
    
    st.markdown(html_content, unsafe_allow_html=True)


# ===== MAIN DASHBOARD =====
def main():
    st.title("📊 KPI Dashboard - Strat AI Solutions")
    st.markdown("**Real-time metrics for pilot workflows and document management**")
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Dashboard Settings")
    
    # Test scenario selector
    test_scenario = st.sidebar.selectbox(
        "🧪 Test Scenario",
        ["happy_path", "missing_docs", "rename", "error_retry"],
        format_func=lambda x: {
            "happy_path": "✅ Happy Path (All Good)",
            "missing_docs": "📄 Missing Documents",
            "rename": "✏️ File Rename Issues",
            "error_retry": "⚠️ Error & Retry"
        }[x]
    )
    
    # Display scenario description
    scenario_descriptions = {
        "happy_path": "All files valid, no missing documents, 100% success rate",
        "missing_docs": "Critical documents missing, low success rate, RED status",
        "rename": "Files with invalid naming requiring corrections",
        "error_retry": "System errors with retry attempts and recovery"
    }
    st.sidebar.info(f"**Current Scenario:** {scenario_descriptions[test_scenario]}")
    
    view_mode = st.sidebar.radio("📊 View Mode", ["Overview", "File Registry", "QA Status"])
    
    # Load data with selected test scenario
    df = load_log_data(test_scenario)
    file_df = load_file_registry(test_scenario)
    
    # Display test scenario banner
    st.info(f"🧪 **Testing Mode Active:** {scenario_descriptions[test_scenario]}")
    
    if view_mode == "Overview":
        show_overview(df, test_scenario)
    elif view_mode == "File Registry":
        show_file_registry(file_df, test_scenario)
    elif view_mode == "QA Status":
        show_qa_status(df, test_scenario)


# ===== OVERVIEW TAB =====
def show_overview(df, test_scenario):
    st.header("📈 Key Performance Indicators")
    
    # Top-level metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        median_cycle = df['Doc_Cycle_Time'].median()
        st.metric("Median Cycle Time", f"{median_cycle:.1f} days", 
                 delta=f"{median_cycle - 7:.1f}" if median_cycle < 7 else None,
                 delta_color="inverse")
    with col2:
        latest_success = df['Run_Success_Rate'].iloc[-1]
        prev_success = df['Run_Success_Rate'].iloc[-2] if len(df) > 1 else latest_success
        st.metric("Latest Success Rate", f"{latest_success*100:.1f}%",
                 delta=f"{(latest_success - prev_success)*100:.1f}%")
    with col3:
        total_missing = df['Missing_Items'].sum()
        st.metric("Total Missing Items", int(total_missing),
                 delta=f"-{int(total_missing)}" if total_missing > 0 else "0",
                 delta_color="inverse")
    with col4:
        avg_onboarding = df['Onboarding_Duration'].mean()
        st.metric("Avg Onboarding", f"{avg_onboarding:.1f} hrs",
                 delta=f"{avg_onboarding - 36:.1f}" if avg_onboarding < 36 else None,
                 delta_color="inverse")
    
    # Test scenario specific insights
    if test_scenario == "missing_docs":
        st.error("⚠️ **Alert:** High number of missing documents detected. Review required.")
    elif test_scenario == "rename":
        st.warning("⚠️ **Alert:** Multiple files require renaming for compliance.")
    elif test_scenario == "error_retry":
        st.warning("⚠️ **Alert:** System experiencing errors. Retry mechanisms active.")
    elif test_scenario == "happy_path":
        st.success("✅ **Status:** All systems operating within optimal parameters.")
    
    # Charts
    st.subheader("📊 Run Success Rate Over Time")
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(df['Date'], df['Run_Success_Rate'], marker='o', color='#2E86AB', linewidth=2)
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Success Rate')
    ax1.set_ylim(0.3, 1.05)
    ax1.axhline(y=0.9, color='green', linestyle='--', alpha=0.5, label='Target (90%)')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig1)
    
    st.subheader("📉 Missing Items Trend")
    fig2, ax2 = plt.subplots(figsize=(10, 4))
    colors = ['#A23B72' if x > 5 else '#2E86AB' for x in df['Missing_Items']]
    ax2.bar(df['Date'], df['Missing_Items'], color=colors)
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Missing Items Count')
    ax2.grid(True, alpha=0.3, axis='y')
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig2)
    
    st.subheader("⏱️ Onboarding Duration Progress")
    fig3, ax3 = plt.subplots(figsize=(10, 4))
    ax3.plot(df['Date'], df['Onboarding_Duration'], marker='s', color='#F18F01', linewidth=2)
    ax3.set_xlabel('Date')
    ax3.set_ylabel('Duration (hours)')
    ax3.axhline(y=36, color='green', linestyle='--', alpha=0.5, label='Target (36 hrs)')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig3)
    
    # Data table without pyarrow
    st.subheader("📋 Raw Data")
    display_dataframe_as_table(df)
    
    # Export functionality
    st.subheader("📥 Export Dashboard")
    if st.button("Export All Charts as PNG"):
        export_charts(df)


# ===== FILE REGISTRY TAB =====
def show_file_registry(file_df, test_scenario):
    st.header("📁 File Registry & Naming Compliance")
    
    # Summary metrics
    total_files = len(file_df)
    valid_files = file_df['Valid'].sum()
    invalid_files = total_files - valid_files
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Files", total_files)
    with col2:
        st.metric("Valid Files ✅", valid_files)
    with col3:
        st.metric("Invalid Files ❌", invalid_files,
                 delta=f"-{invalid_files}" if invalid_files > 0 else "0",
                 delta_color="inverse")
    
    # Test scenario specific alerts
    if test_scenario == "missing_docs":
        expected_files = 5
        st.error(f"⚠️ **Critical:** Expected {expected_files} files, found only {total_files}. " 
                f"{expected_files - total_files} files missing!")
    elif test_scenario == "rename" and invalid_files > 0:
        st.warning(f"⚠️ **Action Required:** {invalid_files} files need renaming to meet compliance standards.")
    
    # File validation table with color coding
    st.subheader("File Validation Status")
    display_colored_registry(file_df)
    
    # Show invalid files that need attention
    if invalid_files > 0:
        st.subheader("❌ Files Requiring Attention")
        invalid_df = file_df[file_df['Valid'] == False][['Filename']]
        st.table(invalid_df)
    
    # File uploader with validation
    st.subheader("📤 Upload New Document")
    uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'jpg', 'png', 'docx'])
    
    if uploaded_file:
        if is_valid_filename(uploaded_file.name):
            st.success(f"✅ Valid filename: {uploaded_file.name}")
            parsed = parse_filename(uploaded_file.name)
            st.json(parsed)
        else:
            st.error(f"❌ Invalid filename: {uploaded_file.name}")
            st.info("Expected format: ClientName_DealID_DocType_YYYYMMDD.ext\nExample: AcmeCorp_DEAL123_IDProof_20251005.pdf")
    
    # Naming rules reference
    with st.expander("📋 Naming Rules Reference"):
        st.markdown("""
        **Pattern:** `<ClientName>_<DealID>_<DocType>_<YYYYMMDD>.<ext>`
        
        **Rules:**
        - ✅ Use underscores `_` to separate parts
        - ✅ Date must be in YYYYMMDD format (no dashes)
        - ✅ Short, meaningful DocType values
        - ✅ Alphanumeric characters only
        - 🚫 No spaces, emojis, or special characters
        - 🚫 No dots or slashes in filename parts
        - 🚫 No dashes between components
        
        **Valid Examples:**
        - `AcmeCorp_DEAL123_IDProof_20251005.pdf`
        - `BetaTech_DEAL007_TaxDocs_20251006.pdf`
        - `Zenith_DEAL221_PartnerAgreements_20251006.pdf`
        
        **Invalid Examples:**
        - `AcmeCorp DEAL123 IDProof.pdf` ❌ (spaces)
        - `BetaTech_DEAL007_TaxDocs_2025-10-06.pdf` ❌ (date format)
        - `invalid_file_name.pdf` ❌ (missing structure)
        """)


# ===== QA STATUS TAB =====
def show_qa_status(df, test_scenario):
    st.header("🔍 QA Status & Daily Summary")
    
    # Latest status
    latest_status = df['Status'].iloc[-1]
    latest_date = df['Date'].iloc[-1]
    
    if latest_status == "GREEN":
        st.success(f"✅ Status for {latest_date}: GREEN - All checks passed")
    else:
        st.error(f"❌ Status for {latest_date}: RED - Action required")
    
    # Test scenario context
    status_context = {
        "happy_path": "All workflows operating smoothly with optimal performance metrics.",
        "missing_docs": "Multiple documents are missing from expected deal folders. Immediate action required.",
        "rename": "File naming violations detected. Files must be renamed to maintain compliance.",
        "error_retry": "System errors encountered during processing. Retry mechanisms have been engaged."
    }
    st.info(f"**Context:** {status_context[test_scenario]}")
    
    # Status history - using static table
    st.subheader("Status History")
    status_df = df[['Date', 'Status', 'Run_Success_Rate', 'Missing_Items']].copy()
    status_df['Run_Success_Rate'] = (status_df['Run_Success_Rate'] * 100).round(1).astype(str) + '%'
    display_dataframe_as_table(status_df)
    
    # Status distribution
    st.subheader("📊 Status Distribution")
    col1, col2 = st.columns(2)
    with col1:
        green_count = (df['Status'] == 'GREEN').sum()
        red_count = (df['Status'] == 'RED').sum()
        st.metric("GREEN Days", green_count)
        st.metric("RED Days", red_count)
    
    with col2:
        fig, ax = plt.subplots(figsize=(6, 4))
        status_counts = df['Status'].value_counts()
        colors_map = {'GREEN': '#2E86AB', 'RED': '#A23B72'}
        colors_list = [colors_map.get(x, '#666666') for x in status_counts.index]
        ax.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%', 
               colors=colors_list, startangle=90)
        ax.set_title('Status Distribution')
        st.pyplot(fig)
    
    # Daily summary generation
    st.subheader("📝 Generate Daily Summary for Notion")
    if st.button("Generate Summary"):
        summary = generate_daily_summary(df, test_scenario)
        st.text_area("Copy to Notion:", summary, height=300)


def generate_daily_summary(df, test_scenario):
    """Generate formatted daily summary for Notion"""
    latest = df.iloc[-1]
    
    scenario_notes = {
        "happy_path": "All systems are functioning optimally with no issues detected.",
        "missing_docs": f"⚠️ CRITICAL: {int(latest['Missing_Items'])} documents are missing from expected folders.",
        "rename": "⚠️ WARNING: Multiple files require renaming to meet compliance standards.",
        "error_retry": "⚠️ NOTICE: System errors detected. Retry mechanisms are handling recovery."
    }
    
    summary = f"""## Daily QA Summary - {latest['Date']}

**Test Scenario:** {test_scenario.replace('_', ' ').title()}
**Status:** {latest['Status']}

### Key Metrics
- Run Success Rate: {latest['Run_Success_Rate']*100:.1f}%
- Missing Items: {int(latest['Missing_Items'])}
- Doc Cycle Time: {latest['Doc_Cycle_Time']} days
- Onboarding Duration: {latest['Onboarding_Duration']} hours

### Trends (Last 5 Days)
- Median Cycle Time: {df['Doc_Cycle_Time'].median():.1f} days
- Average Success Rate: {df['Run_Success_Rate'].mean()*100:.1f}%
- Total Missing Items: {int(df['Missing_Items'].sum())}
- Average Onboarding: {df['Onboarding_Duration'].mean():.1f} hours

### Status Notes
{scenario_notes[test_scenario]}

### Action Items
"""
    
    if test_scenario == "happy_path":
        summary += "✅ Continue monitoring - no action required\n"
    elif test_scenario == "missing_docs":
        summary += f"🔴 URGENT: Locate and upload {int(latest['Missing_Items'])} missing documents\n"
        summary += "🔴 Review document collection process\n"
        summary += "🔴 Contact clients for outstanding items\n"
    elif test_scenario == "rename":
        summary += "🟡 Rename non-compliant files using standard format\n"
        summary += "🟡 Update file naming documentation\n"
        summary += "🟡 Train team on proper naming conventions\n"
    elif test_scenario == "error_retry":
        summary += "🟡 Monitor retry success rates\n"
        summary += "🟡 Investigate root cause of errors\n"
        summary += "🟡 Review system logs for patterns\n"
    
    summary += f"""
### Next Steps
{'✅ Maintain current standards and procedures' if latest['Status'] == 'GREEN' else '⚠️ Address red flags and re-test workflows'}

---
*Auto-generated by KPI Dashboard - Test Mode: {test_scenario}*
"""
    return summary.strip()


# ===== EXPORT FUNCTIONALITY =====
def export_charts(df):
    """Export all charts as PNG files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create combined figure
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    # Chart 1: Success Rate
    axes[0].plot(df['Date'], df['Run_Success_Rate'], marker='o', color='#2E86AB', linewidth=2)
    axes[0].set_title('Run Success Rate Over Time')
    axes[0].set_ylabel('Success Rate')
    axes[0].axhline(y=0.9, color='green', linestyle='--', alpha=0.5)
    axes[0].grid(True, alpha=0.3)
    
    # Chart 2: Missing Items
    colors = ['#A23B72' if x > 5 else '#2E86AB' for x in df['Missing_Items']]
    axes[1].bar(df['Date'], df['Missing_Items'], color=colors)
    axes[1].set_title('Missing Items Trend')
    axes[1].set_ylabel('Count')
    axes[1].grid(True, alpha=0.3, axis='y')
    
    # Chart 3: Onboarding Duration
    axes[2].plot(df['Date'], df['Onboarding_Duration'], marker='s', color='#F18F01', linewidth=2)
    axes[2].set_title('Onboarding Duration Progress')
    axes[2].set_ylabel('Hours')
    axes[2].set_xlabel('Date')
    axes[2].axhline(y=36, color='green', linestyle='--', alpha=0.5)
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    
    # Download button
    st.download_button(
        label="Download Dashboard Charts",
        data=buf,
        file_name=f"Dashboard_Metrics_{timestamp}.png",
        mime="image/png"
    )
    
    st.success(f"✅ Charts exported as Dashboard_Metrics_{timestamp}.png")


# ===== RUN APP =====
if __name__ == "__main__":
    main()