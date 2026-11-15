// Golden Wolves - Miami paw plaque (standalone).
// The plaque is a wolf paw: four toes with black claws above a big main pad,
// black outlines inside a white rim, yellow-to-orange fills (like the 305 paw logo).
// "Miami GOLDEN WOLVES" and the wolf head sit on the main pad.
// Wall-mounted: details on the front only, two keyhole slots on the back.
//
// part = "all" for a coloured preview, or one colour for multicolour STL export:
//        black | yellow | orange | red | white | miami (the Miami lettering)
// Needs the traced wolf files in ./wolf_v2/
//
// Units: mm.  X = across, Z = up, Y = thickness (front face at -Y).

part = "all";
$fn = 64;
FONT = "Liberation Sans:style=Bold";

C = [["black",[0.08,0.08,0.08]], ["yellow",[0.98,0.86,0.10]], ["orange",[0.97,0.55,0.12]],
     ["red",[0.85,0.15,0.12]], ["white",[0.97,0.97,0.97]],
     ["miami",[0.08,0.08,0.08]]];   // "miami" = the Miami lettering, black, exported as its own part
function rgb(n) = [for (c = C) if (c[0] == n) c[1]][0];
module col(n) { if (part == "all") color(rgb(n)) children(); else if (part == n) children(); }

CORE = 8;     // core thickness
L    = 2;     // colour layer thickness
EDGE = 14;    // black outer edge around the whole paw
RIM  = 9;     // white rim (EDGE - RIM = black edge width)
LINE = 3;     // black outline around each pad

module slab(t) { translate([0, t/2, 0]) rotate([90, 0, 0]) linear_extrude(t) children(); }
module lay(a, h) { translate([0, -a, 0]) rotate([90, 0, 0]) linear_extrude(h) children(); }

// ---------- paw shape ----------
module pad2d() {          // main pad: wide rounded top, two lobes at the bottom
    hull() {
        translate([-110, 40]) circle(r = 45);  translate([110, 40]) circle(r = 45);
        translate([0, 62])    circle(r = 58);
        translate([-68, -112]) circle(r = 60); translate([68, -112]) circle(r = 60);
    }
}
TOES = [[-145, 132, 24], [-52, 165, 8], [52, 165, -8], [145, 132, -24]];   // [x, y, tilt]
TOE_W = 66;  TOE_H = 86;
module toe(t) { translate([t[0], t[1]]) rotate(t[2]) scale([TOE_W/2, TOE_H/2]) circle(r = 1); }
module toes2d() { for (t = TOES) toe(t); }
module pads2d() { pad2d(); toes2d(); }
module joined(r) { offset(r = -22) offset(r = 22 + r) pads2d(); }   // one outline around the toes and pad

function bez(p0, p1, p2, t) = (1-t)*(1-t)*p0 + 2*(1-t)*t*p1 + t*t*p2;
module claw(t) {          // curved black claw growing out of the top of each toe
    N = 12;
    pts = [for (i = [0:N]) bez([0, TOE_H/2 - 6], [0, TOE_H/2 + 26], [t[2] < 0 ? 14 : -14, TOE_H/2 + 46], i/N)];
    translate([t[0], t[1]]) rotate(t[2])
        for (i = [0 : N-1]) hull() {
            translate(pts[i])   circle(d = 26 - 24*i/N);
            translate(pts[i+1]) circle(d = 26 - 24*(i+1)/N);
        }
}
module claws2d() { for (t = TOES) claw(t); }

// two-tone fill: yellow on top, orange on the bottom of each pad
module lower(y) { translate([-500, -500]) square([1000, 500 + y]); }
PAD_SPLIT = -8;           // main pad: orange below this line (behind the wolf)
module toe_lower(t) { translate([t[0], t[1]]) rotate(t[2]) translate([-50, -100]) square([100, 100 - 10]); }

// ---------- lettering + wolf ----------
module tmiami()  { translate([0, 86]) text("Miami",  size = 20, font = FONT, halign = "center", valign = "center"); }
module tgolden() { translate([0, 60]) text("GOLDEN", size = 18, font = FONT, halign = "center", valign = "center"); }
module twolves() { translate([0, 28]) text("WOLVES", size = 28, font = FONT, halign = "center", valign = "center"); }

WOLF_W = 140;  WOLF_Y = -64;     // traced from the clean logo: 2000 x 1892 canvas, centre (998, 946.5), 1940 wide
module wolf(name) { translate([0, WOLF_Y]) scale(WOLF_W / 1940) translate([-998, -946.5])
                        import(str("wolf_v2/wolf_", name, ".svg")); }

// ---------- model ----------
// core: the whole paw plus claws, black
col("black") difference() {
    slab(CORE) { joined(EDGE); claws2d(); }
    for (x = [-80, 80])                       // keyhole slots in the back
        translate([x, CORE/2 - 4, 40]) rotate([-90, 0, 0]) linear_extrude(5) {
            circle(d = 10); translate([-2.75, 0]) square([5.5, 14]); translate([0, 14]) circle(d = 5.5);
        }
}
// layer 1: white rim (and between the toes), pad fills
col("white")  lay(CORE/2, L) difference() {
    joined(RIM);
    offset(r = LINE) pad2d();  offset(r = LINE) toes2d();
    claws2d();
}
col("yellow") lay(CORE/2, L) {
    difference() { pad2d(); lower(PAD_SPLIT); }
    for (t = TOES) difference() { toe(t); toe_lower(t); }
}
col("orange") lay(CORE/2, L) {
    intersection() { pad2d(); lower(PAD_SPLIT); }
    for (t = TOES) intersection() { toe(t); toe_lower(t); }
}
// layer 2: black lettering, outline behind GOLDEN, wolf silhouette with yellow outline
col("black")  lay(CORE/2 + L, L) { twolves(); offset(r = 2.5) tgolden(); wolf("head"); }
col("miami")  lay(CORE/2 + L, L) tmiami();      // its own part so Bambu lists it separately
col("yellow") lay(CORE/2 + L, L) difference() { offset(r = 3.5) wolf("head"); wolf("head"); }
// layer 3: GOLDEN fill and wolf colours
col("yellow") lay(CORE/2 + 2*L, 1) { tgolden(); wolf("yellow"); }
col("red")    lay(CORE/2 + 2*L, 1) wolf("red");
col("white")  lay(CORE/2 + 2*L, 1) wolf("white");
