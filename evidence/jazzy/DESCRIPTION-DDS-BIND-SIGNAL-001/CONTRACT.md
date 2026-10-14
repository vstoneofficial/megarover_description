# DESCRIPTION-DDS-BIND-SIGNAL-001

対象は9c8644684851f91325fe260d8bb15d9c9cfc37d1の単独表示。固定条件はDESCRIPTION-STANDALONE-001と同じ。通常表示6条件と初期化中終了3条件が合格した後、F120A / gui=false / RViz出現後0.15秒のSIGINTで、joint_state_nodeのUDP bind失敗・DDSドメイン作成エラー・Tracebackが発生した。終了コード0でも不合格とした。元の失敗、PID、実行prefix、hash、clean状態はfinal-candidate-10-f120a-false-early-sigintに保持した。

追加診断条件：productionソースを変更せず、LD_PRELOADでbindの戻り値とerrnoを観測した。元のタイミング8回では再発しなかったため、joint_state_nodeのbind実行中だけ専用threadからSIGINTを送る診断を追加した。これは基準の変更ではなく、原因を分離する診断である。SDKは変更していない。

signal-diagnostic-1/2/3は3回とも同じDDSエラーで不合格となり、bindのerrno=4（EINTR）が記録された。2回目は元の失敗と同じUDP 32417でerrno=4。同じ診断でbind呼出し中のSIGINT/SIGTERMだけをpthread_sigmaskで一時保留すると、masked-control-1/2/3は3回とも合格した。errno=98（EADDRINUSE）はDDSの次候補ポート探索で、errno=4による初期化失敗とは区別した。

証明した原因：SIGINTがnativeのROS/DDSノード初期化に入ると、WSLのUDP bindがEINTRで中断し、SDKがドメイン作成失敗を返す。Pythonの停止要求を記録するだけではnative syscallの中断を防げない。

変更可能なファイルはscripts/joint_state_node.pyとscripts/joint_state_gui.pyのみ。同じSDK JointStatePublisher初期化の間だけSIGINT/SIGTERMを保留し、元のmaskを必ず復元する。停止要求は初期化後に既存の正常終了処理で処理する。エラーを握り潰さず、DDS/ROS/QtのSDK、launch、model、TF、設定、検証閾値は変更しない。

合格条件：診断のSDK初期化中SIGINTがEINTRを生じなくなること。診断libraryなしで元の失敗条件、3機種×GUI有無の通常表示と初期化中SIGINT、GUI再起動を同じ基準で完走すること。標準build/testが合格すること。main・上流への昇格はしない。

診断を再構築する場合は、dds-bind-diagnostic/bind_signal_control.c.txtをgcc -x c -shared -fPIC -ldl -pthreadで.soにする。元のコンパイルはgcc -shared -fPIC -o bind_signal_control.so bind_signal_control.c -ldl -pthread。source/.soのSHA-256はcontrol-hashes.txtに記録した。BIND_SIGNAL_MASK_CONTROL=1が診断中の保留対照条件。観測Cソースは証拠用の.txtとして保持し、packageのproductionソースとは分ける。
