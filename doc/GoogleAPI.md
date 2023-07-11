# gspreadの設定
2023/07/11現在の方法なので、アップデートなど仕様変更があれば状況は変化すると思うのでご注意ください。

## Google Cloud Platformの設定
まず、[Google Cloud Platform](https://console.cloud.google.com/cloud-resource-manager)にアクセスしてください。
この際に、googleアカウントでログインする必要があります。

![Image GoogleCloud home](figure/GoogleCloudPlatform_home.png)

以上のような画面になりますので、青色の文字のプロジェクトを作成をクリックしてください。

すると、新しいプロジェクトの設定画面に映ると思うので、任意の名前を設定してください。
組織に所属したアカウントで作成する場合は、「組織」「場所」といった項目が出てきますので、
google APIを用いることに問題がなければ、デフォルトの値を用いて作成することができると思います。

gmailなどフリーなメールアドレスを使用する場合は「組織なし」を選択で問題ありません。
この例では「組織なし」を使用した場合の例を記載します。
最後に作成ボタンをクリックしてください。

![Image GoogleCloud newproject](figure/GoogleCloudPlatform_newproject.png)

しばらく待つと(1分程度)、プロジェクトが作成され、一覧に表示されるようになります。
ここに先ほど設定した名前が表示されれば、プロジェクト作成は完了です。

![Image GoogleCloud index](figure/GoogleCloudPlatform_index.png)

続いて、APIの有効化を行います。
gspreadを使用するためには次の二つのAPIを有効化する必要があります。

* Google Drive API 
* Google Sheets API

以下の手順によりAPIを有効化しますが、他に有効化したいAPIがありましたら、同様の手順で有効化することができます。

まず、左側の「三」の形の設定ボタンから、APIとサービスをクリックしてください。

![Image GoogleCloud index](figure/GoogleCloudPlatform_setting.png)
