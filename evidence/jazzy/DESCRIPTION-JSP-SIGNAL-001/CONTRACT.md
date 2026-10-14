# DESCRIPTION-JSP-SIGNAL-001

対象：gui:=falseの単独display、Jazzy / CycloneDDS / domain100 / VNC :1。

再現コード：`e8f44ea4097552846a136a67cc04943f6d99c2fd`、clean。
原証拠：`../DESCRIPTION-RVIZ-WINDOW-001/controlled-candidate/window-candidate-05-mega3-false-ready/`。

症状：表示と配信は成功するが、SIGINT後、SDK joint_state_publisherがdestroy_node→destroy_service内のKeyboardInterruptで終了コード-2になる。他の表示プロセスは正常に終了する。

対象原因：SDK配信ノードがlaunchと同じforeground process groupにあり、検証のgroup SIGINTとlaunchの転送SIGINTが重複する。SDK mainはspin中のKeyboardInterruptを処理するが、続くdestroy_nodeにはそのハンドラーがない。記録したprocess group、転送ログ、実スタックとSDK mainを確認した。既存bringup入口の同じSDKノードはsetsidで別sessionに置かれている。

許可する修正は、launch/display.launch.pyのgui:=false用joint_state_publisherへ同じsetsid prefixを付ける1行のみ。SDK・モデル・RViz・ジョイントGUI・終了期限・再現条件を変更しない。

同じgroup SIGINTのready / early-sigint条件でSDK配信ノードが正常終了することを確認する。表示・全TF・joint_statesを維持し、Traceback・ERROR・強制終了・残留なし。3機種×GUI有無と再起動を確認する。main・上流へ昇格しない。
