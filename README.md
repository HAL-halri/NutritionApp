# 手軽に使える健康管理アプリ

## 📖 アプリの概要
「毎日の食事記録が面倒で続かない」という自身の課題を解決するために開発した、写真やテキストから手軽に栄養管理ができるWebアプリケーションです。
Gemini APIを活用し、食事の写真やテキストから摂取カロリーとPFC（タンパク質・脂質・炭水化物）を自動算出することで、入力のハードルを極限まで下げました。

- **アプリURL:** https://nutritionapp-faxpy6zqm8ew4jl99fwowd.streamlit.app/
  （※無料サーバーを利用しているため、初回読み込みに数十秒かかる場合があります）

## ✨ 主な機能
- **自動栄養素算出:** Gemini APIによる画像・テキストからのPFCバランス自動解析
- **ユーザー認証機能:** Firebase Authenticationを用いた安全なログイン・アカウント作成
- **ユーザー別データ管理:** Firestoreを活用した、他者のデータと混在しない安全な履歴管理
- **ダッシュボード表示:** 摂取した栄養素のグラフ表示
- **長期間のデータ保存:** 複数期間のデータ保存による持続性の高い健康管理を実現

## 📸 画面イメージ
### ログイン後の画面
<img width="1278" height="672" alt="スクリーンショット 2026-06-18 222812" src="https://github.com/user-attachments/assets/25037a09-e72e-457a-87b0-42d627fd96ab" />
### 食事データの分析結果
<img width="984" height="574" alt="スクリーンショット 2026-06-18 222748" src="https://github.com/user-attachments/assets/2f9df40c-649a-47d4-91ae-17d5206ef8f1" />




## 🛠 使用技術
- **フロントエンド / バックエンド:** Python (Streamlit)
- **データベース:** Firebase (Cloud Firestore)
- **認証機能:** Firebase Authentication
- **外部API:** Google Gemini API
- **インフラ・デプロイ:** Streamlit Community Cloud
- **バージョン管理:** Git / GitHub

## 💡 開発における工夫点・注力したこと
**1. 複数ユーザーを前提とした安全なデータ設計**
当初は単一ユーザーを想定していましたが、実際の運用を見据えて複数ユーザー対応に再設計しました。Firestoreにおいて、ユーザーIDをドキュメントキーとしてプロフィールや履歴データを紐付ける構造にし、セキュアなデータ管理を実現しています。

**2. 生成AIによる開発プロセスの効率化**
Gemini等の生成AIを単なる機能（API）として組み込むだけでなく、開発工程そのものにも活用しました。AIからの提案を鵜呑みにせず、自分の要件に合わせて検証・取捨選択しながら実装を進めることで、約1ヶ月という短期間での基本機能実装を達成しました。

## 🚀 ローカルでの動かし方
```bash
# 1. リポジトリのクローン
git clone https://github.com/HAL-halri/NutritionApp.git

# 2. ディレクトリの移動
cd NutritionApp

# 3. 必要なライブラリのインストール
pip install -r requirements.txt

# 4. アプリの起動
streamlit run app.py

# 5. 環境変数の設定
【注意】ローカルで実行する際は、.streamlit/secrets.toml を作成し、以下のキーを設定する必要があります。

GOOGLE_API_KEY

FIREBASE_KEY (JSON形式)

FIREBASE_WEB_API_KEY
