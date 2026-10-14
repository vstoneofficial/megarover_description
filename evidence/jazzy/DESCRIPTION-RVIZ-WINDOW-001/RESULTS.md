# RVizウインドウ終了の確認

実行コード：`e8f44ea4097552846a136a67cc04943f6d99c2fd`、clean。CPP backendは変更せず、同じ再現プログラムを使用した。

診断の追加再送なしで、early-sigintは0.769秒・0.969秒、readyは1.474秒・1.269秒で正常終了した。4runともTraceback・ERROR・強制終了・残留はなく、readyではモデル・TF・joint_statesを確認した。artifactは実行前後で一致した。

続くgui:=falseのrunでは、別のSDK joint_state_publisher終了時KeyboardInterruptを検出した。GUIなし構成を含む単独display全体の合格とは扱わない。原証拠をcontrolled-candidate/に保存した。
