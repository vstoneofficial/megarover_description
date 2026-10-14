# メガローバーの3Dモデルのパッケージ

![](images/mega3_description.png)

## 準備

Ubuntu 24.04 / ROS 2 Jazzyで、メガローバーの3Dモデルを表示するパッケージです。ROS 2 Jazzyを導入した環境で使用してください。

### パッケージの導入

```bash
source /opt/ros/jazzy/setup.bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
git clone --branch jazzy https://github.com/vstoneofficial/megarover_description.git
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src --rosdistro jazzy -r -y
colcon build --symlink-install --packages-select megarover_description
source install/setup.bash
export ROS_DOMAIN_ID=100
```

### オプションの表示

ヴイストンの台車ロボットのオプションを表示する場合は、`vs_rover_options_description`を`src`フォルダーにクローンしてください。（詳細は[こちら](https://github.com/vstoneofficial/vs_rover_options_description)を参照してください）

```bash
cd ~/ros2_ws/src
git clone --branch master https://github.com/vstoneofficial/vs_rover_options_description.git
cd ~/ros2_ws
colcon build --symlink-install --packages-select megarover_description vs_rover_options_description
source install/setup.bash
```

対応するオプション:

- LRF TG30
- バンパーセンサ（メガローバー：前後）
- デプスカメラ Realsense D435i
- カメラステー

初期状態ではオプションをコメントアウトしています。使用するロボットに合わせて、[mega3.xacro](./urdf/mega3.xacro)、[f120a.xacro](./urdf/f120a.xacro)、[s40a_lb.xacro](./urdf/s40a_lb.xacro)の必要なオプションだけコメントを解除してください。

例えばmega3でTG30を使用する場合は、次の行を有効化します。

```xml
<!-- OPTION LRF TG30 -->
<xacro:include filename="$(find vs_rover_options_description)/urdf/lrf/tg30_mega3.xacro" />
```

xacroを編集した後は、ワークスペースでビルドして設定を反映してください。

```bash
cd ~/ros2_ws
colcon build --symlink-install --packages-select megarover_description
source install/setup.bash
```

## 構成

- `urdf/`
  - 各ロボットの Xacro、Gazebo 用定義、ros2_control 用定義
- `meshes/`
  - 3D モデル
- `launch/`
  - RViz 表示用 launch
- `rviz/`
  - RViz 設定ファイル
- `params/`
  - ros2_control のコントローラ設定
- `scripts/`
  - 補助ノード

## RViz上の可視化

ロボットモデルを表示します。`rover:=`で機種を切り替えます。

```bash
source ~/ros2_ws/install/setup.bash
export ROS_DOMAIN_ID=100
ros2 launch megarover_description display.launch.py rover:=mega3
```

`rover:=`で指定できる値:

- `mega3`
- `f120a`
- `s40a_lb`

### メガローバーVer 3.0を表示する場合:

```bash
ros2 launch megarover_description display.launch.py rover:=mega3
```

### F120Aを表示する場合:

```bash
ros2 launch megarover_description display.launch.py rover:=f120a
```

### S40A_LBを表示する場合:

```bash
ros2 launch megarover_description display.launch.py rover:=s40a_lb
```

関節操作のウィンドウを非表示にする場合は、`gui:=false`を指定してください。RVizは表示されます。

```bash
ros2 launch megarover_description display.launch.py rover:=mega3 gui:=false
```

終了するには、起動した端末でCtrl+Cを押してください。RVizの表示設定を保存する場合は、終了前にFile → Save Configを使用してください。
