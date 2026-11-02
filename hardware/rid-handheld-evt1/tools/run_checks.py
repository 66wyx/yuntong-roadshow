"""Native firmware logic tests + engineering consistency. Requires C++17 c++/g++/clang++ or zig.

python tools/run_checks.py --compiler path/to/zig.exe
The ESP-IDF projects, electronics, antennas and physical enclosure are NOT validated here.
"""
from pathlib import Path
import argparse
import csv
import json
import shutil
import subprocess
import tempfile
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'validation';OUT.mkdir(exist_ok=True)
arg=argparse.ArgumentParser();arg.add_argument('--compiler');opts=arg.parse_args()
compiler=opts.compiler or shutil.which('c++') or shutil.which('clang++') or shutil.which('g++') or shutil.which('zig')
if not compiler: raise SystemExit('C++17 compiler not found. Supply --compiler path/to/zig.exe or c++.')
subprocess.run([sys.executable,str(ROOT/'tools/generate_design.py')],check=True)
with tempfile.TemporaryDirectory(prefix='rid-evt1-') as tmp:
    exe=Path(tmp)/('core-tests.exe' if sys.platform=='win32' else 'core-tests')
    cmd=[compiler]+(['c++'] if Path(compiler).stem=='zig' else [])+[
        '-std=c++17','-Wall','-Wextra','-Werror','-O0','-I'+str(ROOT/'firmware/core/include'),
        str(ROOT/'firmware/core/src/rid_core.cpp'),str(ROOT/'firmware/tests/core_tests.cpp'),'-o',str(exe)]
    subprocess.run(cmd,check=True,capture_output=True,text=True)
    result=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
    (OUT/'native-core-tests.txt').write_text(result.stdout,encoding='utf-8')
cases=[line[5:] for line in result.stdout.splitlines() if line.startswith('PASS ')]
cfg=json.loads((ROOT/'design.json').read_text(encoding='utf-8'))
cad=json.loads((ROOT/'mechanical/generated/cad-checks.json').read_text(encoding='utf-8'))
assert cad['all_solids_valid'] and not cad['physical_envelope_intersections']
assert all(cad[k]>0 for k in ('battery_to_pcb_nominal_gap_mm','module_to_display_nominal_gap_mm','gnss_patch_to_front_roof_nominal_gap_mm'))
assert cad['revision']==cfg['revision']
records=list(csv.DictReader((ROOT/'electrical/gpio.csv').open(encoding='utf-8')))
report=dict(date=cfg['date'],revision=cfg['revision'],native_cpp17='passed',native_test_count=len(cases),
            native_cases=cases,gpio_assignments=len(records),nominal_cad_solid_count=cad['part_count'],
            nominal_cad_intersections=len(cad['physical_envelope_intersections']),
            esp_idf_build='not_run_toolchain_unavailable',physical_validation='not_run_no_hardware',
            schematic_erc='not_run_schematic_not_complete',pcb_drc='not_run_no_copper_layout',
            display_interface='supplier_confirmation_required',battery_pack='supplier_maximum_drawing_required')
(OUT/'validation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(result.stdout)
print(json.dumps({k:v for k,v in report.items() if k!='native_cases'},ensure_ascii=False))
