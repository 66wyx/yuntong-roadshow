"""Native analytic and exact-Bezier CAD primitives, in millimetres.

There is no mesh/STL input. Curves are CAD circles/arcs and cubic Beziers.
"""
import math
import cadquery as cq
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
from OCP.Geom import Geom_BezierCurve
from OCP.TColgp import TColgp_Array1OfPnt
from OCP.gp import gp_Pnt


def _vec(point):
    return cq.Vector(*point, 0) if len(point)==2 else cq.Vector(*point)


def _line(a,b):
    return cq.Edge.makeLine(_vec(a),_vec(b))


def _prism(wire,z0,z1,x=0,y=0):
    return cq.Solid.extrudeLinear(wire, [], cq.Vector(0,0,z1-z0)).translate((x,y,z0))


def rounded_wire(w,h,r):
    r=max(0,min(r,w/2,h/2))
    if r<1e-9:
        return cq.Wire.makePolygon([cq.Vector(-w/2,-h/2),cq.Vector(w/2,-h/2),cq.Vector(w/2,h/2),cq.Vector(-w/2,h/2)],close=True)
    if abs(w-h)<1e-9 and abs(2*r-w)<1e-9:
        return cq.Wire.makeCircle(r,cq.Vector(),cq.Vector(0,0,1))
    arcs=[]
    for x,y,angle in ((w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)):
        pts=[(x+r*math.cos(math.radians(angle+a)),y+r*math.sin(math.radians(angle+a))) for a in (0,45,90)]
        arcs.append(pts)
    edges=[]
    for i,pts in enumerate(arcs):
        edges.append(cq.Edge.makeThreePointArc(*[_vec(p) for p in pts]))
        end,next_start=pts[-1],arcs[(i+1)%4][0]
        if math.dist(end,next_start)>1e-8:edges.append(_line(end,next_start))
    return cq.Wire.assembleEdges(edges)


def rect(w,h,z0,z1,x=0,y=0,r=.2):
    return _prism(rounded_wire(w,h,r),z0,z1,x,y)


def cyl(r,z0,z1,x=0,y=0):
    return cq.Solid.makeCylinder(r,z1-z0,cq.Vector(x,y,z0),cq.Vector(0,0,1))


def cone_z(r0,r1,z0,z1,x=0,y=0):
    return cq.Solid.makeCone(r0,r1,z1-z0,cq.Vector(x,y,z0),cq.Vector(0,0,1))


def _bezier(points):
    poles=TColgp_Array1OfPnt(1,len(points))
    for i,(x,y) in enumerate(points,start=1):poles.SetValue(i,gp_Pnt(x,y,0))
    return cq.Edge(BRepBuilderAPI_MakeEdge(Geom_BezierCurve(poles)).Edge())


def corner_wire(w,h,L):
    controls=[[(0,0),(.28*L,0),(.64*L,0),(.82*L,-.18*L)],
              [(.82*L,-.18*L),(L,-.36*L),(L,-.72*L),(L,-L)]]
    quadrants=[]
    for sx,sy,reverse in ((1,1,False),(1,-1,True),(-1,-1,False),(-1,1,True)):
        curves=[[(sx*(w/2-L+xx),sy*(h/2+yy)) for xx,yy in c] for c in controls]
        if reverse:curves=[list(reversed(c)) for c in reversed(curves)]
        quadrants.append(curves)
    edges=[]
    for i,curves in enumerate(quadrants):
        edges.extend(_bezier(c) for c in curves)
        edges.append(_line(curves[-1][-1],quadrants[(i+1)%4][0][0]))
    return cq.Wire.assembleEdges(edges)


def corner_prism(w,h,L,z0,z1,x=0,y=0):
    return _prism(corner_wire(w,h,L),z0,z1,x,y)


def rocker_prism(w,h,upper,z0,z1,x=0,y=0):
    radius=w/2;c=h/2-radius
    if upper:
        arc=[(radius,c),(0,c+radius),(-radius,c)]
        rest=[(-radius,-h/2),(radius,-h/2)]
    else:
        arc=[(-radius,-c),(0,-c-radius),(radius,-c)]
        rest=[(radius,h/2),(-radius,h/2)]
    edges=[cq.Edge.makeThreePointArc(*[_vec(p) for p in arc])]
    points=[arc[-1],*rest,arc[0]]
    edges.extend(_line(a,b) for a,b in zip(points,points[1:]))
    return _prism(cq.Wire.assembleEdges(edges),z0,z1,x,y)


def rotate_x_about_origin(shape,deg,z_offset=0):
    return shape.rotate((0,0,0),(1,0,0),deg).translate((0,0,z_offset))


def side_rect(w,h,y0,y1,x,z,r=.2):
    return rotate_x_about_origin(rect(w,h,-y1,-y0,x,0,r),90,z)


def side_hole(r,y0,y1,x,z):
    return rotate_x_about_origin(cyl(r,-y1,-y0,x,0),90,z)


def union(a,b):
    return a.fuse(b).clean()


def cut(a,b):
    return a.cut(b).clean()


def stroke(a,b,width,z0,z1):
    length=math.dist(a,b)
    dx=-(b[1]-a[1])*width/(2*length);dy=(b[0]-a[0])*width/(2*length)
    pts=[(a[0]+dx,a[1]+dy),(a[0]-dx,a[1]-dy),(b[0]-dx,b[1]-dy),(b[0]+dx,b[1]+dy)]
    wire=cq.Wire.makePolygon([_vec(p) for p in pts],close=True)
    return _prism(wire,z0,z1)
