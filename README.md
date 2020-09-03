# paper2html

[![License: AGPL](https://img.shields.io/badge/license-AGPL-blue)](https://opensource.org/licenses/AGPL-3.0)
[![Python Version](https://img.shields.io/badge/python-3.5-blue)](https://github.com/ktaaaki/paper2html)
[![Platform](https://img.shields.io/badge/platform-macos-yellow)](https://github.com/ktaaaki/paper2html)

It will convert a pdf paper to html pages. Only the format of single or double column is supported.

２段組の論文をhtml表示するツールです．

# 導入
## paper2htmlのインストール
依存ライブラリとpaper2htmlのインストール
```
> git clone https://github.com/ktaaaki/paper2html.git
> brew install mupdf-tools
> conda install -c conda-forge poppler
> pip install -e paper2html
```

## 使用方法
ipythonから
```
>>> import paper2html
>>> paper2html.open_paper_htmls("path-to-paper-file.pdf")
```
右クリックメニューまたは自動化から

- 変換したいpdfを選択して，`open pdf as html`を選択する
- `~/paper2html/downloads`にブラウザからpdfを保存する（自動的に変換が起動）

## ショートカットと右クリックメニューの作成（mac用）
クローンしたソースフォルダから`paper2html/open_downloaded_cache.workflow`と
`open pdf as html.workflow`をダブルクリックする．
`.zshrc`で自動的に有効になるconda環境でない場合は，
automatorからインストールされたworkflow内部のシェルスクリプトを変更してください．

ワークフローをインストールしたら，`~/paper2html/downloads`を右クリック＞サービス＞フォルダアクションを設定..を選択し，
サービスを確認
"Finder"が制限されたサービス"フォルダアクションを設定..."を使おうとしています．と出るのでサービスの実行を押し，
＋でスクリプトを追加，`open_downloaded_cache.workflow`を選択し，関連付ける，を選択する．

MacOSがCatalina以上であれば，設定＞セキュリティとプライバシー＞フルディスクアクセス　にFinder.appの追加が必要．
ワークフロー内のシェルスクリプトで(システムのpythonではなく)依存関係をインストールしたpythonを利用するため．
設定しないと`Operation is not permitted`のエラーが出るので注意．

※ `~/paper2html/downloads`のファイルは容量制限を超えると自動削除されるので注意．
容量はautomatorから変更可能（clean_downloadsの2番めの引数，デフォルトで1GB）．
自動削除なしVer.は`open_downloaded.workflow`．
