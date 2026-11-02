#include "rid_core.hpp"
#include <cassert>
#include <cmath>
#include <cstdio>
#include <limits>
using namespace rid;
int main() {
  int n=0;
  auto pass=[&](const char* title){++n;std::printf("PASS %s\n",title);};
  PoseController p;
  assert(p.update(80,false,100)==View::Radar);
  assert(p.update(80,false,699)==View::Radar);
  assert(p.update(80,false,700)==View::Height);pass("pose stable threshold");
  assert(p.update(40,false,900)==View::Height);
  assert(p.update(10,true,1000)==View::Height);
  assert(p.update(10,false,1100)==View::Height);
  assert(p.update(10,false,1700)==View::Radar);pass("hysteresis and motion rejection");
  p.set_mode(ViewMode::Radar);p.update(80,false,2000);assert(p.update(80,false,2700)==View::Radar);pass("manual view override");
  p.set_mode(ViewMode::Automatic);p.update(10,false,10);assert(p.update(10,false,610)==View::Radar);pass("clock rollback resets pending timer");
  Fix a{0,0,10.0,1000,true},b{0,0.001,30.0,1000,true};
  auto r=relative_position(a,b,1500);
  assert(r.position_valid && std::abs(r.horizontal_m-111.31949)<.01);
  assert(r.bearing_true_deg && std::abs(*r.bearing_true_deg-90)<.001);
  assert(r.relative_height_m && *r.relative_height_m==20);pass("WGS84 east baseline and relative ellipsoid height");
  b.ellipsoid_height_m.reset();r=relative_position(a,b,1500);
  assert(r.position_valid&&!r.relative_height_m&&!r.elevation_deg);pass("missing height stays unknown");
  assert(!relative_position(a,b,5000).position_valid);
  b.received_ms=7000;assert(!relative_position(a,b,1500).position_valid);pass("stale and future fix rejection");
  b=a;r=relative_position(a,b,1500);assert(r.position_valid&&!r.bearing_true_deg);pass("coincident position has no invented bearing");
  auto heading=pointing_heading({0,1,0},{0,0,-1},0,true);assert(heading&&*heading==0);
  heading=pointing_heading({0,0,1},{1,0,0},90,true);assert(heading&&std::abs(*heading-90)<.01);
  assert(!pointing_heading({0,0,1},{0,0,-1},90,true));pass("upright uses screen back and rejects degenerate projection");
  assert(!pointing_heading({0,1,0},{0,1,0},45,false));assert(*screen_bearing(45,std::nullopt)==45);pass("unreliable compass degrades to north-up");
  Track t;t.update_position(a);t.update_identity("LAB-1",1000);t.update_identity("LAB-1",5000);
  assert(!t.position_fresh(5000));pass("new identity cannot refresh old position");
  Fix older=a;older.received_ms=900;older.latitude_deg=25;t.update_position(older);assert(t.position.latitude_deg==0);pass("out of order position ignored");
  assert(charge_phase({0x1c,0,false,true})==ChargePhase::Full);
  assert(charge_phase({0x1c,0,true,true})==ChargePhase::TopOff);
  assert(charge_phase({0x14,0,false,true})==ChargePhase::Charging);
  assert(charge_phase({0x04,0,false,true})==ChargePhase::NotCharging);
  assert(charge_phase({0x1c,1,false,true})==ChargePhase::Fault);
  assert(charge_phase({0x1c,0,false,false})==ChargePhase::Unknown);pass("charger completion distinct from fault idle and topoff");
  assert(input_limit_ma(UsbCurrent::Unconfigured,true)==100);
  assert(input_limit_ma(UsbCurrent::DefaultConfigured,true)==500);
  assert(input_limit_ma(UsbCurrent::Advertised3000,true)==1500);
  assert(input_limit_ma(UsbCurrent::Advertised1500,false)==100);pass("USB input current bounded by valid source detection");
  const std::uint8_t standard[]={'1','2','3','4','5','6','7','8','9'};
  assert(crc16(standard,9)==0x29b1);pass("CRC16 CCITT standard vector");
  RadioFrame f;f.transport=2;f.size=512;
  for(unsigned i=0;i<512;++i)f.payload[i]=static_cast<std::uint8_t>(i);
  std::array<std::uint8_t,520> wire{};auto len=encode_frame(f,wire.data(),wire.size());assert(len==520);
  FrameParser parser;std::optional<RadioFrame> decoded;
  for(auto c:wire){auto v=parser.push(c);if(v)decoded=v;}
  assert(decoded&&decoded->size==512&&decoded->payload==f.payload);pass("maximum payload fragmented UART stream");
  wire[30]^=1;decoded.reset();for(auto c:wire){auto v=parser.push(c);if(v)decoded=v;}
  assert(!decoded&&parser.rejected()>0);
  encode_frame(f,wire.data(),wire.size());for(auto c:wire){auto v=parser.push(c);if(v)decoded=v;}
  assert(decoded);pass("CRC corruption resynchronizes to next valid frame");
  RadioFrame small;small.transport=1;small.size=3;small.payload[0]=1;small.payload[1]=2;small.payload[2]=3;
  std::array<std::uint8_t,20> sw{};len=encode_frame(small,sw.data(),sw.size());
  for(auto c:std::array<std::uint8_t,6>{0xa5,0x5a,1,0,0xff,0xff})parser.push(c);
  decoded.reset();for(std::size_t i=0;i<len;++i){auto v=parser.push(sw[i]);if(v)decoded=v;}
  assert(decoded&&decoded->size==3);pass("invalid UART length resynchronizes");
  parser.push(0xa5);parser.push(0x5a);parser.push(1);parser.push(2);parser.push(0);parser.push(2);
  parser.reset_partial();decoded.reset();
  for(std::size_t i=0;i<len;++i){auto v=parser.push(sw[i]);if(v)decoded=v;}
  assert(decoded&&decoded->size==3);pass("inter-byte timeout resets truncated frame");
  std::printf("%d checks passed\n",n);return 0;
}
