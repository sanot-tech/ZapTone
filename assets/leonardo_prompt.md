🎨 Leonardo AI prompts for the ZapTone icon
═══════════════════════════════════════════════════════

The app icon: a film frame turning into a sound wave, with a small
lightning bolt. Made in pure vector geometry so it stays sharp at
every size from 16 px to 1024 px.

You do NOT have to use AI for this icon.
Our own SVG in assets/icon.svg is clean, sharp and already works.
Use these prompts only if you want to explore other looks.


───────────────────────────────────────────────────────
1️⃣  MAIN PROMPT  (copy this whole block)
───────────────────────────────────────────────────────

App icon design for a video-to-MP3 converter app called "ZapTone".
Flat vector logo, modern tech style, strictly geometric construction.

COMPOSITION:
- A rounded film frame in the centre, drawn with clean vector strokes.
- Inside the frame, a sound wave made of six rounded vertical bars,
  the tallest one exactly in the middle, like a real audio meter.
- A small sharp lightning bolt in the lower right corner, fully inside
  the frame, never touching the outline.
- Two thin audio arcs on the lower left, like speaker sound waves.
- Small film sprocket holes on the top and bottom edges of the frame.
- Deep space blue rounded square background, generous empty margins,
  the symbol fills about 70 percent of the canvas.

STYLE:
- Pure flat vector, crisp edges, correct geometry, mathematically
  clean curves, consistent 10 percent stroke weight.
- Two color gradient only: Plasma orange #FF8C42 melting into hot pink
  #FF5F8D. Dark plate #12141C. Off-white accents #E8ECF4.
- Very subtle glow behind the sound wave, one soft bloom only.
- Professional software icon, Swiss grid discipline, Bauhaus clarity,
  Swiss poster geometry, no decoration that carries no meaning.

QUALITY WORDS: sharp, balanced, iconic, memorable, scalable,
professional-grade, logo design, vector illustration.

SQUARE 1:1, centered, 1024x1024, flat design, no background scene.


───────────────────────────────────────────────────────
2️⃣  NEGATIVE PROMPT  (paste into the negative box)
───────────────────────────────────────────────────────

photograph, photorealistic, 3d render, glossy plastic, glassmorphism,
drop shadow on the background, skeuomorphic, bevel, emboss, metallic
chrome, lens flare, bokeh, glow everywhere, rainbow gradient,
purple pink cyan neon overload, wireframe mesh, hexagon grid pattern,
circuit board texture, holographic foil, text, letters, words, numbers,
watermark, signature, frame border, mockup on a device, hands, person,
busy background, cluttered composition, asymmetric off-center layout,
low contrast, muddy colors, blurry edges, jpeg artifacts, noise,
tiny details that disappear at 16 pixels, multiple icons in one image,
logo template with placeholder grid, stock photo watermark

WHY THIS LIST: most AI icons fail because they add texture, glow and
a scene. An app icon must survive being shrunk to 16 px in a taskbar.


───────────────────────────────────────────────────────
3️⃣  STYLE VARIANTS  (pick one, keep the composition)
───────────────────────────────────────────────────────

A. "PLASMA"
   Deep space blue plate, orange to pink gradient, subtle inner glow.
   Modern KDE Plasma feeling. Best choice for Linux and Flatpak.

B. "NEON ARCADE"
   Pure black plate, neon cyan to magenta gradient, thin neon strokes,
   strong outer glow on the wave only. Good for a dark taskbar.

C. "PAPER CUT"
   Off-white #F4F1EA plate, one flat orange shape, deep navy strokes,
   no gradient at all, hard cut shapes with paper thickness of 0.
   Works great printed on a T-shirt or in light themes.

D. "MONO LINE"
   Single white line on near-black, no fills, stroke only, 2 px lines.
   Smallest possible file, looks sharp everywhere. Safest fallback.


───────────────────────────────────────────────────────
4️⃣  MODEL AND SETTINGS
───────────────────────────────────────────────────────

- Model:              a vector or flat-design specialist model
                       (Phoenix or Lucid Realism for a flat look)
- Preset:             Vector Art / Flat Design / Logo Design
- Contrast:           high (we need clean separated shapes)
- Guidance scale:    6 to 8 (too high makes melted shapes)
- Number of images:   4 (pick the cleanest geometry)
- Alchemy:            on, if the model supports it
- Photoreal:          OFF, always
- Output:             1024x1024, PNG, transparent background OFF
                       (we want the rounded plate drawn by the icon)

Then: export at 1024, send it back, and we will auto-generate every
size (16, 22, 24, 32, 48, 64, 128, 256, 512, 1024) plus .ico and
.icns with scripts/make_icons.py.


───────────────────────────────────────────────────────
5️⃣  MANUAL CLEANUP CHECKLIST
───────────────────────────────────────────────────────

After you get the image, check these before using it:

☐  Do the six sound bars read clearly at 32 px? If not, delete extras.
☐  Is the lightning bolt fully inside the frame? It must not touch it.
☐  Are the corners of the plate rounded the same way on all sides?
☐  Is there any tiny text or fake lettering? Delete it, always.
☐  Does it still work if you make it pure black and white?
☐  Are there exactly two colors plus the dark plate? No more.
☐  No frame around the whole image (no outer border line).


───────────────────────────────────────────────────────
6️⃣  ALTERNATIVE IDEA (if the main one looks too generic)
───────────────────────────────────────────────────────

"Minimal pictogram: a single arrow zap turning into three concentric
sound rings. One continuous stroke, rounded line caps, no fills.
Inspired by Soviet constructivist posters and Swiss railway signage,
combined with modern sound app iconography. Two color gradient,
deep navy plate."