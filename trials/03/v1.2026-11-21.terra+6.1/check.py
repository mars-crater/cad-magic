"""Check both first submissions against the dimensional brief."""
from math import cos, sin, pi
from pathlib import Path
import cadquery as cq

for path in sorted(Path(__file__).parent.glob('*/*.step')):
    count = 11 if '11' in path.stem else 8
    part = cq.importers.importStep(str(path)).val()
    box = part.BoundingBox()
    assert part.isValid() and len(part.Solids()) == 1
    assert max(abs(a-b) for a,b in zip((box.xlen,box.ylen,box.zlen),(64,64,6))) < 1e-5
    bore = cq.Solid.makeCylinder(3.999,8,(0,0,-1))
    assert part.intersect(bore).Volume() < 1e-6
    expected = pi*(32**2-4**2)*6-count*2*(7*3+pi*1.5**2)
    assert abs(part.Volume()-expected) < 1e-4
    for i in range(count):
        a = 2*pi*i/count
        for r,t,z,inside in [(23,0,3.99,True),(23,0,4.01,False),(27.99,0,5,False),(28.01,0,5,True),(23,1.49,5,False),(23,1.51,5,True)]:
            assert part.isInside((r*cos(a)-t*sin(a),r*sin(a)+t*cos(a),z)) == inside
    print(path.name, count, round(part.Volume(),6))
