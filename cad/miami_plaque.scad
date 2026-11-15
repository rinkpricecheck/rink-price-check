// 305 Golden Wolves - Miami wall plaque (standalone).
// Striped sunset disc, palm tree and hockey stick, with "305 GOLDEN WOLVES"
// and the wolf head placed directly on the sunset (no shield border).
// Wall-mounted: details on the front only, two keyhole slots on the back.
//
// part = "all" for a coloured preview, or one colour for multicolour STL export:
//        black | yellow | orange | pink | red | white
// Needs the traced wolf files in ./wolf_v2/
//
// Units: mm.  X = across, Z = up, Y = thickness (front face at -Y).

part = "all";
$fn = 64;
FONT = "Liberation Sans:style=Bold";

C = [["black",[0.08,0.08,0.08]], ["yellow",[0.98,0.86,0.10]], ["orange",[0.97,0.55,0.12]],
     ["pink",[0.95,0.42,0.55]], ["red",[0.85,0.15,0.12]], ["white",[0.97,0.97,0.97]]];
function rgb(n) = [for (c = C) if (c[0] == n) c[1]][0];
module col(n) { if (part == "all") color(rgb(n)) children(); else if (part == n) children(); }

R    = 150;   // sunset disc radius
CORE = 8;     // core thickness
L    = 2;     // colour layer thickness

// ---------- layers ----------
module slab(t) { translate([0, t/2, 0]) rotate([90, 0, 0]) linear_extrude(t) children(); }
module lay(a, h) { translate([0, -a, 0]) rotate([90, 0, 0]) linear_extrude(h) children(); }

// ---------- curve helpers ----------
function bez(p0, p1, p2, t) = (1-t)*(1-t)*p0 + 2*(1-t)*t*p1 + t*t*p2;
module stroke(pts, ws) {
    for (i = [0 : len(pts) - 2]) hull() {
        translate(pts[i]) circle(d = ws[i]);
        translate(pts[i+1]) circle(d = ws[i+1]);
    }
}
N = 20;

// ---------- palm tree ----------
TRUNK   = [for (i = [0:N]) bez([100, -150], [175, 0], [70, 142], i/N)];
TRUNK_W = [for (i = [0:N]) 28 - 12*i/N];
TOP     = [70, 148];
LEAF_A  = [172, 140, 108, 76, 45, 15, -12];
LEAF_L  = [115, 118, 100, 100, 122, 118, 95];
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

// ---------- hockey stick (handle top-left, blade bottom-right) ----------
module shaft2d() { stroke([[-195, -20], [92, -150]], [22, 22]); }
module blade2d() { stroke([[86, -140], [120, -158], [210, -158]], [24, 26, 26]); }
module stick2d() { shaft2d(); blade2d(); }
module shaft_fill() { difference() { offset(delta = -4) shaft2d(); translate([-215, -45]) rotate(-24) square([45, 60]); } }
module blade_tape() { intersection() { offset(delta = -4) blade2d();
                                       for (x = [128 : 12 : 200]) translate([x, -180]) square([5, 50]); } }

// ---------- sunset ----------
STRIPE_C = ["orange", "orange", "pink", "orange", "pink", "pink"];
module sun2d()     { intersection() { circle(r = R - 9); translate([-R, 2]) square([2*R, R]); } }
module stripe2d(i) { intersection() { circle(r = R - 9); translate([-R, -10 - i*22]) square([2*R, 13]); } }
module keep_clear() { offset(delta = 4) palm2d(); offset(delta = 4) stick2d(); }

// ---------- lettering + wolf ----------
module t305()    { translate([0, 86]) text("305",    size = 20, font = FONT, halign = "center", valign = "center"); }
module tgolden() { translate([0, 60]) text("GOLDEN", size = 18, font = FONT, halign = "center", valign = "center"); }
module twolves() { translate([0, 28]) text("WOLVES", size = 28, font = FONT, halign = "center", valign = "center"); }

WOLF_W = 140;  WOLF_Y = -64;     // traced from the clean logo: 2000 x 1892 canvas, centre (998, 946.5), 1940 wide
module wolf(name) { translate([0, WOLF_Y]) scale(WOLF_W / 1940) translate([-998, -946.5])
                        import(str("wolf_v2/wolf_", name, ".svg")); }

// ---------- model ----------
// core
col("black") difference() {
    slab(CORE) { circle(r = R); palm2d(); stick2d(); }
    for (x = [-80, 80])                       // keyhole slots in the back
        translate([x, CORE/2 - 4, 70]) rotate([-90, 0, 0]) linear_extrude(5) {
            circle(d = 10); translate([-2.75, 0]) square([5.5, 14]); translate([0, 14]) circle(d = 5.5);
        }
}
// layer 1: sunset, palm and stick details
col("yellow") lay(CORE/2, L) difference() { sun2d(); keep_clear(); }
for (i = [0 : len(STRIPE_C)-1]) col(STRIPE_C[i]) lay(CORE/2, L) difference() { stripe2d(i); keep_clear(); }
col("orange") lay(CORE/2, L) trunk_rings();
col("pink")   lay(CORE/2, L) leaf_ribs();
col("orange") lay(CORE/2, L) { shaft_fill(); blade_tape(); }
// layer 2: black lettering, outline behind GOLDEN, wolf silhouette
col("black") lay(CORE/2 + L, L) { t305(); twolves(); offset(r = 2.5) tgolden(); wolf("head"); }
col("yellow") lay(CORE/2 + L, L) difference() { offset(r = 3.5) wolf("head"); wolf("head"); }   // outline so the head stands off the stripes
// layer 3: GOLDEN fill and wolf colours
col("yellow") lay(CORE/2 + 2*L, 1) { tgolden(); wolf("yellow"); }
col("red")    lay(CORE/2 + 2*L, 1) wolf("red");
col("white")  lay(CORE/2 + 2*L, 1) wolf("white");
