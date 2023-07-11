# shift_maker
**python** + **Pulp** + **gspread**

シフト、スケジュール調整などを自動で行うためのスクリプトです。pythonのPulpライブラリを用いて最適化問題を解きます。
基本的にはyamlファイルを編集するだけで、拘束条件を加えることができるようになっています。

ここではgoogle formなどを利用して、情報をgoogle spreadsheetに反映させ、それを取得してシフトを作成します。
つまり、このレポジトリにはシフトの最適化に必要なコードのみが含まれており、個人情報は含まれていません。
使い方の節で説明するファイルを新たに作成する必要があります。

また、google formを利用した場合を想定しており、このスクリプトを走らせるために必須な調査項目は、
* 名前
* シフトの可否(チェックボックスを利用したグリッド方式)
    * 入れない場合にチェックを入れてもらうことに注意

となっています。
google formについては[GoogleFormの設定](doc/GoogleForm.md)も参照してください。
必要な情報が記載されるシフトの列番号はschedule.yamlに記入したものを読み取る設定になっているので、
項目は自由に増やしても問題ありません。(設定に関しては使い方の節で詳しく述べます。)

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
```shell
vim sheet_structure.yaml
```

また、作成された鍵であるjsonファイルはjsonディレクトリの中に入れてください。
```shell
mv /hoge/huga.json json/
```

実際にpythonスクリプトからgoogle spreadsheetにアクセスできるかどうかをチェックしたい場合は、
chkconnect.pyを実行してください。
```shell
python chkconnection.py
```

## シフター情報の追記
実際にシフトを組むときには、このシフトにはこのような属性の人が必ず一人必要だといった、シフターの属性を取り入れると便利です。
そこで、google spreadsheet上にその属性を追加してください。
(シートを別にするかどうかは検討中)

追加したものに関してはsheet_structure.yamlに追記してください。
```shell
vim sheet_structure.yaml
```

model.yamlのnameノードでその変数を使用することができます。
詳細は次のモデルの設定を参照してください。

## データのチェック、整形
```shell
python read_data.py
```

comments.txtと整形されたデータdata.csvが出力されます。


## モデルの設定
シフトの調整を最適化問題に落とし込むためには、適切な目的関数を作成し、それを最小化(最大化)する必要があります。

イベントの都合上、シフトと同時に何かの仕事を振り分ける必要があり、さらにそちらの仕事の優先度が高い場合、
その人のシフト調査ファイルを直接編集することをお勧めします。

## シフト表の作成
適切にmodel.yamlを作成したら、make_shifttable.pyを実行してシフト表を作成します。
作成されたシフト表はoutput/shift_table.xlsxに作られます。

```shell
python make_shifttable.py
```

拘束条件を満たすシフトが作成できなかったり、何か問題、注意すべき点が発生した場合、
その内容がターミナル上とwarning.txt(上書き)に書き込まれます。
note.txtに書かれた内容が満たされているかどうかもチェックしてください。

# デバッグモード
各pythonスクリプトは"d"のオプションを使うことでデバッグモードになります。
templateの中に置かれたテストファイルをもとにスクリプトが実行されます。
作成されるファイルは通常と同じようにoutputディレクトリに出力されます。

```shell
python make_shifttable.py -d
```

問題点を見つけたら、ソースコードは適宜修正してください。