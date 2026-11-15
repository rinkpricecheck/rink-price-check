// Golden Wolves - Miami paw plaque (standalone), styled after the team's 305 paw logo:
// a bold black paw silhouette with a pointed top, white claws cut into the black,
// three yellow toes, a wide yellow main pad and a thin white outer edge.
// On the pad: the wolf head, big red "Miami" outlined in black (like the 305),
// and "GOLDEN WOLVES" underneath.
// Wall-mounted: details on the front only, two keyhole slots on the back.
//
// part = "all" for a coloured preview, or one colour for multicolour STL export:
//        black | yellow | red | white | miami (the red Miami lettering)
// Needs the traced wolf files in ./wolf_v2/
//
// Units: mm.  X = across, Z = up, Y = thickness (front face at -Y).

part = "all";
$fn = 64;
FONT = "Liberation Sans:style=Bold";

C = [["black",[0.08,0.08,0.08]], ["yellow",[0.98,0.73,0.06]], ["red",[0.86,0.07,0.10]],
     ["white",[0.97,0.97,0.97]],
     ["miami",[0.86,0.07,0.10]]];   // "miami" = the red Miami lettering, exported as its own part
function rgb(n) = [for (c = C) if (c[0] == n) c[1]][0];
module col(n) { if (part == "all") color(rgb(n)) children(); else if (part == n) children(); }

CORE = 8;     // core thickness
L    = 2;     // colour layer thickness
EDGE = 5;     // thin white outer edge

module slab(t) { translate([0, t/2, 0]) rotate([90, 0, 0]) linear_extrude(t) children(); }
module lay(a, h) { translate([0, -a, 0]) rotate([90, 0, 0]) linear_extrude(h) children(); }
function bez(p0, p1, p2, t) = (1-t)*(1-t)*p0 + 2*(1-t)*t*p1 + t*t*p2;
module stroke(pts, ws) {
    for (i = [0 : len(pts) - 2]) hull() {
        translate(pts[i]) circle(d = ws[i]);
        translate(pts[i+1]) circle(d = ws[i+1]);
    }
}

// ---------- paw ----------
module pad2d() {          // wide main pad: rounded shoulders, a hump on top, wavy bottom
    hull() {
        translate([-100, 22]) circle(r = 42);   translate([100, 22]) circle(r = 42);
        translate([-108, -45]) circle(r = 52);  translate([108, -45]) circle(r = 52);
        translate([-72, -118]) circle(r = 50);  translate([72, -118]) circle(r = 50);
        translate([0, -122])   circle(r = 50);
    }
    translate([0, 42]) scale([75, 32]) circle(r = 1);
}
TOES = [[-112, 142, 14, 78, 104], [0, 162, 0, 86, 112], [112, 142, -14, 78, 104]];   // [x, y, tilt, w, h]
module toe(t) { translate([t[0], t[1]]) rotate(t[2]) scale([t[3]/2, t[4]/2]) circle(r = 1); }
module toes2d() { for (t = TOES) toe(t); }
module pads2d() { pad2d(); toes2d(); }

// white claws: [base, control, tip, base width]
CLAWS = [[[0, 228], [0, 250], [0, 272], 34],
         [[-104, 206], [-108, 228], [-124, 250], 30], [[104, 206], [108, 228], [124, 250], 30],
         [[-168, 112], [-180, 134], [-196, 160], 28], [[168, 112], [180, 134], [196, 160], 28]];
module claw(c) { N = 10; stroke([for (i = [0:N]) bez(c[0], c[1], c[2], i/N)], [for (i = [0:N]) c[3]*(1 - i/N) + 2]); }
module claws2d() { for (c = CLAWS) claw(c); }

// the black silhouette: everything grown and smoothed into one blob, claw tips poking out like flames
module silhouette() { offset(r = -30) offset(r = 30) { offset(r = 26) pads2d(); offset(r = 15) claws2d(); } }

// ---------- lettering + wolf ----------
module tmiami()  { translate([0, -86]) text("Miami", size = 58, font = FONT, halign = "center", valign = "center"); }
module tgw()     { translate([0, -138]) text("GOLDEN WOLVES", size = 16, font = FONT, halign = "center", valign = "center"); }

WOLF_W = 124;  WOLF_Y = 12;      // traced from the clean logo: 2000 x 1892 canvas, centre (998, 946.5), 1940 wide
module wolf(name) { translate([0, WOLF_Y]) scale(WOLF_W / 1940) translate([-998, -946.5])
                        import(str("wolf_v2/wolf_", name, ".svg")); }

// ---------- model ----------
// core: the paw silhouette plus its thin edge, black
col("black") difference() {
    slab(CORE) offset(r = EDGE) silhouette();
    for (x = [-80, 80])                       // keyhole slots in the back
        translate([x, CORE/2 - 4, 40]) rotate([-90, 0, 0]) linear_extrude(5) {
            circle(d = 10); translate([-2.75, 0]) square([5.5, 14]); translate([0, 14]) circle(d = 5.5);
        }
}
// layer 1: white outer edge, white claws, yellow toes and pad
col("white")  lay(CORE/2, L) { difference() { offset(r = EDGE) silhouette(); silhouette(); } claws2d(); }
col("yellow") lay(CORE/2, L) pads2d();
// layer 2: black outline around Miami, black GOLDEN WOLVES, wolf with a black outline
col("black")  lay(CORE/2 + L, L) { offset(r = 4) tmiami(); tgw(); offset(r = 3) wolf("head"); }
// layer 3: red Miami and the wolf colours
col("miami")  lay(CORE/2 + 2*L, 1) tmiami();
col("yellow") lay(CORE/2 + 2*L, 1) wolf("yellow");
col("red")    lay(CORE/2 + 2*L, 1) wolf("red");
col("white")  lay(CORE/2 + 2*L, 1) wolf("white");
