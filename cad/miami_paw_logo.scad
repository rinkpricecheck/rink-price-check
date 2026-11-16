// Golden Wolves - Miami paw logo plaque (standalone).
// Traced straight from the finished logo artwork: black paw with gold rim, grey claws,
// gold pads, the wolf head, varsity "MIAMI" and the GOLDEN WOLVES banner.
// Built as a black core with a flat full-colour face on top (every colour at the same height).
// Wall-mounted: two keyhole slots on the back.
//
// part = "all" for a coloured preview, or one colour for multicolour STL export:
//        black | yellow | white | red | gray (the claws)
// Needs the traced files in ./paw_logo/
//
// Units: mm.  X = across, Z = up, Y = thickness (front face at -Y).

part = "all";
$fn = 48;

C = [["black",[0.06,0.06,0.06]], ["yellow",[0.99,0.71,0.02]], ["white",[0.98,0.98,0.98]],
     ["red",[0.75,0.04,0.08]], ["gray",[0.79,0.80,0.83]]];
function rgb(n) = [for (c = C) if (c[0] == n) c[1]][0];
module col(n) { if (part == "all") color(rgb(n)) children(); else if (part == n) children(); }

W    = 212;   // overall width; 212 wide makes it about 253 tall, so it fits a 256 mm bed in one piece
CORE = 5;     // black core thickness
FACE = 1.2;   // colour face thickness

// traced at 1 px = 1 mm on a 1254 x 1254 canvas; the logo spans x 129..1121, y 53..1237 (y up)
module art(name) { scale(W / 992) translate([-625, -645]) import(str("paw_logo/", name, ".svg")); }

module slab(t) { translate([0, t/2, 0]) rotate([90, 0, 0]) linear_extrude(t) children(); }
module face()  { translate([0, -CORE/2, 0]) rotate([90, 0, 0]) linear_extrude(FACE) children(); }

// The traced colours tile the logo with no gaps; each is also grown by GROW so the curve fitting
// can't open hairline seams (they'd fill with black and print as black specks along the edges).
// Overlaps go to the higher colour: red, gray, white, yellow, then black takes what is left.
GROW = 0.15;
module c2d(n)     { intersection() { offset(delta = GROW) art(n); art("outline"); } }
module red2d()    { c2d("red"); }
module gray2d()   { difference() { c2d("gray"); red2d(); } }
module white2d()  { difference() { c2d("white"); red2d(); gray2d(); } }
module yellow2d() { difference() { c2d("yellow"); red2d(); gray2d(); white2d(); } }
module black2d()  { difference() { art("outline"); red2d(); gray2d(); white2d(); yellow2d(); } }

col("black") difference() {
    slab(CORE) art("outline");
    for (x = [-45, 45])                       // keyhole slots in the back
        translate([x, CORE/2 - 3, 50]) rotate([-90, 0, 0]) linear_extrude(4) {
            circle(d = 9); translate([-2.5, 0]) square([5, 12]); translate([0, 12]) circle(d = 5);
        }
}
col("black")  face() black2d();
col("yellow") face() yellow2d();
col("white")  face() white2d();
col("red")    face() red2d();
col("gray")   face() gray2d();
