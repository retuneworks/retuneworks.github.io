# RETUNE WORKS Website

RETUNE WORKS公式サイトのGitHub Pages向けMVPです。HTML / CSS / Vanilla JavaScriptだけで動作し、ビルドは不要です。

## Pages

- / — ブランドの玄関
- /instruments/ — 海外向け楽器・機材事業（英語）
- /instruments/journal/ — 楽器記事カテゴリー
- /ai/ — 国内・地域向け生成AI活動（日本語）
- /ai/journal/ — AI記事カテゴリー
- /about/ — ブランド思想
- /contact/ — 問い合わせ案内

## Local preview

ルートディレクトリで「python -m http.server 8000」を実行し、http://localhost:8000/ を開きます。file:// 直開きではルート相対リンクを正しく確認できません。

## Publish with GitHub Pages

1. GitHubの retuneworks/retuneworks.github.io リポジトリへ、このフォルダの中身をpushします。
2. リポジトリの Settings → Pages を開きます。
3. Deploy from a branch、ブランチ main、フォルダ /(root) を選び保存します。
4. 公開後 https://retuneworks.github.io/ を確認します。

## Before launch

- contact/index.html のTODOを公式メールアドレスへ置き換える
- 実機でモバイル表示と各外部リンクを最終確認する
- 必要に応じて記事を追加する

## Image assets

assets/images/instruments-hero.png と assets/images/ai-hero.png は、本MVP用にOpenAIの組み込み画像生成で作成した背景画像です。
