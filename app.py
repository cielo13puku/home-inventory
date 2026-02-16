import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json

# ページの設定
st.set_page_config(
    page_title="Hirata家 在庫管理",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stat-box {
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# タイトル
st.markdown('<div class="main-header">🏠 Hirata家 在庫管理システム</div>', unsafe_allow_html=True)

# Google Sheets接続関数
@st.cache_resource
def get_google_sheet():
    """Google Sheetsに接続"""
    try:
        # secrets.tomlから認証情報を取得
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # secrets.tomlの認証情報を辞書形式に変換
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
        
        # スプレッドシートを開く
        sheet_url = "https://docs.google.com/spreadsheets/d/1xLJxgm9SxveTBPJz1swAygGrc4zdoAD1GoRMLLaNgs0/edit?usp=sharing"
        sheet = client.open_by_url(sheet_url).sheet1
        
        return sheet
    except Exception as e:
        st.error(f"Google Sheets接続エラー: {e}")
        return None

# データ読み込み関数
def load_data(sheet):
    """スプレッドシートからデータを読み込む"""
    try:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # 数値型に変換
        df['予備数'] = pd.to_numeric(df['予備数'], errors='coerce').fillna(0).astype(int)
        df['補充しきい値'] = pd.to_numeric(df['補充しきい値'], errors='coerce').fillna(0).astype(int)
        
        return df
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
        return None

# データ更新関数
def update_data(sheet, df):
    """スプレッドシートにデータを書き込む"""
    try:
        # DataFrameをリストに変換
        data = [df.columns.tolist()] + df.values.tolist()
        
        # シートをクリアして新しいデータを書き込む
        sheet.clear()
        sheet.update(data, 'A1')
        
        return True
    except Exception as e:
        st.error(f"データ更新エラー: {e}")
        return False

# メイン処理
try:
    # Google Sheetsに接続
    sheet = get_google_sheet()
    
    if sheet is None:
        st.error("Google Sheetsに接続できませんでした。secrets.tomlを確認してください。")
        
        with st.expander("📝 secrets.tomlの設定方法"):
            st.markdown("""
            ### 1. `.streamlit`フォルダを作成
            プロジェクトのルートディレクトリに `.streamlit` フォルダを作成してください。
            
            ### 2. `secrets.toml`ファイルを作成
            `.streamlit`フォルダ内に `secrets.toml` ファイルを作成し、以下の内容を記載:
            
            ```toml
            [gsheets]
            type = "service_account"
            project_id = "your-project-id"
            private_key_id = "your-private-key-id"
            private_key = "-----BEGIN PRIVATE KEY-----\\nYour private key here\\n-----END PRIVATE KEY-----\\n"
            client_email = "your-service-account@your-project.iam.gserviceaccount.com"
            client_id = "your-client-id"
            auth_uri = "https://accounts.google.com/o/oauth2/auth"
            token_uri = "https://oauth2.googleapis.com/token"
            auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
            client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
            ```
            
            ### 3. スプレッドシートの共有設定
            - Google Sheetsで対象のスプレッドシートを開く
            - 「共有」ボタンをクリック
            - Service Accountのメールアドレス(`client_email`)を追加
            - 「編集者」権限を付与
            """)
        st.stop()
    
    # データを読み込む
    df = load_data(sheet)
    
    if df is None or df.empty:
        st.warning("データが見つかりませんでした。スプレッドシートを確認してください。")
        st.stop()
    
    # サイドバーに統計情報
    with st.sidebar:
        st.header("📊 在庫サマリー")
        
        total_items = len(df)
        critical_items = len(df[df['予備数'] < df['補充しきい値']])
        ok_items = total_items - critical_items
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("総アイテム数", total_items)
        with col2:
            st.metric("要補充", critical_items, delta=None if critical_items == 0 else f"-{critical_items}")
        
        st.divider()
        
        # フィルター機能
        st.subheader("🔍 フィルター")
        view_mode = st.radio(
            "表示モード",
            ["すべて表示", "要補充のみ", "在庫OKのみ"],
            index=0
        )
        
        st.divider()
        
        # 一括操作
        st.subheader("⚡ 一括操作")
        if st.button("🔄 データを再読み込み", use_container_width=True):
            st.cache_resource.clear()
            st.rerun()
        
        st.info("💡 ボタンをタップして在庫を増減できます")
    
    # メインエリア:タブで整理
    tab1, tab2, tab3 = st.tabs(["📦 在庫管理", "🛒 買い物リスト", "📈 データ一覧"])
    
    # --- タブ1: 在庫管理 ---
    with tab1:
        # フィルター適用
        if view_mode == "要補充のみ":
            display_df = df[df['予備数'] < df['補充しきい値']]
        elif view_mode == "在庫OKのみ":
            display_df = df[df['予備数'] >= df['補充しきい値']]
        else:
            display_df = df
        
        if display_df.empty:
            st.info("表示するアイテムがありません")
        else:
            for index, row in display_df.iterrows():
                current_stock = int(row['予備数'])
                threshold = int(row['補充しきい値'])
                
                # ステータス判定
                if current_stock < threshold:
                    if current_stock == 0:
                        status_icon = "🚨"
                        status_text = "在庫切れ"
                        color = "#dc3545"
                    else:
                        status_icon = "⚠️"
                        status_text = "要補充"
                        color = "#ffc107"
                else:
                    status_icon = "✅"
                    status_text = "在庫OK"
                    color = "#28a745"
                
                # カード表示
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                
                with col1:
                    st.markdown(f"### {status_icon} {row['項目名']}")
                    st.caption(f"しきい値: {threshold}個")
                
                with col2:
                    st.markdown(f"<h2 style='color: {color}; margin: 0;'>{current_stock}個</h2>", unsafe_allow_html=True)
                    st.caption(status_text)
                
                with col3:
                    if st.button("➖", key=f"minus_{index}", use_container_width=True):
                        df.at[index, '予備数'] = max(0, current_stock - 1)
                        if update_data(sheet, df):
                            st.success("更新しました!")
                            st.rerun()
                
                with col4:
                    if st.button("➕", key=f"plus_{index}", use_container_width=True):
                        df.at[index, '予備数'] = current_stock + 1
                        if update_data(sheet, df):
                            st.success("更新しました!")
                            st.rerun()
                
                st.divider()
    
    # --- タブ2: 買い物リスト ---
    with tab2:
        st.header("🛒 今日の買い物リスト")
        
        to_buy = df[df['予備数'] < df['補充しきい値']].copy()
        
        if not to_buy.empty:
            st.warning(f"**{len(to_buy)}個のアイテム**を補充する必要があります")
            
            for idx, (index, row) in enumerate(to_buy.iterrows(), 1):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    shortage = int(row['補充しきい値']) - int(row['予備数'])
                    st.markdown(f"### {idx}. {row['項目名']}")
                    st.caption(f"現在: {row['予備数']}個 | 不足: {shortage}個")
                
                with col2:
                    if st.button("✓ 購入済み", key=f"bought_{index}", use_container_width=True):
                        df.at[index, '予備数'] = int(row['補充しきい値'])
                        if update_data(sheet, df):
                            st.success(f"{row['項目名']}を補充しました!")
                            st.rerun()
                
                st.divider()
            
            # リストをコピー用に出力
            with st.expander("📋 リストをコピー"):
                shopping_list = "\n".join([f"・{row['項目名']}" for _, row in to_buy.iterrows()])
                st.text_area("買い物リスト", shopping_list, height=200)
        else:
            st.success("🎉 すべての在庫が十分です!")
            st.balloons()
    
    # --- タブ3: データ一覧 ---
    with tab3:
        st.header("📈 在庫データ一覧")
        
        # データフレームを見やすく表示
        display_table = df.copy()
        display_table['ステータス'] = display_table.apply(
            lambda row: '🚨 在庫切れ' if row['予備数'] == 0
            else '⚠️ 要補充' if row['予備数'] < row['補充しきい値']
            else '✅ OK',
            axis=1
        )
        
        st.dataframe(
            display_table[['項目名', '予備数', '補充しきい値', 'ステータス']],
            use_container_width=True,
            hide_index=True
        )
        
        # CSVダウンロード
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 CSVでダウンロード",
            data=csv,
            file_name="inventory_data.csv",
            mime="text/csv"
        )

except Exception as e:
    st.error("🚨 予期しないエラーが発生しました")
    st.code(str(e))
    
    with st.expander("🔍 デバッグ情報"):
        import traceback
        st.code(traceback.format_exc())