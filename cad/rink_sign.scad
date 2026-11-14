// Rink locker-room sign: hockey-stick bracket + hanging team shield
// Double-sided: every face detail is mirrored so the BACK reads exactly like the FRONT.
// Units: mm.  X = along the stick, Z = up, Y = thickness (front face at -Y).
//
// part = "all"    -> colored preview of the whole thing
// part = "yellow" | "black" | "cream" | "red" | "white"
//        -> just that color, for multicolor 3D printing (export each as STL)

part = "all";
$fn = 64;

FONT      = "Liberation Sans:style=Bold";
FONT_ITAL = "Liberation Sans:style=Bold Italic";

// ---------- colors ----------
C = [["yellow",[0.98,0.86,0.10]], ["black",[0.08,0.08,0.08]], ["cream",[0.93,0.90,0.82]],
     ["red",[0.85,0.15,0.12]], ["white",[0.97,0.97,0.97]]];
function rgb(n) = [for (c = C) if (c[0] == n) c[1]][0];
module col(n) { if (part == "all") color(rgb(n)) children(); else if (part == n) children(); }

// ---------- double-sided helpers ----------
// Put a 2D shape on the face plane y = -a (front), thickness h, and the same
// shape on the back (y = +a), rotated 180 deg about Z through x = cx so it
// reads correctly from behind.
module face_layer(a, h, cx) {
    translate([0, -a, 0]) rotate([90, 0, 0]) linear_extrude(h) children();
    translate([cx, 0, 0]) rotate([0, 0, 180]) translate([-cx, 0, 0])
        translate([0, -a, 0]) rotate([90, 0, 0]) linear_extrude(h) children();
}
// Solid slab centred on y=0 (core)
module slab(t) { translate([0, t/2, 0]) rotate([90, 0, 0]) linear_extrude(t) children(); }

// =====================================================================
// 1. HOCKEY-STICK BRACKET
// =====================================================================
SHAFT_L = 330;  SHAFT_H = 30;  SHAFT_T = 18;  BLADE_T = 12;

module blade2d() {
    polygon([[325, 15], [325, -15], [395, -15], [425, 0], [455, 60], [480, 140],
             [482, 170], [468, 178], [448, 168], [415, 110], [380, 40], [350, 15]]);
}
module stick() {
    // wall plate
    col("black") difference() {
        translate([-12, -30, -45]) cube([12, 60, 90]);
        for (z = [-30, 30]) translate([-13, 0, z]) rotate([0, 90, 0]) cylinder(d = 6, h = 20);
    }
    // shaft (black) + yellow hosel section
    col("black")  slab(SHAFT_T) translate([0, -SHAFT_H/2]) square([SHAFT_L - 70, SHAFT_H]);
    col("yellow") slab(SHAFT_T) difference() { translate([SHAFT_L - 70, -SHAFT_H/2]) square([70, SHAFT_H]); blade2d(); }
    // blade: yellow heel, black tape, yellow toe
    col("yellow") slab(BLADE_T) intersection() { blade2d(); translate([300, -50]) square([300, 85]); }
    col("black")  slab(BLADE_T) difference() { intersection() { blade2d(); translate([300, 35])  rotate(-12) square([300, 115]); }
                                                 translate([300, -50]) square([300, 85]); }
    col("yellow") slab(BLADE_T) difference()   { blade2d(); translate([300, -50]) square([300, 85]);
                                                 translate([300, 35]) rotate(-12) square([300, 115]); }
    // BAUER lettering, raised 1 mm, both sides
    col("yellow") face_layer(SHAFT_T/2, 1, 135)
        translate([135, 0]) text("BAUER", size = 19, font = FONT_ITAL, halign = "center", valign = "center");
}

// =====================================================================
// 2. HANGING SHIELD SIGN  (GOLDEN WOLVES)
// =====================================================================
SIGN_CX = 140;  SIGN_TOP = -62;  SIGN_W = 170;  SIGN_H = 240;
CORE_T = 6;  L = 2;   // core thickness, per-layer thickness

module pennant(inset = 0) {
    translate([SIGN_CX, SIGN_TOP]) offset(delta = -inset)
        polygon([[-SIGN_W/2, 0], [SIGN_W/2, 0], [SIGN_W/2, -SIGN_H + 60],
                 [0, -SIGN_H], [-SIGN_W/2, -SIGN_H + 60]]);
}

// Wolf head traced from the photo of the real sign (cad/wolf/*.svg, made with potrace).
// SVG canvas is 880 x 780 units; head centre is at (431, 379.5).  WOLF_W = finished width in mm.
WOLF_W = 112;
module wolf_layer(name) {
    scale(WOLF_W / 806) translate([-431, -379.5]) import(str("wolf/wolf_", name, ".svg"));
}

module wolf_sign() {
    WX = SIGN_CX;  WY = SIGN_TOP - 157;
    // core
    col("yellow") slab(CORE_T) pennant(0);
    // black border layer
    col("black")  face_layer(CORE_T/2, L, SIGN_CX) pennant(7);
    // cream panel
    col("cream")  face_layer(CORE_T/2 + L, L, SIGN_CX) pennant(13);
    // lettering
    col("yellow") face_layer(CORE_T/2 + 2*L, 1.5, SIGN_CX)
        translate([SIGN_CX, SIGN_TOP - 54]) text("GOLDEN", size = 15, font = FONT, halign = "center", valign = "center");
    col("black")  face_layer(CORE_T/2 + 2*L, 2, SIGN_CX)
        translate([SIGN_CX, SIGN_TOP - 30]) text("305", size = 18, font = FONT, halign = "center", valign = "center");
    col("black")  face_layer(CORE_T/2 + 2*L, 2, SIGN_CX)
        translate([SIGN_CX, SIGN_TOP - 84]) text("WOLVES", size = 24, font = FONT, halign = "center", valign = "center");
    // wolf head: black silhouette, yellow face on top, red mouth, white teeth
    col("black")  face_layer(CORE_T/2 + 2*L, 2, SIGN_CX) translate([WX, WY]) wolf_layer("head");
    col("yellow") face_layer(CORE_T/2 + 3*L, 1, SIGN_CX) translate([WX, WY]) wolf_layer("yellow");
    col("red")    face_layer(CORE_T/2 + 3*L, 1, SIGN_CX) translate([WX, WY]) wolf_layer("red");
    col("white")  face_layer(CORE_T/2 + 3*L, 1, SIGN_CX) translate([WX, WY]) wolf_layer("white");
}

// clips joining stick and sign
module clips() {
    for (x = [SIGN_CX - 40, SIGN_CX + 40]) col("black") {
        translate([x - 11, -8, SIGN_TOP - 6]) cube([22, 16, -SIGN_TOP - SHAFT_H/2 + 6]);
        translate([x - 13, -9, -SHAFT_H/2 - 22]) cube([26, 18, 10]);          // buckle
        translate([x - 11, 0, -SHAFT_H/2 - 4]) rotate([0, 90, 0]) cylinder(d = 8, h = 22); // hinge pin
    }
}

// =====================================================================
stick();
clips();
wolf_sign();
