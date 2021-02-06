# paper2html

[![License: AGPL](https://img.shields.io/badge/license-AGPL-yellow)](https://opensource.org/licenses/AGPL-3.0)
[![Python Version](https://img.shields.io/badge/python-3.5|3.7|3.8-blue)](https://github.com/ktaaaki/paper2html)
[![Platform](https://img.shields.io/badge/platform-windows|macos|ubuntu-blue)](https://github.com/ktaaaki/paper2html)

It will convert a pdf paper to html pages & show them using pdf-miner & poppler. Only the format of single or double column is supported. If you use Chrome, you can browser-translate papers(as of 2021/2/6).

pdf-miner.sixとpopplerを使用して(２段組を含む)論文をhtml表示するツールです．論文調のマニュアルでもきれいに表示できることもあります．Chromeを使用すれば，ブラウザ翻訳が可能になります(2021/2/6現在)．

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

## 基本的な使用方法
まずブックマークレットを作成します．ブラウザで何かしらのページをお気に入り登録し，登録内容を編集してURLの欄の記述を以下のコードに書き換えます．
```
javascript:var esc=encodeURIComponent;var d=document;var subw=window.open('http://localhost:5000/paper2html?url='+esc(location.href)).document;
```
以下のコマンドで，ローカルでpaper2htmlサーバを立ち上げます．
```shell
> python paper2html/main.py
```
次にブラウザからpdfファイルを開き，作成したブックマークレットを押してサーバに翻訳リクエストを送ります．

pdfの内容と抽出したテキストの2つが並んだページが表示されれば成功です．

## その他の使用方法
ダウンロードしたpdfを指定して実行することで，htmlページが自動的に開きます．（ブラウザ翻訳はできません．）

pythonから
```
> python paper2html/commands.py "path-to-paper-file.pdf"
```
ipythonから
```
>>> import paper2html
>>> paper2html.open_paper_htmls("path-to-paper-file.pdf")
```

開くブラウザは以下のように指定可能です．
```
> python paper2html/commands.py "path-to-paper-file.pdf" --browser_path="/path/to/browser"
```

また，pdfからhtmlへの変換のみも行うことができます．
```
>>> import paper2html
>>> paper2html.paper2html("path-to-paper-file or directory")
```

## トラブルシューティング
`which pdfinfo`（またはwindowsでは`where.exe pdfinfo`）とコマンド入力して何も出力されない場合は，popplerが実行環境から見えていません．
popplerのインストール場所を確認してください．
