// 305 Golden Wolves - Miami hanging sign (standalone).
// Striped sunset disc framed by twin palm trees, "305 GOLDEN WOLVES" and the wolf
// head directly on the sunset (no shield border), hanging from a hockey-stick wall bracket.
// Double-sided: the back looks exactly like the front.
//
// part = "all" for a coloured preview, or one colour for multicolour STL export:
//        black | yellow | orange | pink | red | white
// half / piece: see "split printing" near the end
// Needs the traced wolf files in ./wolf_v2/
//
// Units: mm.  X = along the bracket, Z = up, Y = thickness (front face at -Y).

part = "all";
$fn = 64;
FONT      = "Liberation Sans:style=Bold";
FONT_ITAL = "Liberation Sans:style=Bold Italic";

C = [["black",[0.08,0.08,0.08]], ["yellow",[0.98,0.86,0.10]], ["orange",[0.97,0.55,0.12]],
     ["pink",[0.95,0.42,0.55]], ["red",[0.85,0.15,0.12]], ["white",[0.97,0.97,0.97]]];
function rgb(n) = [for (c = C) if (c[0] == n) c[1]][0];
module col(n) { if (part == "all") color(rgb(n)) children(); else if (part == n) children(); }

R    = 150;   // sunset disc radius
CORE = 8;     // core thickness
L    = 2;     // colour layer thickness
EX   = 165;   // disc centre, along the bracket
EZ   = -270;  // disc centre height (bracket shaft is at 0)
SLOT_W = 28;  SLOT_H = 5;  SLOT_DX = 40;  SLOT_Z = 126;   // strap slots near the top of the disc

// ---------- layers ----------
module slab(t) { translate([0, t/2, 0]) rotate([90, 0, 0]) linear_extrude(t) children(); }
// same 2D artwork on the front and the back (turned so it reads correctly from behind)
module lay(a, h) {
    translate([0, -a, 0]) rotate([90, 0, 0]) linear_extrude(h) children();
    rotate([0, 0, 180]) translate([0, -a, 0]) rotate([90, 0, 0]) linear_extrude(h) children();
}

// ---------- curve helpers ----------
function bez(p0, p1, p2, t) = (1-t)*(1-t)*p0 + 2*(1-t)*t*p1 + t*t*p2;
module stroke(pts, ws) {
    for (i = [0 : len(pts) - 2]) hull() {
        translate(pts[i]) circle(d = ws[i]);
        translate(pts[i+1]) circle(d = ws[i+1]);
    }
}
N = 20;
module twin() { children(); mirror([1, 0]) children(); }

// ---------- palm trees (one each side, mirrored) ----------
TRUNK   = [for (i = [0:N]) bez([100, -150], [175, 0], [70, 142], i/N)];
TRUNK_W = [for (i = [0:N]) 28 - 12*i/N];
TOP     = [70, 148];
LEAF_A  = [140, 108, 76, 45, 15, -12];
LEAF_L  = [118, 100, 100, 122, 118, 95];
function leaf_pts(k, t0 = 0, t1 = 1) =
    [for (i = [0:N]) let(t = t0 + (t1 - t0)*i/N)
        TOP + LEAF_L[k]*t*[cos(LEAF_A[k]), sin(LEAF_A[k])] - [0, 55*t*t*abs(cos(LEAF_A[k]))]];
function leaf_w() = [for (i = [0:N]) let(t = i/N) 4 + 20*sin(180*t)*(1 - 0.35*t)];

module palm2d() {
    stroke(TRUNK, TRUNK_W);
    for (k = [0:len(LEAF_A)-1]) stroke(leaf_pts(k), leaf_w());
    translate(TOP) circle(d = 16);
}
module trunk_rings() {
    intersection() {
        offset(delta = -4) stroke(TRUNK, TRUNK_W);
        for (i = [1 : 2 : N-1]) let(p = TRUNK[i], d = TRUNK[i+1] - p)
            translate(p) rotate(atan2(d[1], d[0]) + 90) translate([-30, -2]) square([60, 4]);
    }
}
module leaf_ribs() { for (k = [0:len(LEAF_A)-1]) stroke(leaf_pts(k, 0.12, 0.85), [for (i = [0:N]) 3]); }

// ---------- sunset ----------
STRIPE_C = ["orange", "orange", "pink", "orange", "pink", "pink"];
module sun2d()     { intersection() { circle(r = R - 9); translate([-R, 2]) square([2*R, R]); } }
module stripe2d(i) { intersection() { circle(r = R - 9); translate([-R, -10 - i*22]) square([2*R, 13]); } }
module keep_clear() { offset(delta = 4) twin() palm2d(); }

// ---------- lettering + wolf ----------
module t305()    { translate([0, 86]) text("305",    size = 20, font = FONT, halign = "center", valign = "center"); }
module tgolden() { translate([0, 60]) text("GOLDEN", size = 18, font = FONT, halign = "center", valign = "center"); }
module twolves() { translate([0, 28]) text("WOLVES", size = 28, font = FONT, halign = "center", valign = "center"); }

WOLF_W = 140;  WOLF_Y = -64;     // traced from the clean logo: 2000 x 1892 canvas, centre (998, 946.5), 1940 wide
module wolf(name) { translate([0, WOLF_Y]) scale(WOLF_W / 1940) translate([-998, -946.5])
                        import(str("wolf_v2/wolf_", name, ".svg")); }

// ---------- the hanging disc ----------
module emblem() {
    col("black") slab(CORE) { circle(r = R); twin() palm2d(); }
    // layer 1: sunset and palm details
    col("yellow") lay(CORE/2, L) difference() { sun2d(); keep_clear(); }
    for (i = [0 : len(STRIPE_C)-1]) col(STRIPE_C[i]) lay(CORE/2, L) difference() { stripe2d(i); keep_clear(); }
    col("orange") lay(CORE/2, L) twin() trunk_rings();
    col("pink")   lay(CORE/2, L) twin() leaf_ribs();
    // layer 2: black lettering, outline behind GOLDEN, wolf silhouette with yellow outline
    col("black")  lay(CORE/2 + L, L) { t305(); twolves(); offset(r = 2.5) tgolden(); wolf("head"); }
    col("yellow") lay(CORE/2 + L, L) difference() { offset(r = 3.5) wolf("head"); wolf("head"); }
    // layer 3: GOLDEN fill and wolf colours
    col("yellow") lay(CORE/2 + 2*L, 1) { tgolden(); wolf("yellow"); }
    col("red")    lay(CORE/2 + 2*L, 1) wolf("red");
    col("white")  lay(CORE/2 + 2*L, 1) wolf("white");
}

// ---------- hockey-stick wall bracket ----------
SHAFT_L = 330;  SHAFT_H = 30;  SHAFT_T = 18;  BLADE_T = 12;
module blade2d() {
    polygon([[325, 15], [325, -15], [395, -15], [425, 0], [455, 60], [480, 140],
             [482, 170], [468, 178], [448, 168], [415, 110], [380, 40], [350, 15]]);
}
module heel_zone() { translate([300, -50]) square([300, 85]); }
module tape_zone() { translate([300, 35]) rotate(-12) square([300, 115]); }
module bracket() {
    col("black") difference() {                         // wall plate
        translate([-12, -30, -45]) cube([12, 60, 90]);
        for (z = [-30, 30]) translate([-13, 0, z]) rotate([0, 90, 0]) cylinder(d = 6, h = 20);
    }
    col("black")  slab(SHAFT_T) translate([0, -SHAFT_H/2]) square([SHAFT_L - 70, SHAFT_H]);
    col("yellow") slab(SHAFT_T) difference() { translate([SHAFT_L - 70, -SHAFT_H/2]) square([70, SHAFT_H]); blade2d(); }
    col("yellow") slab(BLADE_T) intersection() { blade2d(); heel_zone(); }
    col("black")  slab(BLADE_T) difference() { intersection() { blade2d(); tape_zone(); } heel_zone(); }
    col("yellow") slab(BLADE_T) difference() { blade2d(); heel_zone(); tape_zone(); }
    // BAUER on both sides
    col("yellow") {
        translate([0, -SHAFT_T/2, 0]) rotate([90, 0, 0]) linear_extrude(1) bauer();
        translate([135, 0, 0]) rotate([0, 0, 180]) translate([-135, -SHAFT_T/2, 0]) rotate([90, 0, 0]) linear_extrude(1) bauer();
    }
}
module bauer() { translate([135, 0]) text("BAUER", size = 19, font = FONT_ITAL, halign = "center", valign = "center"); }

// loops under the stick shaft (one per strap): a tab with a 28 x 5 mm slot the strap wraps through
module shaft_loop(x) {
    col("black") translate([0, 4, 0]) rotate([90, 0, 0]) linear_extrude(8) difference() {
        translate([x, -13]) offset(r = 4) offset(delta = -4) translate([-19, -26]) square([38, 28]);
        translate([x - 14, -33.5]) square([28, 5]);
    }
}


// ---------- split printing ----------
// half  = "full" | "front" | "back"  : cut down the middle (y = 0) so each half prints flat, detail up
// piece = "all"  | "sign"  | "stick" : the stick bracket and the sign are separate print items
// piece = "keys"                    : the printed alignment keys (print them on the front-halves plate)
// Alignment keys: each half has three 2.5 mm deep sockets in an uneven pattern - two round, one
// square - so the halves only fit together one way. The keys (8 mm, printed) sit in the sockets
// and lock the halves together while the glue sets.
half  = "full";
piece = "all";
KEY = 8;  KEY_CLR = 0.15;  KEY_DEPTH = 2.5;  KEY_H = 2*KEY_DEPTH - 0.4;
module key2d(sq, d) { if (sq) square(d, center = true); else circle(d = d, $fn = 48); }
module key_sockets(pts) {
    for (p = pts) translate([p[0], 0, p[1]]) rotate([90, 0, 0])
        linear_extrude(2*KEY_DEPTH, center = true) key2d(p[2], KEY + 2*KEY_CLR);
}
module keys() {       // 2 sets of 3 + 2 spares, lying so the front-half orientation stands them upright
    shapes = [0, 0, 1, 0, 0, 1, 0, 1];
    col("black") for (i = [0 : len(shapes) - 1])
        translate([i*14, 0, 0]) rotate([90, 0, 0]) linear_extrude(KEY_H) key2d(shapes[i], KEY);
}
module cut_half() {
    if (half == "front")     intersection() { children(); translate([-2000, -100, -2000]) cube([4000, 100, 4000]); }
    else if (half == "back") intersection() { children(); translate([-2000, 0, -2000]) cube([4000, 100, 4000]); }
    else children();
}

STICK_KEYS = [[60, 0, 0], [215, 2, 1], [372, -2, 0]];            // [x, z, square?]
DISC_KEYS  = [[-100, 40, 0], [100, 62, 1], [0, 110, 0]];          // relative to the disc centre, on the solid sun

// ---------- model ----------
// straps are real 1" (25 mm) webbing: through the loops under the shaft and the two slots in the disc
if (piece == "keys") keys();
if (piece == "all" || piece == "stick") cut_half() difference() {
    union() { bracket(); for (dx = [-SLOT_DX, SLOT_DX]) shaft_loop(EX + dx); }
    if (half != "full") key_sockets(STICK_KEYS);
}
if (piece == "all" || piece == "sign") cut_half() translate([EX, 0, EZ]) difference() {
    emblem();
    for (dx = [-SLOT_DX, SLOT_DX]) translate([dx - SLOT_W/2, -50, SLOT_Z - SLOT_H/2]) cube([SLOT_W, 100, SLOT_H]);
    if (half != "full") key_sockets(DISC_KEYS);
}
