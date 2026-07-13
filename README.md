# threads-ai-research-bot-legal

Threads AI副業リサーチBOT（運営者：AI副業自動化ラボ）の
**プライバシーポリシー・データ削除案内を公開するための静的Webサイト**です。

このリポジトリはPublic運用を前提としています。

**現在のリリース準備状態（2026-07-13時点）**：公開情報4項目（問い合わせ先・発効日・最終更新日・
保持期間）はすべて正式値を反映済みで、プレースホルダーは解消済みです。`python scripts/validate_site.py --release`
がPASSすることを公開の条件とします（本README「6. 公開前検証方法」参照）。

## 1. このリポジトリの目的

- Meta App Reviewに提出する「プライバシーポリシーURL」「Data Deletion Instructions URL」として
  利用できる、公開アクセス可能な静的Webページを提供します。
- 本サイトはHTML・CSSのみで構成され、JavaScriptは使用していません。
- 外部CSS・外部JavaScript・外部フォント・CDN・アクセス解析・Cookie・広告・トラッキングピクセル・
  iframe・お問い合わせフォームは使用していません。

## 2. BOT本体コードを含まないこと

- 本リポジトリは、Threads AI副業リサーチBOT本体（別のPrivateリポジトリで管理）のソースコードを
  含みません。
- BOT本体のPrivateリポジトリのURL・内部パス・実行データを本リポジトリへコピーしないでください。
- BOT本体の`.env`（アクセストークン等）を本リポジトリへ含めないでください。

## 3. 公開対象ページ

| ファイル | 内容 |
|---|---|
| `index.html` | トップページ（サービス概要、日本語・英語） |
| `privacy.html` | プライバシーポリシー（日本語・英語） |
| `data-deletion.html` | データ削除案内（日本語・英語） |
| `404.html` | 存在しないページへアクセスした場合の案内 |
| `styles.css` | 共通スタイルシート |
| `robots.txt` | 検索エンジン向け公開設定 |
| `.nojekyll` | GitHub PagesでJekyll処理を行わないための設定 |

## 4. ローカル確認方法

Python標準ライブラリのHTTPサーバーを使用します。

```
python -m http.server 8000
```

以下のURLをブラウザで確認してください。

- http://localhost:8000/
- http://localhost:8000/privacy.html
- http://localhost:8000/data-deletion.html
- http://localhost:8000/404.html

確認後は、サーバーを起動したターミナルで `Ctrl + C` を押して終了してください。

## 5. ドラフト検証方法

プレースホルダーが残っていても警告として扱われ、それ以外の重大な問題がなければ成功します。

```
python scripts/validate_site.py --draft
```

## 6. 公開前検証方法

プレースホルダーが1つでも残っている場合、および問い合わせ先・発効日・最終更新日・保持期間が
未設定の場合は失敗します。秘密情報らしき文字列・内部リンク切れがある場合も失敗します。

```
python scripts/validate_site.py --release
```

**公開（GitHub Pagesの有効化、commit、push）の前に、必ず `--release` が成功することを確認してください。**

## 7. GitHub Pages有効化手順（ユーザーが実施）

Claude Codeはこの手順を代行しません。GitHubの設定変更・公開操作は行っていません。

1. GitHub上で `threads-ai-research-bot-legal` を開く
2. `Settings` を開く
3. `Pages` を開く
4. `Source` を `Deploy from a branch` にする
5. `Branch` を `main` にする
6. `Folder` を `/(root)` にする
7. `Save` を押す
8. 公開処理の完了を待つ
9. 公開URLをシークレットウィンドウ（キャッシュの影響を避けるため）で確認する

### 想定公開URL

- トップページ：https://ai-automation-lab-jp.github.io/threads-ai-research-bot-legal/
- プライバシーポリシー：https://ai-automation-lab-jp.github.io/threads-ai-research-bot-legal/privacy.html
- データ削除案内：https://ai-automation-lab-jp.github.io/threads-ai-research-bot-legal/data-deletion.html

カスタムドメイン・CNAMEファイルは使用しません。GitHub Actionsも使用しません。

## 8. プレースホルダー一覧（解消済み）

以下のプレースホルダーは、Phase 4D-2で正式な公開情報に置き換え、**すべて解消済み**です。
`index.html` / `privacy.html` / `data-deletion.html` のいずれにも残っていません
（`scripts/validate_site.py`の検出対象リストとしては、将来の回帰検知のために引き続き保持しています）。

| プレースホルダー（解消済み） | 反映先 | 反映内容 |
|---|---|---|
| `CONTACT_EMAIL_REQUIRED` | index.html / privacy.html / data-deletion.html | `ai.automation.lab.jp@gmail.com` |
| `EFFECTIVE_DATE_REQUIRED` | index.html / privacy.html | 2026年7月13日 / July 13, 2026 |
| `LAST_UPDATED_DATE_REQUIRED` | index.html / privacy.html | 2026年7月13日 / July 13, 2026 |
| `RETENTION_PERIOD_REQUIRED` | privacy.html | データ種別ごとの保持期間（本README「9. 保持期間」参照） |

今後、公開情報を更新する場合は、該当ファイルを直接編集し、`--release`検証がPASSすることを
確認してから反映してください。

## 9. 公開情報（反映済み）

- **公開問い合わせメールアドレス**：`ai.automation.lab.jp@gmail.com`
- **発効日**：2026年7月13日（July 13, 2026）
- **最終更新日**：2026年7月13日（July 13, 2026）
- **データ保持期間（保存上限）**：
  - raw JSON：取得日から最大90日
  - processed JSON：取得日から最大180日
  - 人間向けJSON／CSV／Markdownレポート：取得日から最大365日
  - ログ：生成日から最大90日
  - アクセストークン：有効期限、失効、連携解除、または不要となるまで
  - 上記は保存上限であり、無期限保存ではありません。**自動削除機能は現段階では未実装**であり、
    運営者が上記の上限を目安に**定期的な手動確認・削除**を行う運用です。削除依頼を受けた場合も、
    対象確認後に手動で削除します。

## 10. 問い合わせ先を公開する際の注意

- 公開問い合わせメールアドレスは、個人が特定されやすい形式（本名を含むメールアドレス等）で
  ある場合、公開範囲を運営者自身の判断で確認してください。
- 問い合わせ用メールアドレスの受信管理（迷惑メール対策等）は運営者の責任で行ってください。

## 11. 更新方法

1. 本リポジトリの該当HTMLファイルを編集する。
2. `python scripts/validate_site.py --draft` でHTML構造・内部リンク等に問題がないか確認する。
3. 公開情報がすべて確定している場合は `python scripts/validate_site.py --release` を実行する。
4. ローカルサーバーで表示を確認する（本README「4. ローカル確認方法」参照）。
5. 変更内容をコミットし、GitHub Pagesへ反映する（commit・pushはユーザー自身が行ってください）。

## 12. 秘密情報・実データを置かないこと

以下を本リポジトリへ**絶対に含めないでください**。

- Threadsアクセストークン、アプリシークレット、`.env`ファイルの内容
- 実際に取得した投稿ID・投稿本文・permalink・username等の実データ
- ローカル環境の絶対パス（例：`C:\Users\...`）
- BOT本体（Privateリポジトリ）のURL・内部ディレクトリ構成
- ターミナル履歴やAPIの生レスポンス

## 13. Privateリポジトリのコードをコピーしないこと

- BOT本体（`threads-ai-research-bot`、Private）のソースコード・設定ファイル・実行結果は、
  本リポジトリへ一切コピーしないでください。
- 本リポジトリに含めてよいのは、公開用に整理されたプライバシーポリシー・データ削除案内の
  文面と、それを表示するための静的HTML・CSSのみです。

## 14. GitHub Pages公開前チェックリスト

- [x] `python scripts/validate_site.py --draft` が成功する
- [x] `python scripts/validate_site.py --release` が成功する（プレースホルダーが残っていないこと）
- [x] プレースホルダーがすべて実際の値に置き換わっている（本README「8. プレースホルダー一覧（解消済み）」参照）
- [x] ローカルサーバーで `index.html` / `privacy.html` / `data-deletion.html` / `404.html` を
      目視確認した
- [x] 秘密情報・実データが含まれていないことを確認した
- [x] `git status` / `git diff` で意図しない変更が含まれていないことを確認した
- [ ] 上記すべてを確認したうえで、ユーザー自身がcommit・push・GitHub Pages有効化を行う

Claude Codeは、GitHub Pagesの有効化・GitHub API操作・commit・push・Meta App Review送信を
代行しません。上記はすべてユーザーが実施してください。
