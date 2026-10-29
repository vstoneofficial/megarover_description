// Copyright 2026 YOSHIDA-V (ROS 2 Jazzy modifications)
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// Qt must be included before GLX introduces Xlib macros.
#include <QApplication>
#include <QEvent>
#include <QObject>
#include <QPointer>
#include <QTimer>

// Keep Xlib's None and Status macros out of the remaining ROS headers.
#include <GL/gl.h>
#include <GL/glx.h>
#undef None
#undef Status

#include <memory>
#include <string>
#include <vector>

#include <rclcpp/rclcpp.hpp>
#include <rviz_common/logging.hpp>
#include <rviz_common/ros_integration/ros_client_abstraction.hpp>
#include <rviz_common/visualization_frame.hpp>
#include <rviz_common/visualization_manager.hpp>
#include <rviz_common/visualizer_app.hpp>

// Display layout changes remain explicitly saveable from File -> Save Config.
// Map data is saved separately; this filter only handles the frame's close event.
class DisplayLayoutCloseFilter final : public QObject
{
public:
  void initializationComplete()
  {
    initialized_ = true;
    if (pending_close_) {
      auto frame = pending_close_;
      pending_close_.clear();
      // Run the deferred close from the application event loop, after init.
      QTimer::singleShot(0, frame.data(), [frame]() {
          if (frame) {
            frame->close();
          }
      });
    }
  }

protected:
  bool eventFilter(QObject * object, QEvent * event) override
  {
    if (event->type() == QEvent::Close) {
      auto * frame = dynamic_cast<rviz_common::VisualizationFrame *>(object);
      if (frame) {
        if (!initialized_) {
          pending_close_ = frame;
          event->ignore();
          RCLCPP_INFO(rclcpp::get_logger("rviz2"),
            "Deferred frame close until RViz initialization completes");
          return true;
        }
        // Stop new frames and finish outstanding GL work while the frame still
        // owns its display resources. Use the renderer's current GLX context.
        if (auto * manager = frame->getManager()) {
          manager->stopUpdate();
        }
        if (glXGetCurrentContext()) {
          const auto drawable = glXGetCurrentDrawable();
          glFinish();
          RCLCPP_INFO(rclcpp::get_logger("rviz2"),
            "Completed rendering before frame close; GLX drawable=%lu",
            drawable);
        }
        const bool modified = frame->isWindowModified();
        frame->setWindowModified(false);
        RCLCPP_INFO(rclcpp::get_logger("rviz2"),
          "Display layout close confirmation disabled; unsaved layout=%s",
          modified ? "true" : "false");
      }
    }
    return false;  // The installed VisualizationFrame performs its usual close.
  }

private:
  bool initialized_{false};
  QPointer<rviz_common::VisualizationFrame> pending_close_;
};

int main(int argc, char ** argv)
{
  auto qt_arguments = rclcpp::remove_ros_arguments(argc, argv);
  std::vector<char *> qt_argv;
  for (auto & argument : qt_arguments) {
    qt_argv.push_back(argument.data());
  }
  qt_argv.push_back(nullptr);
  int qt_argc = static_cast<int>(qt_arguments.size());
  QApplication application(qt_argc, qt_argv.data());
  DisplayLayoutCloseFilter close_filter;
  application.installEventFilter(&close_filter);

  const auto logger = rclcpp::get_logger("rviz2");
  rviz_common::set_logging_handlers(
    [logger](const std::string & text, const std::string &, size_t) {
      RCLCPP_DEBUG(logger, "%s", text.c_str());
    },
    [logger](const std::string & text, const std::string &, size_t) {
      RCLCPP_INFO(logger, "%s", text.c_str());
    },
    [logger](const std::string & text, const std::string &, size_t) {
      RCLCPP_WARN(logger, "%s", text.c_str());
    },
    [logger](const std::string & text, const std::string &, size_t) {
      RCLCPP_ERROR(logger, "%s", text.c_str());
    });
  rviz_common::install_rviz_rendering_log_handlers();

  rviz_common::VisualizerApp visualizer(
    std::make_unique<rviz_common::ros_integration::RosClientAbstraction>());
  visualizer.setApp(&application);
  if (!visualizer.init(argc, argv)) {
    return 1;
  }
  close_filter.initializationComplete();
  return application.exec();
}
