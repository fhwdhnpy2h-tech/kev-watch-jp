# KEV Watch JP — 自動更新される脆弱性検索サイト

CISA Known Exploited Vulnerabilities（KEV）カタログを毎日取得し、静的サイトを自動公開するスターターキットです。

## 何が自動化される？
- 公式 JSON の取得と形式検証
- 脆弱性の製品名・CVE・追加日による検索
- HTML / JSON / CSV / RSS の生成
- GitHub Actions による毎日 8:17（日本時間）のビルドと GitHub Pages 公開

**現時点では有料契約、メール通知、顧客管理は未実装です。売上は自動では発生しません。**

## 0. 必要なもの
GitHub アカウント（無料プランから始められます）。ブラウザーで設定すれば、PC を常時起動する必要はありません。

## 1. リポジトリ作成
1. https://github.com/new にアクセス
2. Repository name を `kev-watch-jp` にする
3. `Public` を選択する。会社資料・秘密情報は入れない
4. `Create repository` を押す
5. ここで提供した ZIP を解凍し、フォルダ内の **すべてのファイルを** リポジトリのルートにアップロードする。隠しフォルダ `.github/workflows/publish.yml` も必須（アップロードが難しければ Web 画面で `.github/workflows/publish.yml` を新規作成し内容を貼り付ける）
6. `Commit changes` を押す

## 2. Pages 設定
1. リポジトリの `Settings` → `Pages`
2. `Build and deployment` → `Source` を **GitHub Actions** にする
3. `Actions` → `Daily KEV update and site publishing` → `Run workflow` を押す
4. 緑のチェックを確認する。Pages URL は `Settings > Pages` などに表示されます（通常 `https://ユーザー名.github.io/kev-watch-jp/`）
5. 掲載件数・検索フォームが表示されるか確認する

## 3. 自動化の確認
`.github/workflows/publish.yml` の cron と timezone により **毎日午前8:17 JSTを目安**に起動。GitHub 側の事情により遅延、スキップ、長期非活動による停止の可能性があるため、定期的に `Actions` の実行履歴を確認してください。

## 4. 手元でテスト（任意）
Python 3 で `KEV_FIXTURE=tests/sample.json python3 build.py` を実行。Windows PowerShell の場合は `$env:KEV_FIXTURE='tests/sample.json'; python build.py`。
テストデータを使わない場合、CISA公式データをインターネットから取得します。
`site/index.html` をブラウザで直接開くと JSON を読めないことがあります。`python -m http.server 8000 --directory site` を起動し `http://localhost:8000` にアクセスしてください。

## 5. マネタイズの現実的な順序
1. 公開後、ターゲットユーザー5〜10人に使い勝手を確認
2. メールによる製品別通知（使用している製品・顧客情報の保存と安全管理が必要）への支払い意思を検証
3. 有料需要が確認できてから Stripe Payment Links などで契約課金を導入
4. 購入者だけにサービスを提供する認可、解約、プライバシーポリシー、特商法表示、サポート体制を実装

## 注意
- CISA KEVは「既知の悪用が確認された脆弱性」の一覧であり、すべての脆弱性は網羅しません。
- 本サービスに表示された英語原文は対処方針や適用バージョンを確定しません。ベンダー発表を確認してください。
- 公式取得に失敗した日は公開処理をエラー終了させ、古いサイトが残ることがあります。失敗に気づけるよう Actions 通知を有効にしてください。
- GitHub Pages は事業運営・EC・商用SaaS のホスティングを認めていません。本キットの Pages 利用は非商用の技術検証・ポートフォリオ用途に限定してください。**収益化する前に Cloudflare Pages / Netlify / Vercel 等の利用規約を確認し、商用利用可能な環境へ移行してください。** GitHub Actions を更新処理に使い、静的ファイルを別ホストへデプロイする構成にも拡張できます。
- GoogleやCISAの認定サービスではありません。
