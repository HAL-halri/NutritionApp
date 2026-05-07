import streamlit as st
import google.generativeai as genai
import json
import os
import pandas as pd
from datetime import datetime, date, timedelta
from PIL import Image
import requests  # 👈 認証の通信に必要なので追加しました！

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Firebaseの初期化
if not firebase_admin._apps:
    key_dict = json.loads(st.secrets["FIREBASE_KEY"])
    cred = credentials.Certificate(key_dict)
    firebase_admin.initialize_app(cred)
db = firestore.client()

# --- API設定 ---
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
FIREBASE_WEB_API_KEY = st.secrets["FIREBASE_WEB_API_KEY"] # 👈 ログイン用に復活

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- アプリ構造 ---
st.set_page_config(page_title="Gemini栄養管理アプリ", layout="wide")

# ==========================================
# 🌟 メモ帳（Session State）の準備
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_uid" not in st.session_state:
    st.session_state["user_uid"] = None

# ==========================================
# 🌟 ログイン・新規登録用の関数
# ==========================================
def sign_up_with_email_and_password(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    r = requests.post(url, json=payload)
    return r.json()

def sign_in_with_email_and_password(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    r = requests.post(url, json=payload)
    return r.json()

# ==========================================
# 🌟 ログインしていない時の画面
# ==========================================
if not st.session_state["logged_in"]:
    st.title("🔐 ログイン")
    tab_login, tab_signup = st.tabs(["ログイン", "新規登録"])

    with tab_login:
        email = st.text_input("email:", key="login_email")
        password = st.text_input("password:", type="password", key="login_pw")
        if st.button("log in"):
            response = sign_in_with_email_and_password(email, password)
            if "error" not in response:
                st.session_state["logged_in"] = True
                st.session_state["user_uid"] = response["localId"]
                st.rerun()
            else:
                st.error("ログインに失敗しました。")

    with tab_signup:
        new_email = st.text_input("email (新規):", key="signup_email")
        new_password = st.text_input("password (新規・6文字以上):", type="password", key="signup_pw")
        if st.button("新規登録してログイン"):
            response = sign_up_with_email_and_password(new_email, new_password)
            if "error" not in response:
                st.session_state["logged_in"] = True
                st.session_state["user_uid"] = response["localId"]
                st.success("登録が完了しました！")
                st.rerun()
            else:
                st.error(f"登録に失敗しました: {response['error']['message']}")

# ==========================================
# 🌟 ログインしている時の画面（本編）
# ==========================================
else:
    st.title("🍽️ パーソナルAI栄養管理アプリ")

    # ログアウトボタンをサイドバーの一番上に配置
    if st.sidebar.button("ログアウト"):
        st.session_state["logged_in"] = False
        st.session_state["user_uid"] = None
        st.rerun()
    st.sidebar.divider()

    # --- データ管理用関数 ---
    def load_json(path, default):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return default

    def save_json(path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    # 🌟 ファイル名をログインしているUIDで分ける
    uid = st.session_state["user_uid"]
    SETTINGS_FILE = f"user_settings_{uid}.json"
    HISTORY_FILE = f"nutrition_history_{uid}.json"

    # データの読み出し
    user_data = load_json(SETTINGS_FILE, {"age": 25, "gender": "男性", "height": 170.0, "weight": 65.0})
    history_data = load_json(HISTORY_FILE, {})

    # --- サイドバー：プロフィール設定 ---
    with st.sidebar:
        st.header("👤 プロフィール")
        age = st.number_input("年齢", 0, 120, user_data["age"])
        gender = st.selectbox("性別", ["男性", "女性"], index=0 if user_data["gender"]=="男性" else 1)
        height = st.number_input("身長 (cm)", 0.0, 250.0, float(user_data["height"]))
        weight = st.number_input("体重 (kg)", 0.0, 300.0, float(user_data["weight"]))
        
        if st.button("プロフィールを保存"):
            save_json(SETTINGS_FILE, {"age": age, "gender": gender, "height": height, "weight": weight})
            st.success("保存しました！")
            
        st.divider()
        st.header("⚙️ データの管理")
        
        # 期間削除のUI
        st.subheader("期間指定で削除")
        del_start = st.date_input("開始日", date.today() - timedelta(days=7), key="del_s")
        del_end = st.date_input("終了日", date.today(), key="del_e")
        
        if st.checkbox("上記期間のデータをまとめて削除"):
            if st.button("⚠️ 一度削除すると復元できません ⚠️"):
                date_period = del_end - del_start
                dates_to_delete = [str(del_start + timedelta(days=i)) for i in range(date_period.days + 1)]
                
                count = 0
                for target_date in dates_to_delete:
                    if target_date in history_data:
                        del history_data[target_date]
                        count += 1
                
                if count > 0:
                    save_json(HISTORY_FILE, history_data)
                    st.success(f"{count}日分のデータを削除しました。")
                    st.rerun()
                else:
                    st.info("該当する期間にデータはありませんでした。")
                    
        # 目標計算
        bmr = (13.7 * weight + 5.0 * height - 6.8 * age + 66) if gender == "男性" else (9.6 * weight + 1.8 * height - 4.7 * age + 665)
        target_cal = int(bmr * 1.5)
        targets = {
            "calories": target_cal,
            "protein": int(weight * 1.2),
            "fat": int(target_cal * 0.25 / 9),
            "carbs": int(target_cal * 0.6 / 4)
        }
        st.info(f"目標: {targets['calories']} kcal / 日")

    # --- 1日グラフ表示用の共通関数 ---
    def display_daily_progress(name, current, target, unit):
        # targetが0の場合のエラー回避
        if target <= 0: return
        ratio = current / target
        percentage = int(ratio * 100)
        if percentage < 90: color = "#ff4b4b" # 赤
        elif percentage <= 110: color = "#00cc66" # 緑
        else: color = "#ffc107" # 黄色
        
        st.write(f"**{name}**: {current}{unit} / 目標{target}{unit} ({percentage}%)※")
        
        max_scale = 1.3 
        fill_width = min(ratio / max_scale, 1.0) * 100
        target_line = (1.0 / max_scale) * 100
        
        st.markdown(f"""
        <div style="position: relative; width: 100%; background-color: #e6e6e6; border-radius: 5px; margin-bottom: 25px; height: 16px;">
            <div style="width: {fill_width}%; height: 100%; background-color: {color}; border-radius: 5px;"></div>
            <div style="position: absolute; left: {target_line}%; top: -4px; height: 24px; border-left: 2px dashed #333;"></div>
        </div>
        """, unsafe_allow_html=True)

    # --- メインエリア：タブ分け ---
    tab1, tab2 = st.tabs(["📝 今日の食事入力", "📊 期間分析"])

    # --- Tab1: 食事入力 ---
    with tab1:
        selected_date = st.date_input("記録・確認する日付", date.today())
        date_str = str(selected_date)
        
        if date_str in history_data:
            col_header, col_del = st.columns([3, 1])
            with col_header:
                st.success(f"✅ {date_str} のデータ")
            with col_del:
                if st.button("🗑️ この日を削除"):
                    del history_data[date_str]
                    save_json(HISTORY_FILE, history_data)
                    st.rerun()

            data = history_data[date_str]
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("カロリー", f"{data.get('calories', 0)} kcal")
            col2.metric("タンパク質", f"{data.get('protein', 0)} g")
            col3.metric("脂質", f"{data.get('fat', 0)} g")
            col4.metric("炭水化物", f"{data.get('carbs', 0)} g")

            st.info("※1日の目標摂取量を100%としています。")

            display_daily_progress("カロリー", data.get('calories', 0), targets['calories'], "kcal")
            display_daily_progress("タンパク質", data.get('protein', 0), targets['protein'], "g")
            display_daily_progress("脂質", data.get('fat', 0), targets['fat'], "g")
            display_daily_progress("炭水化物", data.get('carbs', 0), targets['carbs'], "g")
            
            st.markdown("### Gemini栄養士からのフィードバック")
            
            if "advice" in data:
                st.info(data["advice"])
            
            if st.button("✨ この日の食事をGeminiに分析してもらう"):
                with st.spinner("栄養バランスを細かく分析中..."):
                    meals_text = data.get('meals', '記録なし')
                    advice_prompt = f"""
                    あなたはプロの厳しくも優しい専属栄養士です。以下の1日の食事内容と栄養素の達成状況を見て、200〜300文字程度でアドバイスをください。
                    ・大きくオーバー、または不足している栄養素を具体的に指摘してください。
                    ・「この食事のこのメニューを〇〇に変えると良かった」「明日は〇〇を多めに食べましょう」など、具体的な食材や料理名を出して改善案を提示してください。
                    
                    【目標】カロリー:{targets['calories']}kcal, タンパク質:{targets['protein']}g, 脂質:{targets['fat']}g, 炭水化物:{targets['carbs']}g
                    【実際】カロリー:{data.get('calories',0)}kcal, タンパク質:{data.get('protein',0)}g, 脂質:{data.get('fat',0)}g, 炭水化物:{data.get('carbs',0)}g
                    【食事内容】{meals_text}
                    """
                    
                    try:
                        advice_res = model.generate_content(advice_prompt)
                        data["advice"] = advice_res.text
                        history_data[date_str] = data
                        save_json(HISTORY_FILE, history_data)
                        st.rerun()
                    except Exception as e:
                        st.error(f"アドバイスの生成に失敗しました: {e}")

        else:
            st.info("この日の記録はまだありません。")
        
        st.divider()
        st.subheader("新しい記録を入力（写真でもOK！）")
        
        uploaded_file = st.file_uploader("食事の写真をアップロード（任意）", type=['png', 'jpg', 'jpeg'])
        if uploaded_file is not None:
            img = Image.open(uploaded_file)
            st.image(img, caption="アップロードされた写真", use_container_width=True)

        col_in1, col_in2 = st.columns(2)
        with col_in1:
            breakfast = st.text_input("朝食", key="bf", placeholder="例：トースト（写真がある場合は空欄でもOK）")
            lunch = st.text_input("昼食", key="ln")
        with col_in2:
            dinner = st.text_input("夕食", key="dn")
            snack = st.text_input("間食", key="sn")

        if st.button("栄養素を計算して保存"):
            if not (breakfast or lunch or dinner or snack) and uploaded_file is None:
                st.error("食事の内容を入力するか、写真をアップロードしてください。")
            else:
                with st.spinner("Geminiが画像を解析して計算中..."):
                    prompt = f"""
                    栄養士として、以下の食事情報（テキストおよび画像）から1日の合計栄養素を推測し、
                    JSON(calories, protein, fat, carbs)のみで返して。余計な文やマークダウンは不要。
                    テキスト入力：朝:{breakfast}, 昼:{lunch}, 夜:{dinner}, 間食:{snack}
                    ※画像が添付されている場合は、画像内の食べ物もテキストの食事に加えて（あるいは補完して）合算すること。
                    """
                    
                    try:
                        if uploaded_file is not None:
                            res = model.generate_content([prompt, img])
                            meals_record = f"【写真あり】 朝:{breakfast}, 昼:{lunch}, 夜:{dinner}, 間食:{snack}"
                        else:
                            res = model.generate_content(prompt)
                            meals_record = f"朝:{breakfast}, 昼:{lunch}, 夜:{dinner}, 間食:{snack}"

                        clean_res = res.text.replace("```json", "").replace("```", "").strip()
                        data = json.loads(clean_res)
                        
                        data["meals"] = meals_record
                        history_data[date_str] = data
                        save_json(HISTORY_FILE, history_data)
                        
                        # 🌟 Firebaseの保存先を「user_A」から「ログイン中のUID」に変更！
                        doc_ref = db.collection("users").document(st.session_state["user_uid"]).collection("meals").document(date_str)
                        doc_ref.set({
                            "date": date_str,
                            "age": age,
                            "gender": gender,
                            "target_cal": target_cal,
                            "ai_analysis": data,
                            "timestamp": firestore.SERVER_TIMESTAMP 
                        })
            
                        st.success("✨ データベースに記録を保存しました！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"エラーが発生しました: {e}")
                        if 'res' in locals():
                            st.write("Geminiの返答:", res.text)

    # --- Tab2: 期間分析 ---
    with tab2:
        st.header("📈 不足量の合計分析")
        if not history_data:
            st.warning("分析するデータがまだありません。まずは食事を入力してください。")
        else:
            period = st.selectbox("分析期間", ["直近1週間", "直近1ヶ月"])
            days = 7 if period == "直近1週間" else 30
            
            end_d = date.today()
            start_d = end_d - timedelta(days=days-1)
            report_dates = [str(start_d + timedelta(days=i)) for i in range(days)]
            
            total_intake = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}
            recorded_days = 0
            for d in report_dates:
                if d in history_data:
                    recorded_days += 1
                    for k in total_intake:
                        total_intake[k] += history_data[d].get(k, 0)
            
            st.write(f"期間: {start_d} 〜 {end_d} （記録済み: {recorded_days}日分）")
            
            total_targets = {k: v * recorded_days for k, v in targets.items()}
            
            if recorded_days > 0:
                diff_data = {
                    "栄養素": ["カロリー", "タンパク質", "脂質", "炭水化物"],
                    "不足量": [total_targets[k] - total_intake[k] for k in ["calories", "protein", "fat", "carbs"]]
                }
                df = pd.DataFrame(diff_data)
                df_chart = df.set_index("栄養素")
                st.bar_chart(df_chart)
                st.write("💡 **グラフの見方**: 正の数値は「目標までの不足分」、負の数値は「摂りすぎた分」です。")
            else:
                st.info("選択された期間内に記録がありません。")