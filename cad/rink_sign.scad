// Rink locker-room sign: hockey-stick bracket + hanging team shield + side flag
// Double-sided: every face detail is mirrored so the BACK reads exactly like the FRONT.
// Units: mm.  X = along the stick, Z = up, Y = thickness (front face at -Y).
//
// part = "all"    -> colored preview of the whole thing
// part = "yellow" | "black" | "cream" | "red" | "white" | "blue" | "grey"
//        -> just that color, for multicolor 3D printing (export each as STL)

part = "all";
$fn = 64;

FONT      = "Liberation Sans:style=Bold";
FONT_ITAL = "Liberation Sans:style=Bold Italic";

// ---------- colors ----------
C = [["yellow",[0.98,0.86,0.10]], ["black",[0.08,0.08,0.08]], ["cream",[0.93,0.90,0.82]],
     ["red",[0.85,0.15,0.12]], ["white",[0.97,0.97,0.97]], ["blue",[0.10,0.35,0.85]],
     ["grey",[0.62,0.64,0.68]]];
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
// 3. SIDE FLAG (BREAKERS-style banner)  -- separate wall-mounted piece
// =====================================================================
FX = 560;           // flag rod starts here (its own wall plate)
FLAG_W = 160;  FLAG_H = 230;  FLAG_T = 3;  FLAG_TOP = -70;
FCX = FX + 25 + FLAG_W/2;  FCY = FLAG_TOP - 110;

module emblem_ring()  { difference() { circle(r = 60); circle(r = 54); } }
module wave()         { difference() { circle(r = 52); translate([14, 20]) circle(r = 22); translate([-60, -60]) square([120, 30]); } }
module wave_curls()   { for (r = [28, 36, 44]) intersection() { circle(r = 51); difference() { translate([14, 20]) circle(r = r + 3);
                          translate([14, 20]) circle(r = r); translate([-80, -80]) square([160, 75]); } } }

module flag() {
    col("black") {
        translate([FX - 12, -25, FLAG_TOP - 25]) cube([12, 50, 60]);            // wall plate
        translate([FX, 0, FLAG_TOP + 6]) rotate([0, 90, 0]) cylinder(d = 12, h = FLAG_W + 40);  // rod
        translate([FX + 25, 0, FLAG_TOP + 6]) rotate([0, 90, 0]) cylinder(d = 18, h = FLAG_W); // sleeve
        slab(FLAG_T) translate([FX + 25, FLAG_TOP - FLAG_H]) square([FLAG_W, FLAG_H]);         // banner
        translate([FX + FLAG_W + 40, 0, FLAG_TOP + 6]) sphere(d = 14);           // rod end cap
    }
    // emblem on both sides
    col("grey")  face_layer(FLAG_T/2, 1,   FCX) translate([FCX, FCY]) emblem_ring();
    col("white") face_layer(FLAG_T/2, 1,   FCX) translate([FCX, FCY]) circle(r = 54);
    col("blue")  face_layer(FLAG_T/2 + 1, 1, FCX) translate([FCX, FCY]) wave();
    col("white") face_layer(FLAG_T/2 + 2, 0.8, FCX) translate([FCX, FCY]) wave_curls();
    col("white") face_layer(FLAG_T/2 + 1, 1.2, FCX)
        translate([FCX, FCY + 6]) text("PALM BEACH", size = 8, font = FONT, halign = "center", valign = "center");
    col("grey")  face_layer(FLAG_T/2 + 1, 1.5, FCX)
        translate([FCX, FCY - 12]) resize([150, 24]) text("BREAKERS", size = 22, font = FONT, halign = "center", valign = "center");
}

// =====================================================================
stick();
clips();
wolf_sign();
flag();
