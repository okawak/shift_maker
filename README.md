# shift_maker
**python** + **Pulp** + **gspread**

シフト、スケジュール調整などを自動で行うためのスクリプトです。pythonのPulpライブラリを用いて最適化問題を解きます。
基本的にはyamlファイル+spreadsheetに属性を追加すると、拘束条件を加えることができるようになっています。

ここではgoogle formなどを利用して、情報をgoogle spreadsheetに反映させ、それを取得してシフトを作成します。
つまり、このレポジトリにはシフトの最適化に必要なコードのみが含まれており、個人情報は含まれていません。
使い方の節で説明するファイルを新たに作成する必要があります。

また、google formを利用した場合を想定しており、このスクリプトを走らせるために必須な調査項目は、
* 名前
* シフトの可否(チェックボックスを利用したグリッド方式)
    * 入れない場合にチェックを入れてもらうことに注意
* 特筆事項を記載するコメント

となっています。
google formについては[GoogleFormの設定](doc/GoogleForm.md)も参照してください。
必要な情報が記載されるシフトの列番号はschedule.yamlに記入したものを読み取る設定になっているので、
項目は自由に増やしても問題ありません。(設定に関しては使い方の節で詳しく述べます。)

デフォルトでは(model.yamlに何も追記しない場合)、シフトの可否のみを考慮したテーブルが作られます。
具体的には、

* 特定の時間のあるシフトには必ず一人割り当てられる
* 一つの時間スロットに同じ人が割り当てられるのを禁止する
* NGのスケジュールにはシフトを入れない

の三つです。表式は、make_shifttable.pyを見てください。
基本的な使い方としては、spreadsheetとmodel.yamlを編集し、属性を考慮したシフトを自動で作成したのちに、
手動で良いかどうかを確かめるといった形です。

また、jupyter notebookで挙動を確認したい場合は、test.ipynbを使用したり、新たにファイルを作成してください。

# 使い方

## pythonの環境構築
pythonのvenvを用いて環境を作ります。エラーが出る場合は他に何かしらインストールが必要になるかもしれません。
```shell
cd directory_you_want_to_install
git clone https://github.com/okawak/shift_maker.git
cd shift_maker
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```
## gspreadの設定
pythonのパッケージであるgspreadを用いて、google spreadsheetにある情報を取得します。
gspreadを使用するためには、spreadsheetとサービスアカウントを連携させることが必要で、
その方法は[gspreadの初期設定](doc/GoogleAPI.md)を参考にしてください。
バージョンによっては方法が変わっている場合もあるので、その点はご注意ください。

google spreadsheetの構造はsheet_structure.yamlに記入してください。
Input用とOutput用のスプレッドシートを用意して、構造をyamlファイルに書くことを忘れないでください。

また、作成された鍵であるjsonファイルはjsonディレクトリの中に入れてください。
```shell
mv /hoge/huga.json json/
```

実際にpythonスクリプトからgoogle spreadsheetにアクセスできるかどうかをチェックしたい場合は、
chkconnect.pyを実行してください。
```shell
python chkconnection.py
```
successが帰って来れば接続は問題ありません。

## シフター情報の追記
実際にシフトを組むときには、このシフトにはこのような属性の人が必ず一人必要だといった、シフターの属性を取り入れると便利です。
そこで、google spreadsheet上にその属性を追加してください。

追加したものに関してはsheet_structure.yamlにその列のアルファベットをattributeノードに追記してください。
この番号は、model.yamlを用いて拘束条件を追記するときに用いることができます。

attributeノードをコメントアウトすると、これを使わないでシフトを作成します。

## データのチェック、整形
Formにテスト用のデータを送る際は、名前をtestにしてください。
testの名前のものはスルーするように設定してあります。

同じ人が複数回答した場合は、タイムスタンプが新しいものを採用するなどのデータの整形を行うために、
read_data.pyを実行してください。

```shell
python read_data.py
```

このとき、sheet_structure.yamlのattributeノードがコメントアウトされていた場合、
全てattributeは0となるようになっていますが、以下のようなコマンドライン引数を設定すると、メールのドメインで属性を区別することができます。
```shell
python read_data.py -i hoge.com
```
これは、hoge.comのドメインを持つメールアドレスで登録されたユーザーを1の属性に、その他のユーザーを0の属性になるようにします。

また、コメントはまとめてcomments.txtに出力され、整形されたデータはdata.csvに出力され、これを用いてシフトテーブルを作ります。


## モデルの設定
model.yamlに書かれたコメントをもとに必要な拘束条件を追記してください。

シフトの調整を最適化問題に落とし込むための考え方については[モデル](doc/model.md)を参照してください。

## シフト表の作成
適切にmodel.yamlを作成したら、make_shifttable.pyを実行してシフト表を作成します。
自動でsheet_structure.yamlのOutputに書かれたシートに結果が書かれるようになっています。

```shell
python make_shifttable.py
```

最適化することができない条件だった場合は、ターミナル上に
```
optimality = Infeasible, target value = 135.0
```
のように"Infeasible"と表示されます。
拘束条件などを見直す必要があります。

うまく解を見つけられた場合、
```
optimality = Optimal, target value = 150.0
```
のように"Optimal"と表示されます。

ただし、必要な条件が足りなかったりする場合もあるので、出力されたシフトテーブルは良く確認してください。
また、comments.txtも参考にして、最終的には手動でシフトを決める必要があると思います。
