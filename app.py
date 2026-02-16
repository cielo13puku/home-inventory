import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# ページの設定
st.set_page_config(
    page_title="おうち在庫管理",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# シンプルでスッキリしたCSS
st.markdown("""
<style>
    /* 全体の背景を白に */
    .stApp {
        background-color: #ffffff;
    }
    
    /* 全体のフォント調整 */
    html, body, [class*="css"] {
        font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', Meiryo, sans-serif;
        font-size: 14px;
    }
    
    /* コンパクトなヘッダー */
    .app-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0.75rem 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .app-title {
        color: white;
        font-size: 1.1rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: 0.3px;
    }
    
    .app-subtitle {
        color: rgba(255,255,255,0.85);
        font-size: 0.65rem;
        margin-top: 0.15rem;
    }
    
    /* 統計カード */
    .stat-card {
        background: white;
        padding: 0.75rem;
        border-radius: 8px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.1);
        text-align: center;
        border: 1px solid #e5e7eb;
    }
    
    .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
    }
    
    .stat-label {
        font-size: 0.65rem;
        color: #6b7280;
        margin-top: 0.15rem;
        font-weight: 500;
    }
    
    .stat-ok { color: #10b981; }
    .stat-warning { color: #f59e0b; }
    .stat-danger { color: #ef4444; }
    
    /* アイテムカード - 横並びレイアウト */
    .item-card {
        background: white;
        border-radius: 10px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.6rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        border: 1px solid #e5e7eb;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .item-left {
        flex: 1;
    }
    
    .item-name {
        font-size: 0.95rem;
        font-weight: 600;
        margin-bottom: 0.2rem;
        color: #1f2937;
    }
    
    .item-stock {
        font-size: 0.7rem;
        color: #6b7280;
    }
    
    /* ボタン調整 */
    .stButton > button {
        border-radius: 6px;
        font-weight: 600;
        font-size: 1rem;
        padding: 0.4rem 0.8rem;
        border: 1px solid #d1d5db;
        background-color: white;
        color: #374151;
        transition: all 0.15s;
        min-width: 40px;
        height: 38px;
    }
    
    .stButton > button:hover {
        background-color: #f9fafb;
        border-color: #9ca3af;
    }
    
    .stButton > button:active {
        transform: scale(0.96);
    }
    
    /* タブのスタイル改善 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.3rem;
        background: white;
        border-radius: 8px;
        padding: 0.3rem;
        margin-bottom: 1rem;
        border: 1px solid #e5e7eb;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        padding: 0.5rem 1rem;
        color: #6b7280;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #667eea;
        color: white;
    }
    
    /* 余白調整 */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 800px;
    }
    
    /* ラジオボタン */
    .stRadio > label {
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    /* 買い物リストアイテム */
    .shopping-item {
        background: #fef3c7;
        border: 1px solid #fcd34d;
        padding: 0.75rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }
    
    .shopping-item-name {
        font-weight: 600;
        font-size: 0.9rem;
        color: #92400e;
    }
    
    .shopping-item-detail {
        font-size: 0.7rem;
        color: #b45309;
        margin-top: 0.2rem;
    }
    
    /* フィルターボタンのスタイル */
    div[data-testid="stHorizontalBlock"] {
        gap: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Google Sheets接続
@st.cache_resource
def get_google_sheet():
    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds_dict = {
            "type": st.secrets["gsheets"]["type"],
            "project_id": st.secrets["gsheets"]["project_id"],
            "private_key_id": st.secrets["gsheets"]["private_key_id"],
            "private_key": st.secrets["gsheets"]["private_key"],
            "client_email": st.secrets["gsheets"]["client_email"],
            "client_id": st.secrets["gsheets"]["client_id"],
            "auth_uri": st.secrets["gsheets"]["auth_uri"],
            "token_uri": st.secrets["gsheets"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["gsheets"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["gsheets"]["client_x509_cert_url"]
        }
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        sheet_url = "https://docs.google.com/spreadsheets/d/1xLJxgm9SxveTBPJz1swAygGrc4zdoAD1GoRMLLaNgs0/edit?usp=sharing"
        sheet = client.open_by_url(sheet_url).sheet1
        
        return sheet
    except Exception as e:
        st.error(f"接続エラー: {e}")
        return None

def load_data(sheet):
    try:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        df['予備数'] = pd.to_numeric(df['予備数'], errors='coerce').fillna(0).astype(int)
        df['補充しきい値'] = pd.to_numeric(df['補充しきい値'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
        return None

def update_data(sheet, df):
    try:
        data = [df.columns.tolist()] + df.values.tolist()
        sheet.clear()
        sheet.update(data, 'A1')
        return True
    except Exception as e:
        st.error(f"更新エラー: {e}")
        return False

# コンパクトなヘッダー
st.markdown("""
<div class="app-header">
    <h1 class="app-title">🏠 おうち在庫管理システム</h1>
    <p class="app-subtitle">いつでも、どこでも、在庫チェック</p>
</div>
""", unsafe_allow_html=True)

# メイン処理
try:
    sheet = get_google_sheet()
    
    if sheet is None:
        st.error("Google Sheetsに接続できませんでした")
        st.stop()
    
    df = load_data(sheet)
    
    if df is None or df.empty:
        st.warning("データが見つかりませんでした")
        st.stop()
    
    # 統計情報
    total_items = len(df)
    critical_items = len(df[df['予備数'] == 0])
    warning_items = len(df[(df['予備数'] > 0) & (df['予備数'] < df['補充しきい値'])])
    ok_items = len(df[df['予備数'] >= df['補充しきい値']])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value stat-ok">{ok_items}</div>
            <div class="stat-label">在庫OK</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value stat-warning">{warning_items}</div>
            <div class="stat-label">要注意</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value stat-danger">{critical_items}</div>
            <div class="stat-label">在庫切れ</div>
        </div>
        """, unsafe_allow_html=True)
    
    # タブ
    tab1, tab2 = st.tabs(["📦 在庫一覧", "🛒 買い物リスト"])
    
    # タブ1: 在庫一覧
    with tab1:
        # フィルター
        filter_option = st.radio(
            "表示",
            ["すべて", "要補充のみ", "在庫OKのみ"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        if filter_option == "要補充のみ":
            display_df = df[df['予備数'] < df['補充しきい値']]
        elif filter_option == "在庫OKのみ":
            display_df = df[df['予備数'] >= df['補充しきい値']]
        else:
            display_df = df
        
        if display_df.empty:
            st.info("表示するアイテムがありません")
        else:
            for index, row in display_df.iterrows():
                current_stock = int(row['予備数'])
                threshold = int(row['補充しきい値'])
                
                # 横並びレイアウト
                col1, col2, col3 = st.columns([3, 0.6, 0.6])
                
                with col1:
                    st.markdown(f"""
                    <div class="item-card">
                        <div class="item-left">
                            <div class="item-name">{row['項目名']}</div>
                            <div class="item-stock">在庫: {current_stock}個 / 在庫下限: {threshold}個</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("➖", key=f"minus_{index}", use_container_width=True):
                        df.at[index, '予備数'] = max(0, current_stock - 1)
                        if update_data(sheet, df):
                            st.rerun()
                
                with col3:
                    if st.button("➕", key=f"plus_{index}", use_container_width=True):
                        df.at[index, '予備数'] = current_stock + 1
                        if update_data(sheet, df):
                            st.rerun()
    
    # タブ2: 買い物リスト
    with tab2:
        to_buy = df[df['予備数'] < df['補充しきい値']].copy()
        
        if not to_buy.empty:
            st.markdown(f"**{len(to_buy)}個のアイテム**を補充する必要があります")
            
            st.markdown("")
            
            for idx, (index, row) in enumerate(to_buy.iterrows(), 1):
                shortage = int(row['補充しきい値']) - int(row['予備数'])
                
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class="shopping-item">
                        <div class="shopping-item-name">{idx}. {row['項目名']}</div>
                        <div class="shopping-item-detail">現在 {row['予備数']}個 → あと{shortage}個必要</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("✓", key=f"bought_{index}", use_container_width=True):
                        df.at[index, '予備数'] = int(row['補充しきい値'])
                        if update_data(sheet, df):
                            st.success("✓")
                            st.rerun()
            
            # コピー用リスト
            with st.expander("📋 コピー用リスト"):
                shopping_list = "\n".join([f"□ {row['項目名']}" for _, row in to_buy.iterrows()])
                st.text_area("", shopping_list, height=200, label_visibility="collapsed")
        else:
            st.success("🎉 すべての在庫が十分です!")
            st.balloons()

except Exception as e:
    st.error("エラーが発生しました")
    with st.expander("詳細"):
        st.code(str(e))