Any contribution that you make to this repository will
be under the Apache 2 License, as dictated by that
[license](http://www.apache.org/licenses/LICENSE-2.0.html):

~~~
5. Submission of Contributions. Unless You explicitly state otherwise,
   any Contribution intentionally submitted for inclusion in the Work
   by You to the Licensor shall be under the terms and conditions of
   this License, without any additional terms or conditions.
   Notwithstanding the above, nothing herein shall supersede or modify
   the terms of any separate license agreement you may have executed
   with Licensor regarding such Contributions.
~~~

# 変更と動作確認

このリポジトリはVstoneのモデルパッケージを基にしたJazzy確認用候補です。既存モデルの作者・maintainer情報を保持し、変更分にはApache License 2.0のnoticeを付けます。

標準ビルドとテストを実行してください。

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select megarover_description
colcon test --packages-select megarover_description
colcon test-result --verbose
```

モデル・起動処理を変更する場合は、対象機種のRViz表示、TF、joint_states、Ctrl+C終了、再起動も確認してください。検証コードと実行したモデル・設定・実行ファイルのhashを、実行ログと対応付けて残します。

配布する初期状態ではTG30などのオプションをコメントにします。変更するmodel・mesh・joint・controller設定を明示し、関係しない物理値を調整しないでください。候補の確認記録はevidence/jazzy/へ保存します。
