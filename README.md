# paper2html

[![License: AGPL](https://img.shields.io/badge/license-AGPL-blue)](https://opensource.org/licenses/AGPL-3.0)
[![Python Version](https://img.shields.io/badge/python-3.5|3.7-blue)](https://github.com/ktaaaki/paper2html)
[![Platform](https://img.shields.io/badge/platform-macos|linux-yellow)](https://github.com/ktaaaki/paper2html)

It will convert a pdf paper to html pages. Only the format of single or double column is supported.

２段組の論文をhtml表示するツールです．

## インストール
外部ツールとして，popplerとmu-pdfに依存しているので，環境に合わせてインストールしてください．
### ubuntuの場合
```
> git clone https://github.com/ktaaaki/paper2html.git
> sudo apt install mupdf mupdf-tools poppler-utils poppler-data
> pip install -e paper2html
```
### macの場合
brew + pyenv + condaの環境でのみ動作確認しています．
```
> git clone https://github.com/ktaaaki/paper2html.git
> brew install mupdf-tools
> conda install -c conda-forge poppler
> pip install -e paper2html
```

## 使用方法
ダウンロードしたpdfを指定して実行することで，htmlページが自動的に開きます．

pythonから
```
> python paper2html/main.py path-to-paper-file.pdf
```
ipythonから
```
>>> import paper2html
>>> paper2html.open_paper_htmls("path-to-paper-file.pdf")
```
macでは下記のインストールを済ませれば，右クリックメニューまたは自動化から

- 変換したいpdfを選択して，`open pdf as html`を選択する
- `~/paper2html/downloads`にブラウザからpdfを保存する（自動的に変換が起動）

ことで利用可能です．

## フォルダアクションと右クリックメニューの作成（mac用）
macではさらに操作を短縮するために，ワークフローが利用できます．

### 右クリックメニューのインストール
クローンしたソースフォルダから`paper2html/open pdf as html.workflow`
をダブルクリックしてautomatorに登録します．

`.zshrc`で自動的に有効になるconda環境でない場合は，
automatorからインストールされたworkflow内部のシェルスクリプトを変更してください．

MacOSがCatalina以上であれば，設定＞セキュリティとプライバシー＞フルディスクアクセス にFinder.appの追加が必要です．
ワークフロー内のシェルスクリプトで(システムのpythonではなく)依存関係をインストールしたpythonを利用するため．
設定しないと`Operation is not permitted`のエラーが出るので注意してください．

### フォルダアクションのインストール
クローンしたソースフォルダから`paper2html/open_downloaded_cache.workflow`
をダブルクリックしてautomatorに登録します．

`.zshrc`で自動的に有効になるconda環境でない場合は，
automatorからインストールされたworkflow内部のシェルスクリプトを変更してください．

MacOSがCatalina以上であれば，設定＞セキュリティとプライバシー＞フルディスクアクセス にFinder.appの追加が必要です．
ワークフロー内のシェルスクリプトで(システムのpythonではなく)依存関係をインストールしたpythonを利用するため．
設定しないと`Operation is not permitted`のエラーが出るので注意してください．

次に，pdfのダウンロード先のフォルダを右クリックし，右クリックメニュー＞サービス＞"フォルダアクションを設定.."を選択し，
"サービスを確認"を押すと，"Finder"が制限されたサービス"フォルダアクションを設定..."を使おうとしています．とメッセージが出ます．
サービスの実行を押し， ＋でスクリプトを追加，`open_downloaded_cache.workflow`を選択し，関連付ける，を選択すれば完了です．

※ `~/paper2html/downloads`のファイルは容量制限を超えると自動削除されるので注意してください．
容量はautomatorから変更可能です（clean_downloadsの2番めの引数，デフォルトで1GB）．
自動削除なしVer.は`open_downloaded.workflow`です．

## トラブルシューティング
`which pdfinfo`とコマンド入力して何も出力されない場合は，popplerが実行環境から見えていません．
popplerのインストール場所を確認してください．
