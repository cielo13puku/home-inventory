import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from google.cloud import vision
import io
from datetime import datetime, timedelta
import re

# ページの設定
st.set_page_config(
    page_title="おうち在庫管理",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# パステルカラーとスタイリッシュなCSS
st.markdown("""
<style>
    /* Streamlitのヘッダーとフッターを非表示 */
    header[data-testid="stHeader"] {
        display: none;
    }
    
    .stDeployButton {
        display: none;
    }
    
    footer {
        display: none;
    }
    
    #MainMenu {
        display: none;
    }
    
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
        background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
        padding: 0.9rem 1rem;
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
        color: rgba(255,255,255,0.9);
        font-size: 0.8rem;
        margin-top: 0.25rem;
        font-weight: 500;
    }
    
    /* 統計カード */
    .stats-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.75rem;
        margin-bottom: 1.5rem;
    }
    
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
    
    /* カテゴリバッジ - パステルカラー */
    .category-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    
    .category-食料品 { background-color: #D4EDDA; color: #155724; }
    .category-日用品 { background-color: #D1ECF1; color: #0C5460; }
    .category-ベビー用品 { background-color: #F8D7DA; color: #721C24; }
    .category-調味料 { background-color: #FFF3CD; color: #856404; }
    
    /* アイテムカード */
    .item-row-inline {
        background: white;
        border-radius: 10px;
        padding: 0.85rem 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        border: 1px solid #e5e7eb;
        margin-bottom: 0.5rem;
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
    
    .expiry-alert {
        font-size: 0.7rem;
        color: #dc3545;
        font-weight: 600;
    }
    
    .expiry-warning {
        font-size: 0.7rem;
        color: #f59e0b;
        font-weight: 600;
    }
    
    /* プログレスバー */
    .progress-bar {
        width: 100%;
        height: 6px;
        background-color: #e5e7eb;
        border-radius: 3px;
        overflow: hidden;
        margin-top: 0.3rem;
    }
    
    .progress-fill {
        height: 100%;
        transition: width 0.3s ease;
        border-radius: 3px;
    }
    
    .progress-high { background: linear-gradient(90deg, #A8E6CF, #88D8B0); }
    .progress-medium { background: linear-gradient(90deg, #FFD3B6, #FFAAA5); }
    .progress-low { background: linear-gradient(90deg, #FFAAA5, #FF8B94); }
    
    /* カラム間の余白を調整 */
    div[data-testid="column"] {
        padding: 0 0.25rem;
    }
    
    div[data-testid="column"]:first-child {
        padding-left: 0;
    }
    
    div[data-testid="column"]:last-child {
        padding-right: 0;
    }
    
    /* 検索バー */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #d1d5db;
        padding: 0.6rem 1rem;
        font-size: 0.9rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #6b7280;
        box-shadow: 0 0 0 2px rgba(107, 114, 128, 0.1);
    }
    
    /* ボタン調整 */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 0.5rem 1rem;
        border: none;
        transition: all 0.2s;
    }
    
    .stButton > button:active {
        transform: scale(0.95);
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
    
    .stRadio div[role="radiogroup"] label {
        color: #1f2937 !important;
    }
    
    .stRadio div[role="radiogroup"] label p {
        color: #1f2937 !important;
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
    
    .manual-item {
        background: #E3F2FD;
        border: 1px solid #90CAF9;
        padding: 0.75rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }
    
    .manual-item-name {
        font-weight: 600;
        font-size: 0.9rem;
        color: #1565C0;
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
        
        # 必要な列を確保
        required_columns = ['アイコン', '項目名', 'カテゴリ', '在庫数', '予備数', '補充しきい値', '賞味期限']
        for col in required_columns:
            if col not in df.columns:
                df[col] = ''
        
        # 数値型に変換
        df['在庫数'] = pd.to_numeric(df['在庫数'], errors='coerce').fillna(0).astype(int)
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

# Vision API関数
def detect_text_from_image(image_bytes):
    """レシート画像からテキストを抽出"""
    try:
        api_key = st.secrets["google_vision"]["api_key"]
        client = vision.ImageAnnotatorClient(client_options={"api_key": api_key})
        
        image = vision.Image(content=image_bytes)
        response = client.text_detection(image=image)
        texts = response.text_annotations
        
        if texts:
            return texts[0].description
        else:
            return ""
    except Exception as e:
        st.error(f"Vision APIエラー: {e}")
        return ""

def parse_receipt_text(text, df):
    """レシートのテキストから商品を抽出"""
    detected_items = []
    lines = text.split('\n')
    registered_items = df['項目名'].tolist()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        for item_name in registered_items:
            if item_name in line:
                numbers = re.findall(r'\d+', line)
                quantity = int(numbers[0]) if numbers else 1
                
                if not any(d['name'] == item_name for d in detected_items):
                    detected_items.append({'name': item_name, 'quantity': quantity})
                break
    
    return detected_items

def check_expiry_status(expiry_date):
    """賞味期限のステータスをチェック"""
    if not expiry_date or expiry_date == '':
        return None
    
    try:
        expiry = datetime.strptime(str(expiry_date), '%Y-%m-%d')
        today = datetime.now()
        days_left = (expiry - today).days
        
        if days_left < 0:
            return 'expired'
        elif days_left <= 3:
            return 'critical'
        elif days_left <= 7:
            return 'warning'
        else:
            return 'ok'
    except:
        return None

# セッション状態の初期化
if 'manual_shopping_list' not in st.session_state:
    st.session_state.manual_shopping_list = []

if 'low_stock_items' not in st.session_state:
    st.session_state.low_stock_items = []

# ヘッダー
st.markdown("""
<div class="app-header">
    <div class="app-title">🏠 おうち在庫管理システム</div>
    <div class="app-subtitle">いつでも、どこでも、在庫チェック</div>
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
    
    # 統計情報の計算
    total_items = len(df)
    critical_items = len(df[df['予備数'] == 0])
    warning_items = len(df[(df['予備数'] > 0) & (df['予備数'] < df['補充しきい値'])])
    ok_items = len(df[df['予備数'] >= df['補充しきい値']])
    
    # 統計情報 - 横並び
    st.markdown(f"""
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; margin-bottom: 1.5rem;">
        <div class="stat-card">
            <div class="stat-value stat-ok">{ok_items}</div>
            <div class="stat-label">在庫OK</div>
        </div>
        <div class="stat-card">
            <div class="stat-value stat-warning">{warning_items}</div>
            <div class="stat-label">要注意</div>
        </div>
        <div class="stat-card">
            <div class="stat-value stat-danger">{critical_items}</div>
            <div class="stat-label">在庫切れ</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # タブ
    tab1, tab2, tab3 = st.tabs(["📦 在庫一覧", "🛒 買うものリスト", "📸 レシート読み取り"])
    
    # タブ1: 在庫一覧
    with tab1:
        # 新規追加ボタン
        if st.button("➕ 新しいアイテムを追加", use_container_width=True):
            st.session_state.show_add_form = True
        
        # 新規追加フォーム
        if st.session_state.get('show_add_form', False):
            with st.form("add_item_form"):
                st.markdown("### 新しいアイテムを追加")
                
                col1, col2 = st.columns(2)
                with col1:
                    new_icon = st.text_input("アイコン(絵文字)", placeholder="🍶")
                    new_name = st.text_input("項目名", placeholder="醤油")
                    new_category = st.text_input("カテゴリ", placeholder="調味料")
                
                with col2:
                    new_stock = st.number_input("在庫数", min_value=0, value=0)
                    new_threshold = st.number_input("在庫下限", min_value=0, value=1)
                    new_expiry = st.text_input("賞味期限(YYYY-MM-DD)", placeholder="2026-12-31")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    submit = st.form_submit_button("追加", use_container_width=True)
                with col_btn2:
                    cancel = st.form_submit_button("キャンセル", use_container_width=True)
                
                if submit and new_name:
                    new_row = {
                        'アイコン': new_icon,
                        '項目名': new_name,
                        'カテゴリ': new_category,
                        '在庫数': new_stock,
                        '予備数': new_stock,
                        '補充しきい値': new_threshold,
                        '賞味期限': new_expiry
                    }
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    if update_data(sheet, df):
                        st.success(f"✓ {new_name}を追加しました!")
                        st.session_state.show_add_form = False
                        st.rerun()
                
                if cancel:
                    st.session_state.show_add_form = False
                    st.rerun()
        
        st.divider()
        
        # 検索バーとフィルター
        search_query = st.text_input("🔍 検索", placeholder="項目名で検索...", label_visibility="collapsed")
        
        col_filter1, col_filter2 = st.columns(2)
        
        with col_filter1:
            categories = ['すべて'] + sorted(df['カテゴリ'].unique().tolist())
            category_filter = st.selectbox("カテゴリー", categories, label_visibility="collapsed", key="category_filter")
        
        with col_filter2:
            filter_option = st.radio("表示", ["すべて", "要補充", "在庫OK"], horizontal=True, label_visibility="collapsed")
        
        # フィルター適用
        display_df = df.copy()
        
        # カテゴリ順にソート
        display_df = display_df.sort_values('カテゴリ')
        
        if search_query:
            display_df = display_df[display_df['項目名'].str.contains(search_query, case=False, na=False)]
        
        if category_filter != 'すべて':
            display_df = display_df[display_df['カテゴリ'] == category_filter]
        
        if filter_option == "要補充":
            display_df = display_df[display_df['予備数'] < display_df['補充しきい値']]
        elif filter_option == "在庫OK":
            display_df = display_df[display_df['予備数'] >= display_df['補充しきい値']]
        
        if display_df.empty:
            st.info("表示するアイテムがありません")
        else:
            for index, row in display_df.iterrows():
                current_stock = int(row['予備数'])
                threshold = int(row['補充しきい値'])
                icon = row.get('アイコン', '')
                category = row.get('カテゴリ', '')
                expiry = row.get('賞味期限', '')
                
                # 在庫率を計算
                if threshold > 0:
                    stock_ratio = (current_stock / threshold) * 100
                else:
                    stock_ratio = 100
                
                # プログレスバーの色
                if stock_ratio >= 100:
                    progress_class = "progress-high"
                elif stock_ratio >= 50:
                    progress_class = "progress-medium"
                else:
                    progress_class = "progress-low"
                
                # 賞味期限チェック
                expiry_status = check_expiry_status(expiry) if category == '食料品' else None
                
                # 横並びレイアウト
                col1, col2, col3, col4 = st.columns([5, 1, 1, 1])
                
                with col1:
                    category_class = f"category-{category}" if category else ""
                    category_badge = f'<span class="category-badge {category_class}">{category}</span>' if category else ''
                    
                    expiry_html = ""
                    if expiry_status == 'expired':
                        expiry_html = f'<div class="expiry-alert">⚠️ 期限切れ</div>'
                    elif expiry_status == 'critical':
                        expiry_html = f'<div class="expiry-alert">⚠️ 期限まであと{(datetime.strptime(str(expiry), "%Y-%m-%d") - datetime.now()).days}日</div>'
                    elif expiry_status == 'warning':
                        expiry_html = f'<div class="expiry-warning">期限まであと{(datetime.strptime(str(expiry), "%Y-%m-%d") - datetime.now()).days}日</div>'
                    
                    progress_bar_html = f'<div class="progress-bar"><div class="progress-fill {progress_class}" style="width: {min(stock_ratio, 100)}%"></div></div>'
                    
                    st.markdown(f"""
                    <div class="item-row-inline">
                        <div class="item-name">{icon} {category_badge}{row['項目名']}</div>
                        <div class="item-stock">在庫: {current_stock}個 / 在庫下限: {threshold}個</div>
                        {expiry_html}
                        {progress_bar_html}
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("⚠️", key=f"low_{index}", use_container_width=True, help="残りわずか"):
                        if row['項目名'] not in st.session_state.low_stock_items:
                            st.session_state.low_stock_items.append(row['項目名'])
                            st.success("買うものリストに追加!")
                            st.rerun()
                
                with col3:
                    if st.button("➖", key=f"minus_{index}", use_container_width=True):
                        df.at[index, '予備数'] = max(0, current_stock - 1)
                        if update_data(sheet, df):
                            st.rerun()
                
                with col4:
                    if st.button("➕", key=f"plus_{index}", use_container_width=True):
                        df.at[index, '予備数'] = current_stock + 1
                        if update_data(sheet, df):
                            st.rerun()
    
    # タブ2: 買うものリスト
    with tab2:
        # 単発追加フォーム
        with st.form("manual_add", clear_on_submit=True):
            st.markdown("### 📝 単発で追加")
            col1, col2 = st.columns([4, 1])
            with col1:
                manual_item = st.text_input("買うもの", placeholder="ティッシュ、シャンプーなど...", label_visibility="collapsed")
            with col2:
                add_manual = st.form_submit_button("追加", use_container_width=True)
            
            if add_manual and manual_item:
                if manual_item not in st.session_state.manual_shopping_list:
                    st.session_state.manual_shopping_list.append(manual_item)
                    st.success(f"✓ {manual_item}を追加しました!")
                    st.rerun()
        
        st.divider()
        
        # 在庫切れアイテム
        to_buy = df[df['予備数'] < df['補充しきい値']].copy()
        
        # 残りわずかアイテム
        low_stock_df = df[df['項目名'].isin(st.session_state.low_stock_items)]
        
        total_items_to_buy = len(to_buy) + len(low_stock_df) + len(st.session_state.manual_shopping_list)
        
        if total_items_to_buy > 0:
            st.markdown(f'<h3 style="color: #1f2937;">買うものリスト ({total_items_to_buy}個)</h3>', unsafe_allow_html=True)
            
            # 在庫切れ
            if not to_buy.empty:
                st.markdown('<h4 style="color: #1f2937;">📦 在庫切れ</h4>', unsafe_allow_html=True)
                for idx, (index, row) in enumerate(to_buy.iterrows(), 1):
                    shortage = int(row['補充しきい値']) - int(row['予備数'])
                    icon = row.get('アイコン', '')
                    
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"""
                        <div class="shopping-item">
                            <div class="shopping-item-name">{icon} {row['項目名']}</div>
                            <div class="shopping-item-detail">現在 {row['予備数']}個 → あと{shortage}個必要</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        if st.button("✓", key=f"bought_{index}", use_container_width=True):
                            df.at[index, '予備数'] = int(row['補充しきい値'])
                            if update_data(sheet, df):
                                st.success("✓")
                                st.rerun()
            
            # 残りわずか
            if not low_stock_df.empty:
                st.markdown('<h4 style="color: #1f2937;">⚠️ 残りわずか</h4>', unsafe_allow_html=True)
                for idx, (index, row) in enumerate(low_stock_df.iterrows(), 1):
                    icon = row.get('アイコン', '')
                    
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"""
                        <div class="shopping-item">
                            <div class="shopping-item-name">{icon} {row['項目名']}</div>
                            <div class="shopping-item-detail">在庫: {row['予備数']}個</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        if st.button("削除", key=f"remove_low_{index}", use_container_width=True):
                            st.session_state.low_stock_items.remove(row['項目名'])
                            st.rerun()
            
            # 単発追加アイテム
            if st.session_state.manual_shopping_list:
                st.markdown('<h4 style="color: #1f2937;">📝 単発メモ</h4>', unsafe_allow_html=True)
                for idx, item in enumerate(st.session_state.manual_shopping_list):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"""
                        <div class="manual-item">
                            <div class="manual-item-name">📌 {item}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        if st.button("削除", key=f"remove_manual_{idx}", use_container_width=True):
                            st.session_state.manual_shopping_list.remove(item)
                            st.rerun()
            
            # コピー用リスト
            with st.expander("📋 コピー用リスト"):
                all_items = []
                for _, row in to_buy.iterrows():
                    all_items.append(f"□ {row['項目名']}")
                for _, row in low_stock_df.iterrows():
                    all_items.append(f"□ {row['項目名']}")
                for item in st.session_state.manual_shopping_list:
                    all_items.append(f"□ {item}")
                
                shopping_list = "\n".join(all_items)
                st.text_area("", shopping_list, height=200, label_visibility="collapsed")
        else:
            st.success("🎉 すべての在庫が十分です!")
    
    # タブ3: レシート読み取り
    with tab3:
        st.markdown('<h3 style="color: #1f2937;">📸 レシートを撮影して自動補充</h3>', unsafe_allow_html=True)
        st.info("レシートの写真をアップロードすると、購入した商品を自動で判別して在庫を補充します")
        
        uploaded_file = st.file_uploader("レシートの写真を選択", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        
        if uploaded_file is not None:
            col1, col2 = st.columns([1, 1])
            with col1:
                st.image(uploaded_file, caption="アップロードされたレシート", use_container_width=True)
            
            with col2:
                st.markdown('<h4 style="color: #1f2937;">🔍 解析中...</h4>', unsafe_allow_html=True)
                
                with st.spinner("レシートを読み取っています..."):
                    image_bytes = uploaded_file.read()
                    receipt_text = detect_text_from_image(image_bytes)
                    
                    if receipt_text:
                        st.success("✅ 読み取り完了!")
                        
                        with st.expander("📄 読み取ったテキスト"):
                            st.text(receipt_text)
                        
                        detected_items = parse_receipt_text(receipt_text, df)
                        
                        if detected_items:
                            st.markdown('<h4 style="color: #1f2937;">検出された商品:</h4>', unsafe_allow_html=True)
                            
                            for item in detected_items:
                                exact_match = df[df['項目名'] == item['name']]
                                
                                if not exact_match.empty:
                                    item_index = exact_match.index[0]
                                    col_a, col_b = st.columns([3, 1])
                                    
                                    with col_a:
                                        st.markdown(f'<div style="color: #1f2937;"><strong>{item["name"]}</strong> ({item["quantity"]}個) ✓ 完全一致</div>', unsafe_allow_html=True)
                                    
                                    with col_b:
                                        if st.button("追加", key=f"add_{item['name']}", use_container_width=True):
                                            current = int(df.at[item_index, '予備数'])
                                            df.at[item_index, '予備数'] = current + item['quantity']
                                            if update_data(sheet, df):
                                                st.success(f"✓ {item['name']}を追加しました!")
                                                st.rerun()
                        else:
                            st.warning("⚠️ 登録されている商品が見つかりませんでした")
                    else:
                        st.error("❌ テキストを読み取れませんでした。もう一度試してください。")
        else:
            st.markdown("""
            <div style="color: #1f2937;">
            
            ### 📱 使い方
            
            1. **レシートを撮影**してアップロード
            2. **自動で商品名を検出**
            3. **「追加」ボタン**で在庫を補充
            
            #### 💡 ヒント
            - レシート全体が写るように撮影してください
            - 明るい場所で撮影するとより正確です
            - 商品名が在庫リストに登録されている必要があります
            
            </div>
            """, unsafe_allow_html=True)

except Exception as e:
    st.error("エラーが発生しました")
    with st.expander("詳細"):
        st.code(str(e))