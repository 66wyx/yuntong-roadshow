"""Read exported binary STL files independently of Blender. Standard library only.

Run on the host: python hardware/rid-handheld-rig-p1/v4/scripts/06_verify_stl.py
Checks file integrity, edge incidence/winding, connectivity, volume and mm scale.
Does not claim self-intersection, slicer or physical fit verification.
"""
from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import json
import struct

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'validation/export-manifest.json').read_text(encoding='utf-8'))
results = []
for item in manifest['parts']:
    path = ROOT / 'stl' / item['file']
    data = path.read_bytes()
    count = struct.unpack_from('<I', data, 80)[0]
    assert len(data) == 84 + 50 * count, f'Truncated or unexpected binary STL: {path}'
    edges, directions, adjacency = Counter(), Counter(), defaultdict(set)
    vertices, ids = [], {}
    volume, degenerate = 0.0, 0
    for index in range(count):
        block = struct.unpack_from('<12fH', data, 84 + 50 * index)
        points = [tuple(block[3 + j * 3:6 + j * 3]) for j in range(3)]
        triangle = []
        for point in points:
            if point not in ids:
                ids[point] = len(vertices)
                vertices.append(point)
            triangle.append(ids[point])
        if len(set(triangle)) != 3:
            degenerate += 1
        for a, b in zip(triangle, triangle[1:] + triangle[:1]):
            edge = (min(a, b), max(a, b))
            edges[edge] += 1
            directions[edge] += 1 if a < b else -1
            adjacency[a].add(b)
            adjacency[b].add(a)
        a, b, c = points
        volume += (a[0] * (b[1]*c[2]-b[2]*c[1])
                   - a[1] * (b[0]*c[2]-b[2]*c[0])
                   + a[2] * (b[0]*c[1]-b[1]*c[0])) / 6
    seen, components = set(), 0
    for vertex in range(len(vertices)):
        if vertex in seen:
            continue
        components += 1
        todo = [vertex]
        seen.add(vertex)
        while todo:
            current = todo.pop()
            for other in adjacency[current] - seen:
                seen.add(other)
                todo.append(other)
    lower = [min(v[k] for v in vertices) for k in range(3)]
    upper = [max(v[k] for v in vertices) for k in range(3)]
    bbox = [upper[k] - lower[k] for k in range(3)]
    bad_edges = sum(value != 2 for value in edges.values())
    bad_winding = sum(value != 0 for value in directions.values())
    valid = (count == item['triangles'] and bad_edges == 0 and bad_winding == 0
             and degenerate == 0 and components == 1 and volume > 0
             and abs(lower[2]) < 1e-4
             and all(abs(bbox[k] - item['bbox_mm'][k]) < .002 for k in range(3)))
    results.append({'file':path.name, 'sha256':hashlib.sha256(data).hexdigest(),
                    'triangles':count, 'nonmanifold_edges':bad_edges,
                    'inconsistent_edge_winding':bad_winding, 'components':components,
                    'degenerate_triangles':degenerate, 'volume_cm3':round(volume/1000,4),
                    'bbox_mm':[round(v,4) for v in bbox],
                    'minimum_z_mm':round(lower[2],6), 'pass':valid})
report = {'units':'mm', 'all_pass':len(results) == 13 and all(r['pass'] for r in results),
          'scope':'Exported STL topology, winding, connectivity, scale and ground position; not a physical fit or slicing test',
          'parts':results}
(ROOT / 'validation/stl-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'all_pass':report['all_pass'], 'parts':len(results),
                  'failures':[r['file'] for r in results if not r['pass']]}))
raise SystemExit(0 if report['all_pass'] else 1)
