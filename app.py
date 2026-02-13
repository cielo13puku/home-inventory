import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# ページの設定
st.set_page_config(page_title="Hirata家 在庫管理", layout="centered")

st.title("🏠 Hirata家 在庫 & 買い物リスト")

# 1. 接続設定
# URLを直接指定します
url = "https://docs.google.com/spreadsheets/d/1xLJxgm9SxveTBPJz1swAygGrc4zdoAD1GoRMLLaNgs0/edit?usp=sharing"

try:
    # 接続の初期化
    # secrets.tomlの設定を明示的に「service_account」として使用するように指示します
    conn = st.connection("gsheets", type=GSheetsConnection)

    # 2. 最新データの読み込み
    df = conn.read(spreadsheet=url, ttl=0)

    # 3. 在庫ステータスと更新処理
    st.header("📦 現在の在庫ステータス")

    for index, row in df.iterrows():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if int(row['予備数']) < int(row['補充しきい値']):
                st.error(f"**{row['項目名']}**\n(予備: {row['予備数']})")
            else:
                st.write(f"**{row['項目名']}**\n(予備: {row['予備数']})")
                
        with col2:
            if st.button("予備-1", key=f"minus_{index}"):
                new_val = max(0, int(row['予備数']) - 1)
                df.at[index, '予備数'] = new_val
                # 【重要】書き込み時にURLとデータを明示
                conn.update(spreadsheet=url, data=df)
                st.rerun()
                
        with col3:
            if st.button("補充+1", key=f"plus_{index}"):
                new_val = int(row['予備数']) + 1
                df.at[index, '予備数'] = new_val
                # 【重要】書き込み時
                conn.update(spreadsheet=url, data=df)
                st.rerun()

    st.divider()
    st.header("🛒 今日の買い物リスト")
    to_buy = df[df['予備数'] < df['補充しきい値']]
    if not to_buy.empty:
        for item in to_buy['項目名']:
            st.error(f"⚠️ **{item}** を買ってください！")
    else:
        st.success("今のところ在庫はバッチリです！")

except Exception as e:
    st.error(f"🚨 実行エラーが発生しました。")
    st.info(f"エラー詳細: {e}")
    
    # 診断情報の表示
    with st.expander("🛠️ 認証の診断ログ"):
        if "connections" in st.secrets and "gsheets" in st.secrets.connections:
            st.write("・secrets.toml の読込: ✅ 成功")
            conf = st.secrets.connections.gsheets
            st.write(f"・認証タイプ: {conf.get('type', '⚠️未設定')}")
            st.write(f"・メールアドレス: {conf.get('client_email', '⚠️未設定')}")
        else:
            st.write("・secrets.toml の読込: ❌ 失敗（場所やファイル名を確認してください）")
