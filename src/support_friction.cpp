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

#include <algorithm>
#include <cmath>
#include <iostream>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#include <gz/common/Event.hh>
#include <gz/plugin/Register.hh>
#include <gz/sim/EntityComponentManager.hh>
#include <gz/sim/EventManager.hh>
#include <gz/sim/System.hh>
#include <gz/sim/components/Collision.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/ParentEntity.hh>
#include <gz/sim/physics/Events.hh>
#include <sdf/Element.hh>

namespace megarover_description
{
// Apply body support and retain original wheel material on actual contacts.
// The model's original wheel coefficients are read without tuning them.
class SupportFriction : public gz::sim::System,
  public gz::sim::ISystemConfigure, public gz::sim::ISystemPreUpdate
{
  using Params = gz::physics::SetContactPropertiesCallbackFeature::
    ContactSurfaceParams<gz::physics::FeaturePolicy3d>;
  struct Rule
  {
    std::string link;
    double mu1;
    double mu2;
  };

public:
  void Configure(
    const gz::sim::Entity & entity,
    const std::shared_ptr<const sdf::Element> & sdf,
    gz::sim::EntityComponentManager &, gz::sim::EventManager & events) override
  {
    this->model = entity;
    this->rules.push_back({sdf->Get<std::string>("support_link"),
        sdf->Get<double>("mu1"), sdf->Get<double>("mu2")});
    auto config = sdf->Clone();
    if (config->HasElement("original_wheel_material")) {
      for (auto wheel = config->GetElement("original_wheel_material"); wheel;
        wheel = wheel->GetNextElement("original_wheel_material"))
      {
        this->rules.push_back({wheel->Get<std::string>("link"),
            wheel->Get<double>("mu1"), wheel->Get<double>("mu2")});
      }
    }
    for (const auto & rule : this->rules) {
      if (!std::isfinite(rule.mu1) || !std::isfinite(rule.mu2) ||
        rule.mu1 < 0 || rule.mu2 < 0)
      {
        throw std::invalid_argument("Invalid contact friction coefficients");
      }
    }
    this->connection = events.Connect<gz::sim::events::CollectContactSurfaceProperties>(
      [this](const gz::sim::Entity & a, const gz::sim::Entity & b,
      const gz::math::Vector3d &, const std::optional<gz::math::Vector3d>,
      const std::optional<gz::math::Vector3d>, const std::optional<double>,
      const size_t, Params & params)
      {
        auto first = this->collisions.find(a);
        auto second = this->collisions.find(b);
        if (first == this->collisions.end() && second == this->collisions.end()) {
          return;
        }
        const auto & material = first != this->collisions.end() ? first->second : second->second;
        double mu1 = material.mu1;
        double mu2 = material.mu2;
        if (first != this->collisions.end() && second != this->collisions.end()) {
          mu1 = std::min(first->second.mu1, second->second.mu1);
          mu2 = std::min(first->second.mu2, second->second.mu2);
        }
        // Retain an already lower coefficient contributed by the other surface.
        params.frictionCoeff = std::min(params.frictionCoeff.value_or(mu1), mu1);
        params.secondaryFrictionCoeff = std::min(
          params.secondaryFrictionCoeff.value_or(mu2), mu2);
        const auto entity = first != this->collisions.end() ? a : b;
        if (this->reportedContacts.insert(entity).second) {
          std::cout << "[support_friction] contact=" << a << "," << b
                    << " link=" << material.link
                    << " mu1=" << *params.frictionCoeff
                    << " mu2=" << *params.secondaryFrictionCoeff << std::endl;
        }
      });
  }

  void PreUpdate(
    const gz::sim::UpdateInfo &,
    gz::sim::EntityComponentManager & ecm) override
  {
    if (this->foundLinks.size() == this->rules.size()) {
      return;
    }
    ecm.Each<gz::sim::components::Collision, gz::sim::components::Name,
      gz::sim::components::ParentEntity>(
      [this, &ecm](const gz::sim::Entity & entity,
      const gz::sim::components::Collision *, const gz::sim::components::Name * name,
      const gz::sim::components::ParentEntity * parent)
      {
        const auto modelParent = ecm.Component<gz::sim::components::ParentEntity>(parent->Data());
        if (!modelParent || modelParent->Data() != this->model) {
          return true;
        }
        const auto & collisionName = name->Data();
        for (const auto & rule : this->rules) {
          const auto directName = rule.link + "_collision";
          const auto reducedSuffix = "__" + directName;
          const bool reducedName = collisionName.size() >= reducedSuffix.size() &&
          collisionName.compare(collisionName.size() - reducedSuffix.size(),
            reducedSuffix.size(), reducedSuffix) == 0;
          if (collisionName == directName || reducedName) {
            if (!ecm.Component<gz::sim::components::EnableContactSurfaceCustomization>(entity)) {
              ecm.CreateComponent(
                entity, gz::sim::components::EnableContactSurfaceCustomization(true));
            }
            this->collisions.emplace(entity, rule);
            this->foundLinks.insert(rule.link);
            std::cout << "[support_friction] collision=" << entity
                      << " name=" << collisionName << std::endl;
          }
        }
        return true;
      });
  }

private:
  gz::sim::Entity model{gz::sim::kNullEntity};
  std::vector<Rule> rules;
  std::unordered_map<gz::sim::Entity, Rule> collisions;
  std::unordered_set<std::string> foundLinks;
  std::unordered_set<gz::sim::Entity> reportedContacts;
  gz::common::ConnectionPtr connection;
};
}  // namespace megarover_description

GZ_ADD_PLUGIN(megarover_description::SupportFriction, gz::sim::System,
  megarover_description::SupportFriction::ISystemConfigure,
  megarover_description::SupportFriction::ISystemPreUpdate)
