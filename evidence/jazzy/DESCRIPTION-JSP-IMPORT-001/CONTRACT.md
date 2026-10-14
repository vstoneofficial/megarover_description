# DESCRIPTION-JSP-IMPORT-001

再現コード：`d7380512af47d8353961f1e559e6e47ef857be43`、clean。gui:=false / early-sigint、Jazzy / domain100 / VNC :1。

原証拠：`../DESCRIPTION-JSP-SIGNAL-001/controlled-candidate/jsp-candidate-02-mega3-false-early-sigint/`。

証明した原因：インストール済みconsole entrypointは、終了要求を保持するハンドラーがない状態でSDKのPython moduleをimportする。実スタックはjoint_state_publisher.pyのimport std_msgs.msgとそのモジュール読み込み中のKeyboardInterruptを示し、終了コード-2になる。setsidで信号の重複を除いても発生したため、前件と区別する。

修正可能：scripts/joint_state_node.py、CMakeLists.txtのそのinstall、launch/display.launch.pyのgui:=falseの起動先のみ。新しい入口はimport前に終了要求を保持し、SDKのJointStatePublisher本体を使用する。配信パラメータ、URDF、joint_statesの計算はSDKを継承する。確認済みジョイントGUIとRViz、SDK、モデル、摩擦は変更しない。

合格条件：同じreadyとearly-sigintで終了コード0、Traceback・ERROR・強制終了・残留なし。全TFとjoint_statesを維持する。3機種×GUI有無、再起動も確認する。終了要求のためにROS contextを先に破棄せず、配信nodeを破棄してからcontextを終了する。期限は元の30秒から変えない。main・上流へ昇格しない。
