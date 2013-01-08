SublimeAizuOnlineJudge
======================

## 概要
AizuOnlineJudgeでの実行をサポートするSublimeText2 plugin

## インストール方法
Package Controlには登録されていないので手動でインストールします。

gitコマンドが使えない場合：Zipファイルをダウンロードして"Packagesフォルダ"に解凍、フォルダ名を`SublimeAizuOnlineJudge`に変更してください

gitコマンドが使える場合："Packagesフォルダ"にリポジトリをクローンしてください。

		https://github.com/shibainurou/SublimeAizuOnlineJudge.git

"Packagesフォルダ"の場所:


* Windows:

        C:\Users\(ユーザー名)\AppData\Roaming\Sublime Text 2\Packages\
        
* OS X:

        ~/Library/Application Support/Sublime Text 2/Packages/

* Linux:

        ~/.config/sublime-text-2/Packages/

## 設定
`Perferences -> Package Settings -> AizuOnlineJudge -> Settings – Default`から`user_name`, `password`を変更する。

## 使い方
`ctrl + shift + p`で開く、コマンドパレットから実行

* `AizuOnlineJudge: Create File`

SublimeText2の下部に表示されるインプットパネルに使用する言語を入力すると、`"Packagesフォルダ"\template`
フォルダにあるテンプレートファイルを展開する。デフォルトはC++。
templateは各言語ごとに作成できるので、`template` + `.cpp`など使用言語の拡張子をつけたテンプレートファイルを作成してください。

* `AizuOnlineJudge: Submit`

AOJに現在開いているソースをSubmitする。

* `AizuOnlineJudge: Submit for Prompt`

AOJに現在開いているソースをSubmitする。
SublimeText2の下部に表示されるインプットパネルに"問題ID"を入力してください。

"問題ID"：

		AOJの各タイトルの先頭に表示されている 4桁 or 5桁 の数字

