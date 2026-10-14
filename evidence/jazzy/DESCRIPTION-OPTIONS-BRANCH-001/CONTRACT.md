# DESCRIPTION-OPTIONS-BRANCH-001

READMEの `git clone -b $ROS_DISTRO` はROS_DISTRO=jazzyで存在しないbranchを選ぶ。
上流remoteはmaster `932a710473d1e68b86d78ab919a8442f457ee79f`だけを返した。
同じremoteのrefs/heads/jazzyを--exit-codeで検索し、exit2を再現した。

修正範囲はREADMEのオプション取得コマンドとJazzy用導入・確認方法のみ。
masterの同じcommitはcleanなローカル依存として既に使用し、README対応オプションの全18組合せでJazzy xacro展開、URDF tree、mesh参照、元モデルのlink/joint不変を確認した。
これは上流の公式Jazzyサポートの宣言ではなく、この環境での確認結果。

存在するmasterを選ぶコマンドへ修正し、Jazzyの環境・依存解決・ビルド・単独表示・domain100を記載する。
モデル、オプションの初期コメント、上流コードは変更しない。単独表示の機能確認結果とAMIR未導入の範囲を区別する。
