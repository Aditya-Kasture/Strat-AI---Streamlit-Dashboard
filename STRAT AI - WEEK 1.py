import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re
from datetime import datetime
import io
# import gspread or pygsheets for Google Sheets integration

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

# ===== DATA LOADING =====
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_log_data():
    """
    Load log data from Google Sheets or sample data
    Replace this function with actual Google Sheets API integration
    """
    # Sample data for demonstration
    data = {
        'Date': ['2025-10-01', '2025-10-02', '2025-10-03', '2025-10-04', '2025-10-05'],
        'Client': ['AcmeCorp', 'BetaTech', 'Zenith', 'AcmeCorp', 'BetaTech'],
        'DealID': ['DEAL123', 'DEAL007', 'DEAL221', 'DEAL123', 'DEAL007'],
        'Doc_Cycle_Time': [10, 7, 6, 5, 4],  # days
        'Run_Success_Rate': [0.85, 0.92, 0.95, 0.97, 0.98],
        'Missing_Items': [5, 2, 1, 0, 0],
        'Onboarding_Duration': [48, 36, 30, 24, 20],  # hours
        'Status': ['RED', 'GREEN', 'GREEN', 'GREEN', 'GREEN']
    }
    return pd.DataFrame(data)

@st.cache_data
def load_file_registry():
    """Load file registry with validation status"""
    files = [
        'AcmeCorp_DEAL123_IDProof_20251005.pdf',
        'BetaTech_DEAL007_TaxDocs_20251006.pdf',
        'Zenith_DEAL221_PartnerAgreements_20251006.pdf',
        'InvalidFile.pdf',
        'AcmeCorp DEAL123 IDProof.pdf'  # Invalid: contains spaces
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

# ===== MAIN DASHBOARD =====
def main():
    st.title("📊 KPI Dashboard - Strat AI Solutions")
    st.markdown("**Real-time metrics for pilot workflows and document management**")
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Dashboard Settings")
    view_mode = st.sidebar.radio("View Mode", ["Overview", "File Registry", "QA Status"])
    
    # Load data
    df = load_log_data()
    file_df = load_file_registry()
    
    if view_mode == "Overview":
        show_overview(df)
    elif view_mode == "File Registry":
        show_file_registry(file_df)
    elif view_mode == "QA Status":
        show_qa_status(df)

# ===== OVERVIEW TAB =====
def show_overview(df):
    st.header("📈 Key Performance Indicators")
    
    # Top-level metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Median Cycle Time", f"{df['Doc_Cycle_Time'].median():.1f} days")
    
    with col2:
        latest_success = df['Run_Success_Rate'].iloc[-1]
        st.metric("Latest Success Rate", f"{latest_success*100:.1f}%")
    
    with col3:
        total_missing = df['Missing_Items'].sum()
        st.metric("Total Missing Items", int(total_missing))
    
    with col4:
        avg_onboarding = df['Onboarding_Duration'].mean()
        st.metric("Avg Onboarding", f"{avg_onboarding:.1f} hrs")
    
    # Charts
    st.subheader("📊 Run Success Rate Over Time")
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(df['Date'], df['Run_Success_Rate'], marker='o', color='#2E86AB', linewidth=2)
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Success Rate')
    ax1.set_ylim(0.8, 1.0)
    ax1.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig1)
    
    st.subheader("📉 Missing Items Trend")
    fig2, ax2 = plt.subplots(figsize=(10, 4))
    ax2.bar(df['Date'], df['Missing_Items'], color='#A23B72')
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
    ax3.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig3)
    
    # Export functionality
    st.subheader("📥 Export Dashboard")
    if st.button("Export All Charts as PNG"):
        export_charts(df)

# ===== FILE REGISTRY TAB =====
def show_file_registry(file_df):
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
        st.metric("Invalid Files ❌", invalid_files)
    
    # File validation table
    st.subheader("File Validation Status")
    
    # Color code the table
    def highlight_validity(row):
        if row['Valid']:
            return ['background-color: #d4edda'] * len(row)
        else:
            return ['background-color: #f8d7da'] * len(row)
    
    styled_df = file_df.style.apply(highlight_validity, axis=1)
    st.dataframe(styled_df, use_container_width=True)
    
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
        - ✅ Date must be in YYYYMMDD format
        - ✅ Short, meaningful DocType values
        - 🚫 No spaces, emojis, or special characters
        - 🚫 No dots or slashes in filename parts
        
        **Examples:**
        - `AcmeCorp_DEAL123_IDProof_20251005.pdf`
        - `BetaTech_DEAL007_TaxDocs_20251006.pdf`
        - `Zenith_DEAL221_PartnerAgreements_20251006.pdf`
        """)

# ===== QA STATUS TAB =====
def show_qa_status(df):
    st.header("🔍 QA Status & Daily Summary")
    
    # Latest status
    latest_status = df['Status'].iloc[-1]
    latest_date = df['Date'].iloc[-1]
    
    if latest_status == "GREEN":
        st.success(f"✅ Status for {latest_date}: GREEN")
    else:
        st.error(f"❌ Status for {latest_date}: RED")
    
    # Status history
    st.subheader("Status History")
    status_df = df[['Date', 'Status', 'Run_Success_Rate', 'Missing_Items']].copy()
    st.dataframe(status_df, use_container_width=True)
    
    # Daily summary generation
    st.subheader("📝 Generate Daily Summary for Notion")
    if st.button("Generate Summary"):
        summary = generate_daily_summary(df)
        st.text_area("Copy to Notion:", summary, height=200)

def generate_daily_summary(df):
    """Generate formatted daily summary for Notion"""
    latest = df.iloc[-1]
    summary = f"""
## Daily QA Summary - {latest['Date']}

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

### Action Items
{'✅ All systems nominal' if latest['Status'] == 'GREEN' else '⚠️ Review missing items and cycle time'}

---
*Auto-generated by KPI Dashboard*
    """
    return summary.strip()

# ===== EXPORT FUNCTIONALITY =====
def export_charts(df):
    """Export all charts as PNG files"""
    timestamp = datetime.now().strftime("%Y%m%d")
    
    # Create combined figure
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    # Chart 1: Success Rate
    axes[0].plot(df['Date'], df['Run_Success_Rate'], marker='o', color='#2E86AB', linewidth=2)
    axes[0].set_title('Run Success Rate Over Time')
    axes[0].set_ylabel('Success Rate')
    axes[0].grid(True, alpha=0.3)
    
    # Chart 2: Missing Items
    axes[1].bar(df['Date'], df['Missing_Items'], color='#A23B72')
    axes[1].set_title('Missing Items Trend')
    axes[1].set_ylabel('Count')
    axes[1].grid(True, alpha=0.3, axis='y')
    
    # Chart 3: Onboarding Duration
    axes[2].plot(df['Date'], df['Onboarding_Duration'], marker='s', color='#F18F01', linewidth=2)
    axes[2].set_title('Onboarding Duration Progress')
    axes[2].set_ylabel('Hours')
    axes[2].set_xlabel('Date')
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
