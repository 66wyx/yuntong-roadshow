#include "rid_core.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <utility>

namespace rid {
namespace {
constexpr double pi = 3.14159265358979323846;
double rad(double d) { return d*pi/180.0; }
double deg(double r) { return r*180.0/pi; }
double wrap(double v) { v=std::fmod(v,360.0); return v<0?v+360:v; }
bool fresh(std::uint64_t at, std::uint64_t now, std::uint64_t age) { return at<=now && now-at<=age; }
bool valid_fix(const Fix& f, std::uint64_t now, std::uint64_t age) {
  return f.valid && std::isfinite(f.latitude_deg) && std::isfinite(f.longitude_deg)
    && std::abs(f.latitude_deg)<=90 && std::abs(f.longitude_deg)<=180
    && fresh(f.received_ms,now,age);
}
std::array<double,3> surface_ecef(const Fix& f) {
  constexpr double a=6378137.0, e2=6.6943799901413165e-3;
  double p=rad(f.latitude_deg),l=rad(f.longitude_deg),sp=std::sin(p),cp=std::cos(p);
  double n=a/std::sqrt(1-e2*sp*sp);
  return {n*cp*std::cos(l),n*cp*std::sin(l),n*(1-e2)*sp};
}
}
View PoseController::view() const {
  if(mode_==ViewMode::Radar) return View::Radar;
  if(mode_==ViewMode::Height) return View::Height;
  return stable_;
}
View PoseController::update(double tilt, bool moving, std::uint64_t now) {
  if(now<last_time_) pending_.reset();
  last_time_=now;
  if(!std::isfinite(tilt)||tilt<0||tilt>90||moving) { pending_.reset(); return view(); }
  std::optional<View> desired;
  if(tilt<25) desired=View::Radar;
  if(tilt>60) desired=View::Height;
  if(!desired || *desired==stable_) { pending_.reset(); return view(); }
  if(!pending_ || *pending_!=*desired) { pending_=desired; pending_since_=now; }
  if(now-pending_since_>=600) { stable_=*desired; pending_.reset(); }
  return view();
}
RelativePosition relative_position(const Fix& self,const Fix& target,std::uint64_t now,std::uint64_t age) {
  RelativePosition out;
  if(!valid_fix(self,now,age)||!valid_fix(target,now,age)) return out;
  const auto a=surface_ecef(self),b=surface_ecef(target);
  double x=b[0]-a[0],y=b[1]-a[1],z=b[2]-a[2];
  double l=rad(self.longitude_deg),p=rad(self.latitude_deg);
  out.east_m=-std::sin(l)*x+std::cos(l)*y;
  out.north_m=-std::sin(p)*std::cos(l)*x-std::sin(p)*std::sin(l)*y+std::cos(p)*z;
  out.horizontal_m=std::hypot(out.east_m,out.north_m);
  out.position_valid=true;
  if(out.horizontal_m>=1.0) out.bearing_true_deg=wrap(deg(std::atan2(out.east_m,out.north_m)));
  if(self.ellipsoid_height_m && target.ellipsoid_height_m
     && std::isfinite(*self.ellipsoid_height_m) && std::isfinite(*target.ellipsoid_height_m)) {
    out.relative_height_m=*target.ellipsoid_height_m-*self.ellipsoid_height_m;
    if(out.horizontal_m>=1.0 || std::abs(*out.relative_height_m)>=1.0)
      out.elevation_deg=deg(std::atan2(*out.relative_height_m,out.horizontal_m));
  }
  return out;
}
std::optional<double> pointing_heading(const std::array<double,3>& top,
  const std::array<double,3>& back,double tilt,bool reliable) {
  if(!reliable||!std::isfinite(tilt)||tilt<0||tilt>90) return std::nullopt;
  for(double v:top) if(!std::isfinite(v)) return std::nullopt;
  for(double v:back) if(!std::isfinite(v)) return std::nullopt;
  // Use horizontal screen top near flat, screen back normal near upright.
  double weight=std::clamp((tilt-25.0)/35.0,0.0,1.0);
  double e=top[0]*(1-weight)+back[0]*weight;
  double n=top[1]*(1-weight)+back[1]*weight;
  if(std::hypot(e,n)<0.05) return std::nullopt;
  return wrap(deg(std::atan2(e,n)));
}
std::optional<double> screen_bearing(double bearing,std::optional<double> heading) {
  if(!std::isfinite(bearing)) return std::nullopt;
  if(!heading) return wrap(bearing); // degraded north-up view
  if(!std::isfinite(*heading)) return std::nullopt;
  return wrap(bearing-*heading);
}
void Track::update_identity(std::string value,std::uint64_t at) {
  if(at>=identity_received_ms) { identity=std::move(value); identity_received_ms=at; }
}
void Track::update_position(const Fix& value) {
  if(value.received_ms>=position.received_ms) position=value;
}
bool Track::position_fresh(std::uint64_t now,std::uint64_t age) const { return valid_fix(position,now,age); }
ChargePhase charge_phase(const ChargerReading& r) {
  if(!r.communication_ok) return ChargePhase::Unknown;
  if(r.fault09!=0) return ChargePhase::Fault;
  if(!(r.status08&0x04)) return ChargePhase::OnBattery;
  switch((r.status08>>3)&3) {
    case 0:return ChargePhase::NotCharging;
    case 1:return ChargePhase::Precharge;
    case 2:return ChargePhase::Charging;
    case 3:return r.topoff_active?ChargePhase::TopOff:ChargePhase::Full;
  }
  return ChargePhase::Unknown;
}
unsigned input_limit_ma(UsbCurrent mode,bool ok) {
  if(mode==UsbCurrent::Detached) return 0;
  if(!ok || mode==UsbCurrent::Unconfigured) return 100;
  if(mode==UsbCurrent::DefaultConfigured) return 500;
  // Board thermal/current budget caps the 3A advertisement to 1.5A.
  return 1500;
}
std::uint16_t crc16(const std::uint8_t* data,std::size_t n) {
  std::uint16_t crc=0xffff;
  for(std::size_t i=0;i<n;++i) { crc^=static_cast<std::uint16_t>(data[i])<<8;
    for(int b=0;b<8;++b) crc=static_cast<std::uint16_t>((crc&0x8000)?(crc<<1)^0x1021:crc<<1); }
  return crc;
}
std::size_t encode_frame(const RadioFrame& f,std::uint8_t* out,std::size_t cap) {
  if(f.size>f.payload.size() || cap<static_cast<std::size_t>(f.size)+8) return 0;
  out[0]=0xa5;out[1]=0x5a;out[2]=1;out[3]=f.transport;
  out[4]=static_cast<std::uint8_t>(f.size);out[5]=static_cast<std::uint8_t>(f.size>>8);
  std::memcpy(out+6,f.payload.data(),f.size);
  const auto crc=crc16(out+2,f.size+4);
  out[6+f.size]=static_cast<std::uint8_t>(crc);out[7+f.size]=static_cast<std::uint8_t>(crc>>8);
  return f.size+8;
}
void FrameParser::consume(std::size_t n) {
  n=std::min(n,count_);count_-=n;
  if(count_) std::memmove(bytes_.data(),bytes_.data()+n,count_);
}
std::optional<RadioFrame> FrameParser::push(std::uint8_t b) {
  if(count_==bytes_.size()) {consume(1);++rejected_;}
  bytes_[count_++]=b;
  while(count_>=2) {
    if(bytes_[0]!=0xa5 || bytes_[1]!=0x5a) {consume(1);continue;}
    if(count_<6) return std::nullopt;
    const std::size_t n=bytes_[4]|(static_cast<std::size_t>(bytes_[5])<<8);
    if(bytes_[2]!=1 || n>512) {++rejected_;consume(1);continue;}
    const std::size_t total=n+8;
    if(count_<total) return std::nullopt;
    const auto expected=static_cast<std::uint16_t>(bytes_[n+6]|(bytes_[n+7]<<8));
    if(crc16(bytes_.data()+2,n+4)!=expected) {++rejected_;consume(1);continue;}
    RadioFrame f;f.transport=bytes_[3];f.size=static_cast<std::uint16_t>(n);
    std::memcpy(f.payload.data(),bytes_.data()+6,n);consume(total);return f;
  }
  return std::nullopt;
}
}
