#!/tmp/cad-magic-venv/bin/python
"""Check exported STEP geometry."""
import math
from pathlib import Path
import cadquery as cq

here = Path(__file__).resolve().parent
for count in (8, 11):
    s = cq.importers.importStep(str(here / f'dial_{count}.step')).val()
    bb = s.BoundingBox()
    capsule_area = (10 - 3) * 3 + math.pi * 1.5**2
    expected = math.pi * (32**2 - 4**2) * 6 - count * capsule_area * 2
    solids = len(s.Solids())
    print(f'{count}: valid={s.isValid()} solids={solids} bbox=({bb.xlen:.6f},{bb.ylen:.6f},{bb.zlen:.6f}) volume={s.Volume():.6f} expected={expected:.6f} delta={s.Volume()-expected:.8f}')
    assert s.isValid() and solids == 1
    assert all(abs(a-b) < 1e-5 for a,b in zip((bb.xlen,bb.ylen,bb.zlen),(64,64,6)))
    assert abs(s.Volume()-expected) < 1e-5
    floors = [f for f in s.Faces() if f.geomType() == 'PLANE' and abs(f.Center().z - 4) < 1e-6]
    assert len(floors) == count
    for i in range(count):
        a = 2 * math.pi * i / count
        x, y = 23 * math.cos(a), 23 * math.sin(a)
        assert any(math.hypot(f.Center().x - x, f.Center().y - y) < 1e-5 and abs(f.Area() - capsule_area) < 1e-5 for f in floors)
    print(f'  {len(floors)} slot floors at z=4, expected centers and capsule areas verified')
