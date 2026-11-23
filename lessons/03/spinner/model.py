"""Airfoil spinner study, dimensions in mm. Build the primary and check a count edit."""
from pathlib import Path
from math import cos, sin, radians, sqrt, hypot
import cadquery as cq

HERE = Path(__file__).resolve().parent


def airfoil(span, sweep=0, rise=0, chord=12, thickness=.18):
    """Symmetric NACA-style thickness distribution; closed, finite trailing edge."""
    def ordinate(t):
        return chord * 5 * thickness * (.2969*sqrt(t) - .126*t - .3516*t*t
                                        + .2843*t**3 - .1015*t**4)

    stations = [.99, .85, .65, .45, .30, .16, .07, .025, .004]
    xy = [(chord*(t-.5), ordinate(t)) for t in [1, *stations]]
    xy += [(-chord/2, 0)]
    xy += [(chord*(t-.5), -ordinate(t)) for t in [*reversed(stations), 1]]
    return (cq.Workplane("YZ", origin=(span, sweep, rise)).moveTo(*xy[0])
            .spline(xy[1:], includeCurrent=True).close().val())


def make_arm():
    # Translated parallel section planes preserve the main wing section throughout.
    wing = cq.Solid.makeLoft([airfoil(12), airfoil(40, 3.2)], ruled=True)
    tip = cq.Solid.makeLoft([airfoil(40, 3.2), airfoil(44, 4.6, 1),
                             airfoil(48, 6.6, 3.7, 10)], ruled=True)
    lower_tip = cq.Solid.makeLoft([airfoil(41, 3.7, .2, 8),
                                   airfoil(45, 5, -2.6, 5)], ruled=True)
    # Revolve the annular axial section around local y: open intake and exhaust.
    cx, cz = 30, -5.6
    nacelle = (cq.Workplane("XY").polyline([(2.5,-8),(3.2,-8),(3.8,-6),
                   (3.8,1.5),(3.0,6),(2.3,6),(2.5,1.5)]).close()
               .revolve(360,(0,0),(0,1)).val().translate((cx,1,cz)))
    pylon = (cq.Workplane("XY").box(1.8,7,3.3).val()
             .translate((cx,1,-1.6)))
    return wing.fuse(tip, lower_tip, nacelle, pylon).clean()


def build(count):
    if count not in range(3, 9):
        raise ValueError("Choose 3–8 arms; higher counts are not designed here.")
    # Hub facets align with each wing root; every rotation uses the same origin.
    hub = (cq.Workplane("XY", origin=(0,0,-2.4)).polygon(2*count,32)
           .extrude(4.8).edges("not |Z").chamfer(.55).val())
    crown = (cq.Workplane("XZ").polyline([(0,2),(11.8,2),(11.8,2.7),
              (10.9,3),(10,3),(9.6,2.7),(9.2,2.7),(8.8,3.3),(7.4,4.5),
              (5.1,5.3),(4.9,5.1),(4.6,5.3),(0,5.3)]).close()
             .revolve(360,(0,0),(0,1)).val())
    seed = make_arm()
    copies = [seed.rotate((0,0,0),(0,0,1),360*i/count) for i in range(count)]
    part = hub.fuse(crown,*copies)
    # Shallow fastener pockets are separate from the arm count.
    holes = [cq.Solid.makeCylinder(.45,.9,(13*cos(radians(i*15)),
             13*sin(radians(i*15)),1.8)) for i in range(24)]
    return part.cut(*holes).clean()


def check(path, count):
    part = cq.importers.importStep(str(path)).val()
    assert len(part.Solids()) == 1 and part.isValid()
    for i in range(count):
        angle = radians(i*360/count)
        def local(x,y,z):
            return (x*cos(angle)-y*sin(angle), x*sin(angle)+y*cos(angle), z)
        # Probe every complete engine duct along the tangential (chordwise) axis.
        duct = cq.Solid.makeCylinder(2.1,16,local(30,-8,-5.6),
                                     (-sin(angle),cos(angle),0))
        assert part.intersect(duct).Volume() < 1e-5
        for pt in [(24,0,0), (30,0,-8.6), (47,6,2.9), (44,5,-1.8)]:
            assert part.isInside(local(*pt)), (count,i,pt)
        assert not part.isInside(local(24*cos(radians(180/count)),
                                           24*sin(radians(180/count)),0))
    # Equal 1 mm radial slices away from hub, engine and tip isolate the foil.
    areas = [part.intersect(cq.Solid.makeBox(1,20,4,(x,-8,-2))).Volume()
             for x in (19,37)]
    assert abs(areas[0]-areas[1]) < .001 and areas[0] > 10
    print(f"main-wing section areas: {areas[0]:.3f}, {areas[1]:.3f} mm²")
    # Max radius is orientation-independent, unlike the axis-aligned bounding box.
    tip_radius = max(hypot(p.X,p.Y) for p in part.Vertices())
    print(f"{count} arms: valid single STEP; {count} open ducts and split tips; "
          f"max vertex radius {tip_radius:.3f} mm; height {part.BoundingBox().zlen:.3f} mm")
    return tip_radius, part.BoundingBox().zlen


if __name__ == "__main__":
    from tempfile import TemporaryDirectory
    cq.exporters.export(build(6),str(HERE/"spinner.step"))
    nominal = check(HERE/"spinner.step",6)
    with TemporaryDirectory() as tmp:
        changed = Path(tmp)/"five.step"
        cq.exporters.export(build(5),str(changed))
        edited = check(changed,5)
    assert all(abs(a-b)<.001 for a,b in zip(nominal,edited))
