#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>

namespace rid {
enum class View { Radar, Height };
enum class ViewMode { Automatic, Radar, Height };

class PoseController {
 public:
  View update(double tilt_degrees, bool moving, std::uint64_t now_ms);
  void set_mode(ViewMode mode) { mode_ = mode; }
  View view() const;
 private:
  ViewMode mode_{ViewMode::Automatic};
  View stable_{View::Radar};
  std::optional<View> pending_;
  std::uint64_t pending_since_{0}, last_time_{0};
};

struct Fix {
  double latitude_deg{0}, longitude_deg{0};
  std::optional<double> ellipsoid_height_m;
  std::uint64_t received_ms{0};
  bool valid{false};
};
struct RelativePosition {
  bool position_valid{false};
  double east_m{0}, north_m{0}, horizontal_m{0};
  std::optional<double> bearing_true_deg, relative_height_m, elevation_deg;
};
RelativePosition relative_position(const Fix& self, const Fix& aircraft,
                                   std::uint64_t now_ms, std::uint64_t max_age_ms=3000);
// Vectors already transformed to world ENU by a calibrated attitude estimator.
std::optional<double> pointing_heading(const std::array<double,3>& top_edge_enu,
                                      const std::array<double,3>& screen_back_enu,
                                      double tilt_deg, bool compass_reliable);
std::optional<double> screen_bearing(double bearing_true_deg,
                                    std::optional<double> true_heading_deg);

struct Track {
  std::string identity;
  Fix position;
  std::uint64_t identity_received_ms{0};
  bool simulated{false};
  void update_identity(std::string value, std::uint64_t at_ms);
  void update_position(const Fix& value);
  bool position_fresh(std::uint64_t now_ms, std::uint64_t max_age_ms=3000) const;
};

enum class ChargePhase { OnBattery, NotCharging, Precharge, Charging, TopOff, Full, Fault, Unknown };
struct ChargerReading {
  std::uint8_t status08{0}, fault09{0};
  bool topoff_active{false}, communication_ok{false};
};
ChargePhase charge_phase(const ChargerReading& reading);
enum class UsbCurrent { Detached, Unconfigured, DefaultConfigured, Advertised1500, Advertised3000 };
unsigned input_limit_ma(UsbCurrent mode, bool controller_ok);

struct RadioFrame {
  std::uint8_t transport{0};
  std::uint16_t size{0};
  std::array<std::uint8_t,512> payload{};
};
std::uint16_t crc16(const std::uint8_t* data, std::size_t size);
// UART wire format: A5 5A, version(1), transport, lenLE16, payload, crcLE16.
std::size_t encode_frame(const RadioFrame&, std::uint8_t* output, std::size_t capacity);
class FrameParser {
 public:
  std::optional<RadioFrame> push(std::uint8_t byte);
  void reset_partial() { if(count_) ++rejected_; count_=0; }
  std::uint64_t rejected() const { return rejected_; }
 private:
  std::array<std::uint8_t,520> bytes_{};
  std::size_t count_{0};
  std::uint64_t rejected_{0};
  void consume(std::size_t n);
};
}
