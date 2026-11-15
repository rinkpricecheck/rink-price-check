// Golden Wolves - Miami paw logo, hanging sign (standalone).
// The traced paw logo on BOTH faces (the back reads correctly from behind). Two 1" strap slots
// are cut horizontally just under the claws, 80 mm apart to line up with the stick loops;
// the straps run up to the loops under the hockey-stick bracket (miami_hanging.scad, piece = "stick").
// About 250 x 298 mm, so each printed half fits a Bambu H2C bed in one piece.
//
// part = "all" for a coloured preview, or one colour for multicolour STL export:
//        black | yellow | white | red | gray (the claws)
// half / piece: see "split printing" near the end
// Needs the traced files in ./paw_logo/
//
// Units: mm.  X = across, Z = up, Y = thickness (front face at -Y).

part = "all";
$fn = 48;

C = [["black",[0.06,0.06,0.06]], ["yellow",[0.99,0.71,0.02]], ["white",[0.98,0.98,0.98]],
     ["red",[0.75,0.04,0.08]], ["gray",[0.79,0.80,0.83]]];
function rgb(n) = [for (c = C) if (c[0] == n) c[1]][0];
module col(n) { if (part == "all") color(rgb(n)) children(); else if (part == n) children(); }

W    = 250;   // paw width; the whole sign is about 250 x 298 mm
CORE = 8;     // black core thickness (4 mm per printed half)
FACE = 1.2;   // colour face thickness, each side

// traced at 1 px = 1 mm on a 1254 x 1254 canvas; the logo spans x 129..1121, y 53..1237 (y up)
module art(name) { scale(W / 992) translate([-625, -645]) import(str("paw_logo/", name, ".svg")); }

// strap slots: horizontal, under the claws, 80 mm apart to line up with the stick loops (they clip the side claws)
SLOT_W = 28;  SLOT_H = 5;  SLOT_X = 40;  SLOT_Z = 95;  SLOT_A = 0;    // horizontal, 80 mm apart like the stick loops
module slots2d() {
    for (m = [0, 1]) mirror([m, 0]) translate([SLOT_X, SLOT_Z]) rotate(-SLOT_A)
        offset(r = 1.5) offset(delta = -1.5) square([SLOT_W, SLOT_H], center = true);
}

// face colours: each one is cut out of the ones below it so the pieces never overlap
module red2d()    { art("red"); }
module gray2d()   { difference() { art("gray"); red2d(); } }
module white2d()  { difference() { art("white"); red2d(); gray2d(); } }
module yellow2d() { difference() { art("yellow"); red2d(); gray2d(); white2d(); } }
module all2d()    { art("outline"); }
module black2d()  { difference() { all2d(); red2d(); gray2d(); white2d(); yellow2d(); } }

module slab(t) { translate([0, t/2, 0]) rotate([90, 0, 0]) linear_extrude(t) children(); }
// same 2D artwork on the front and the back (turned so it reads correctly from behind)
module faces() {
    translate([0, -CORE/2, 0]) rotate([90, 0, 0]) linear_extrude(FACE) children();
    rotate([0, 0, 180]) translate([0, -CORE/2, 0]) rotate([90, 0, 0]) linear_extrude(FACE) children();
}

module sign() {
    col("black")  slab(CORE) all2d();
    col("black")  faces() black2d();
    col("yellow") faces() yellow2d();
    col("white")  faces() white2d();
    col("red")    faces() red2d();
    col("gray")   faces() gray2d();
}

// ---------- split printing ----------
// half  = "full" | "front" | "back" : cut down the middle (y = 0) so each half prints flat, face up
// piece = "sign" | "keys"           : the sign, or the printed alignment keys
// Each half has three 2.5 mm deep sockets (two round, one square, uneven pattern) so the halves only
// fit together one way; the 8 mm printed keys sit in them and lock the halves while the glue sets.
half  = "full";
piece = "sign";
KEY = 8;  KEY_CLR = 0.15;  KEY_DEPTH = 2.5;  KEY_H = 2*KEY_DEPTH - 0.4;
KEYS_AT = [[-70, -60, 0], [75, -20, 1], [0, 60, 0]];             // [x, z, square?]
module key2d(sq, d) { if (sq) square(d, center = true); else circle(d = d, $fn = 48); }
module key_sockets() {
    for (p = KEYS_AT) translate([p[0], 0, p[1]]) rotate([90, 0, 0])
        linear_extrude(2*KEY_DEPTH, center = true) key2d(p[2], KEY + 2*KEY_CLR);
}
module keys() {       // 1 set of 3 + 2 spares, lying so the front-half orientation stands them upright
    shapes = [0, 0, 1, 0, 1];
    col("black") for (i = [0 : len(shapes) - 1])
        translate([i*14, 0, 0]) rotate([90, 0, 0]) linear_extrude(KEY_H) key2d(shapes[i], KEY);
}
module cut_half() {
    if (half == "front")     intersection() { children(); translate([-1000, -100, -1000]) cube([2000, 100, 2000]); }
    else if (half == "back") intersection() { children(); translate([-1000, 0, -1000]) cube([2000, 100, 2000]); }
    else children();
}

// ---------- model ----------
if (piece == "keys") keys();
if (piece == "sign") cut_half() difference() {
    sign();
    translate([0, 50, 0]) rotate([90, 0, 0]) linear_extrude(100) slots2d();      // strap slots, all the way through
    if (half != "full") key_sockets();
}
