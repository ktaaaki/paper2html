# paper2html

[![License: AGPL](https://img.shields.io/badge/license-AGPL-yellow)](https://opensource.org/licenses/AGPL-3.0)
[![Python Version](https://img.shields.io/badge/python-3.5|3.7|3.8-blue)](https://github.com/ktaaaki/paper2html)
[![Platform](https://img.shields.io/badge/platform-windows|macos|ubuntu-blue)](https://github.com/ktaaaki/paper2html)

It will convert a pdf paper to html pages & show them using pdf-miner & poppler. Only the format of single or double column is supported.

pdf-miner.sixとpopplerを使用して(２段組を含む)論文等をhtml表示するツールです．論文調のマニュアルでもきれいに表示できることもあります．

<img width="1633" alt="demo" src="https://user-images.githubusercontent.com/4715386/94166499-54ecb480-fec6-11ea-8155-d44d192445fa.png">
Albanie, Samuel, Sébastien Ehrhardt, and Joao F. Henriques. "Stopping gan violence: Generative unadversarial networks." arXiv preprint arXiv:1703.02528 (2017).

## 依存環境のインストール
popplerに依存しているので，環境に合わせてインストールしてください．

### windowsの場合
`http://blog.alivate.com.au/poppler-windows/`

からpopplerをダウンロード＋解凍して，環境変数にexeファイルのある場所のPathを通してください．

例えば最新のバイナリ:poppler-0.68.0_x86を`C:¥Users¥YOUR_NAME¥Downloads`にダウンロードして展開した場合は，
システムの詳細設定の表示＞システムのプロパティ＞詳細設定＞環境変数(N)...＞ユーザー環境変数のPathを編集して
値`C:¥Users¥YOUR_NAME¥Downloads¥poppler-0.68.0¥bin`を新規に追加してください．

### ubuntuの場合
```
> sudo apt install poppler-utils poppler-data
```
### macの場合
anaconda(miniconda)の場合
```
> conda install poppler
```
homebrewの場合
```
> brew install poppler
```
## 本体のインストール
python3とgitをインストールした後，
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

`.zshrc`で自動的に有効になるpython環境 (≒ zshでデフォルトのpython)でない場合は，
automatorからインストールされたworkflow内部のシェルスクリプトを変更してください．

MacOSがCatalina以上であれば，設定＞セキュリティとプライバシー＞フルディスクアクセス にFinder.appの追加が必要です．
ワークフロー内のシェルスクリプトで(システムのpythonではなく)依存関係をインストールしたpythonを利用するため．
設定しないと`Operation is not permitted`のエラーが出るので注意してください．

### フォルダアクションのインストール（mac用）
クローンしたソースフォルダから`paper2html/open_downloaded.workflow`
をダブルクリックしてautomatorに登録します．

`.zshrc`で自動的に有効になるpython環境 (≒ zshでデフォルトのpython)でない場合は，
automatorからインストールされたworkflow内部のシェルスクリプトを変更してください．

MacOSがCatalina以上であれば，設定＞セキュリティとプライバシー＞フルディスクアクセス にFinder.appの追加が必要です．
ワークフロー内のシェルスクリプトで(システムのpythonではなく)依存関係をインストールしたpythonを利用するため．
設定しないと`Operation is not permitted`のエラーが出るので注意してください．

次に，pdfのダウンロード先のフォルダを右クリックし，右クリックメニュー＞サービス＞"フォルダアクションを設定.."を選択し，
"サービスを確認"を押すと，"Finder"が制限されたサービス"フォルダアクションを設定..."を使おうとしています．とメッセージが出ます．
サービスの実行を押し， ＋でスクリプトを追加(下図参照)，`open_downloaded.workflow`を選択し，関連付ける，を選択すれば完了です．

<img width="483" alt="accept_folder_action" src="https://user-images.githubusercontent.com/4715386/94677454-dffefc00-0357-11eb-8948-be0ea6c8f137.png">

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

(デフォルトのブラウザ以外で開きたい場合は，持っているブラウザに合わせて`BROWSER_PATH`も適宜変更してください．)

### フォルダ監視スクリプト（windows用）
※ フォルダ監視が一部環境で機能しないバグが報告されています．

`paper2html/open_downloaded.ps1`の`"${HOME}/Downloads"`を適当なフォルダパスに書き換えた後，
`paper2html/open_downloaded.ps1`の右クリックメニュー＞`power shellを実行`を選択すると，
指定したフォルダが監視されます．

このフォルダにダウンロードを行えば自動的にブラウザが起動します．

(デフォルトのブラウザ以外で開きたい場合は，持っているブラウザに合わせて`$browser_path`も適宜変更してください．)

## トラブルシューティング
`which pdfinfo`（またはwindowsでは`where.exe pdfinfo`）とコマンド入力して何も出力されない場合は，popplerが実行環境から見えていません．
popplerのインストール場所を確認してください．
