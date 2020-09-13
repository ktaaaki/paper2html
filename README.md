# paper2html

[![License: AGPL](https://img.shields.io/badge/license-AGPL-yellow)](https://opensource.org/licenses/AGPL-3.0)
[![Python Version](https://img.shields.io/badge/python-3.5|3.7-blue)](https://github.com/ktaaaki/paper2html)
[![Platform](https://img.shields.io/badge/platform-windows|macos|ubuntu-blue)](https://github.com/ktaaaki/paper2html)

It will convert a pdf paper to html pages. Only the format of single or double column is supported.

２段組の論文をhtml表示するツールです．

## 依存環境のインストール
popplerとmu-pdfに依存しているので，環境に合わせてインストールしてください．

### windowsの場合
`http://blog.alivate.com.au/poppler-windows/`

`https://mupdf.com/downloads/`

からpopplerとmupdfをダウンロード＋解凍して，環境変数にexeファイルのある場所のPathを通してください．

### ubuntuの場合
```
> sudo apt install mupdf mupdf-tools poppler-utils poppler-data
```
### macの場合
brew + pyenv + condaの環境でのみ動作確認しています．
```
> brew install mupdf-tools
> conda install -c conda-forge poppler
```
## 本体のインストール
以下のコマンドで，作業ディレクトリにクローンしたpaper2htmlをインストールできます．
```
> git clone https://github.com/ktaaaki/paper2html.git
> pip install -e paper2html
```

## 使用方法
ダウンロードしたpdfを指定して実行することで，htmlページが自動的に開きます．

pythonから
```
> python paper2html/main.py "path-to-paper-file.pdf"
```
ipythonから
```
>>> import paper2html
>>> paper2html.open_paper_htmls("path-to-paper-file.pdf")
```
mac,linuxでは下記のインストールを済ませれば，右クリックメニューまたは自動化から

- 変換したいpdfを選択して，`open pdf as html`を選択する
- `~/paper2html/downloads`にブラウザからpdfを保存する（自動的に変換が起動）

ことで利用可能です．

開くブラウザは以下のように指定可能です．
```
> python paper2html/main.py "path-to-paper-file.pdf" --browser_path="/path/to/browser"
```

また，pdfからhtmlへの変換のみも行うことができます．
```
>>> import paper2html
>>> paper2html.paper2html("path-to-paper-file or directory")
```

## フォルダアクションと右クリックメニューの作成
一部のOSではさらに操作を短縮するツールが利用できます．

### 右クリックメニューのインストール（mac用）
クローンしたソースフォルダから`paper2html/open pdf as html.workflow`
をダブルクリックしてautomatorに登録します．

`.zshrc`で自動的に有効になるconda環境でない場合は，
automatorからインストールされたworkflow内部のシェルスクリプトを変更してください．

MacOSがCatalina以上であれば，設定＞セキュリティとプライバシー＞フルディスクアクセス にFinder.appの追加が必要です．
ワークフロー内のシェルスクリプトで(システムのpythonではなく)依存関係をインストールしたpythonを利用するため．
設定しないと`Operation is not permitted`のエラーが出るので注意してください．

### フォルダアクションのインストール（mac用）
クローンしたソースフォルダから`paper2html/open_downloaded.workflow`
をダブルクリックしてautomatorに登録します．

`.zshrc`で自動的に有効になるconda環境でない場合は，
automatorからインストールされたworkflow内部のシェルスクリプトを変更してください．

MacOSがCatalina以上であれば，設定＞セキュリティとプライバシー＞フルディスクアクセス にFinder.appの追加が必要です．
ワークフロー内のシェルスクリプトで(システムのpythonではなく)依存関係をインストールしたpythonを利用するため．
設定しないと`Operation is not permitted`のエラーが出るので注意してください．

次に，pdfのダウンロード先のフォルダを右クリックし，右クリックメニュー＞サービス＞"フォルダアクションを設定.."を選択し，
"サービスを確認"を押すと，"Finder"が制限されたサービス"フォルダアクションを設定..."を使おうとしています．とメッセージが出ます．
サービスの実行を押し， ＋でスクリプトを追加，`open_downloaded.workflow`を選択し，関連付ける，を選択すれば完了です．

### ディレクトリ監視スクリプト（ubuntu用）
以下のように監視用のツールを導入し，
```
sudo apt install inotify-tools
```
`paper2html/open_downloaded.sh`の`DOWNLOADS_DIR`を設定した後，
以下のコマンドを実行すると，ディレクトリが監視されます．
```
bash paper2html/open_downloaded.sh
```
このディレクトリにダウンロードを行えば自動的にブラウザが起動します．

### フォルダ監視スクリプト（windows用）
`paper2html/open_downloaded.ps1`の`"C:\MyDownloads"`を適当なフォルダパスに書き換えた後，
`paper2html/open_downloaded.ps1`の右クリックメニュー＞`power shellを実行`を選択すると，
フォルダが監視されます．

このフォルダにダウンロードを行えば自動的にブラウザが起動します．

## トラブルシューティング
`which pdfinfo`（またはwindowsでは`where.exe pdfinfo`）とコマンド入力して何も出力されない場合は，popplerが実行環境から見えていません．
popplerのインストール場所を確認してください．
