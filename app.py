"""
PNG ↔ SVG Converter
────────────────────
SVG → PNG : sips (outil natif macOS)
PNG → SVG : potrace via subprocess (brew install potrace)
"""

import streamlit as st
import subprocess
import tempfile
import os
import io
import base64
from PIL import Image

st.set_page_config(page_title="PNG ↔ SVG Converter", page_icon="🔄", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.hero-title { font-family: 'Space Mono', monospace; font-size: 2.6rem; font-weight: 700;
    letter-spacing: -0.04em; color: #0f0f0f; margin-bottom: 0; line-height: 1.1; }
.hero-sub { font-size: 1.05rem; color: #6b7280; margin-top: 0.35rem; margin-bottom: 2rem; font-weight: 300; }
.badge { display: inline-block; color: #fff; font-family: 'Space Mono', monospace;
    font-size: 0.7rem; padding: 2px 8px; border-radius: 99px; letter-spacing: 0.04em;
    margin-right: 6px; vertical-align: middle; }
.badge-green { background: #16a34a; } .badge-blue { background: #2563eb; }
.card-title { font-family: 'Space Mono', monospace; font-size: 0.78rem; font-weight: 700;
    letter-spacing: 0.08em; text-transform: uppercase; color: #9ca3af; margin-bottom: 0.7rem; }
.divider { border: none; border-top: 1.5px solid #e5e7eb; margin: 1.5rem 0; }
.info-box { background: #eff6ff; border: 1.5px solid #bfdbfe; border-radius: 10px;
    padding: 0.75rem 1rem; font-size: 0.88rem; color: #1e40af; margin-bottom: 1rem; }
.err-box  { background: #fef2f2; border: 1.5px solid #fca5a5; border-radius: 10px;
    padding: 0.75rem 1rem; font-size: 0.88rem; color: #991b1b; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="hero-title">PNG ↔ SVG</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-sub">Convertisseur local · '
    '<span class="badge badge-green">PNG→SVG</span> potrace '
    '<span class="badge badge-blue">SVG→PNG</span> sips natif macOS</p>',
    unsafe_allow_html=True,
)

# ── Vérification potrace ────────────────────────────────────────────────────────
def check_tool(name):
    r = subprocess.run(["which", name], capture_output=True)
    return r.returncode == 0

potrace_ok = check_tool("potrace")
sips_ok    = check_tool("sips")

if not potrace_ok:
    st.markdown(
        '<div class="err-box">⚠️ <b>potrace</b> introuvable. '
        'Installez-le avec : <code>brew install potrace</code><br>'
        'La conversion PNG→SVG ne sera pas disponible avant installation.</div>',
        unsafe_allow_html=True,
    )

# ── Upload ─────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader("Déposez un fichier PNG ou SVG", type=["png", "svg"])

if not uploaded:
    st.markdown('<div class="info-box">📂 Chargez un fichier PNG ou SVG pour commencer.</div>', unsafe_allow_html=True)
    st.stop()

ext = uploaded.name.rsplit(".", 1)[-1].lower()
raw = uploaded.read()
size_kb = len(raw) / 1024

# ── Preview ────────────────────────────────────────────────────────────────────
st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown('<div class="card-title">📌 Fichier source</div>', unsafe_allow_html=True)

col_prev, col_info = st.columns([3, 2])
with col_prev:
    if ext == "png":
        st.image(Image.open(io.BytesIO(raw)), use_container_width=True)
    else:
        b64 = base64.b64encode(raw).decode()
        st.markdown(
            f'<img src="data:image/svg+xml;base64,{b64}" '
            f'style="width:100%;border-radius:8px;background:#fff">',
            unsafe_allow_html=True,
        )

with col_info:
    st.markdown(f"**Nom :** `{uploaded.name}`")
    st.markdown(f"**Format :** `{ext.upper()}`")
    st.markdown(f"**Taille :** `{size_kb:.1f} Ko`")
    if ext == "png":
        img_info = Image.open(io.BytesIO(raw))
        w, h = img_info.size
        st.markdown(f"**Dimensions :** `{w} × {h} px`")
        st.markdown(f"**Mode :** `{img_info.mode}`")

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PNG → SVG via potrace
# ══════════════════════════════════════════════════════════════════════════════
if ext == "png":
    st.markdown('<div class="card-title">⚙️ Options · PNG → SVG (potrace)</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        mode = st.selectbox(
            "Mode de vectorisation",
            ["Couleur (multi-calques)", "Niveaux de gris", "Noir & blanc"],
            help="Couleur = plusieurs passes avec seuillage. N&B = tracé direct.",
        )
        turdsize = st.slider(
            "Filtre bruit (turdsize)", 0, 20, 2,
            help="Supprime les petites taches. 0 = aucun filtrage.",
        )
    with col2:
        alphamax = st.slider(
            "Lissage des coins", 0.0, 1.33, 1.0, step=0.05,
            help="0 = coins nets, 1.33 = très arrondi.",
        )
        opttolerance = st.slider(
            "Tolérance courbes", 0.1, 2.0, 0.2, step=0.05,
            help="Précision du tracé des courbes de Bézier.",
        )

    st.markdown(
        '<div class="info-box">💡 <b>potrace</b> est le moteur de vectorisation de référence '
        '(utilisé par Inkscape). Aucune extension Python — appel direct au binaire.</div>',
        unsafe_allow_html=True,
    )

    btn_disabled = not potrace_ok
    if st.button("🔄 Convertir en SVG", use_container_width=True, type="primary", disabled=btn_disabled):
        with st.spinner("Vectorisation en cours…"):
            try:
                img_orig = Image.open(io.BytesIO(raw))

                if mode == "Noir & blanc":
                    # Conversion directe en bitmap 1-bit → potrace
                    layers = [img_orig.convert("L")]
                    thresholds = [128]
                elif mode == "Niveaux de gris":
                    gray = img_orig.convert("L")
                    layers = [gray, gray, gray]
                    thresholds = [85, 128, 200]
                else:  # Couleur
                    rgb = img_orig.convert("RGB")
                    r, g, b = rgb.split()
                    layers = [r, g, b]
                    thresholds = [128, 128, 128]

                svg_parts = []
                colors = ["#1a1a2e", "#16213e", "#0f3460"] if mode == "Couleur (multi-calques)" else ["#000000"] * 3

                for i, (layer, thresh, color) in enumerate(zip(layers, thresholds, colors)):
                    # Seuillage → image 1-bit
                    bw = layer.point(lambda p: 255 if p < thresh else 0, "1")

                    with tempfile.NamedTemporaryFile(suffix=".pbm", delete=False) as f_pbm:
                        bw.save(f_pbm.name)
                        pbm_path = f_pbm.name
                    svg_path = pbm_path.replace(".pbm", f"_{i}.svg")

                    result = subprocess.run([
                        "potrace",
                        pbm_path,
                        "--svg",
                        f"--turdsize={turdsize}",
                        f"--alphamax={alphamax:.2f}",
                        f"--opttolerance={opttolerance:.2f}",
                        "-o", svg_path,
                    ], capture_output=True)

                    os.unlink(pbm_path)

                    if result.returncode != 0:
                        st.error(f"Erreur potrace : {result.stderr.decode()}")
                        st.stop()

                    with open(svg_path, "r") as f:
                        svg_content = f.read()
                    os.unlink(svg_path)

                    # Extraire les chemins du SVG
                    import re
                    paths = re.findall(r'<path[^/]*/>', svg_content, re.DOTALL)
                    paths += re.findall(r'<path[^>]*>.*?</path>', svg_content, re.DOTALL)
                    for path in paths:
                        colored = re.sub(r'fill="[^"]*"', f'fill="{color}"', path)
                        if 'fill=' not in colored:
                            colored = colored.replace('<path', f'<path fill="{color}"')
                        svg_parts.append(colored)

                # Dimensions du SVG final
                w_orig, h_orig = img_orig.size
                svg_final = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w_orig}" height="{h_orig}" viewBox="0 0 {w_orig} {h_orig}">
  <rect width="100%" height="100%" fill="white"/>
  {''.join(svg_parts)}
</svg>'''

                svg_bytes = svg_final.encode("utf-8")

                st.success("✅ Vectorisation terminée !")
                b64_svg = base64.b64encode(svg_bytes).decode()
                st.markdown(
                    f'<img src="data:image/svg+xml;base64,{b64_svg}" '
                    f'style="width:100%;border-radius:8px;background:#fff;border:1.5px solid #e5e7eb">',
                    unsafe_allow_html=True,
                )
                out_name = uploaded.name.replace(".png", ".svg")
                st.download_button(
                    f"⬇️ Télécharger {out_name}", svg_bytes,
                    file_name=out_name, mime="image/svg+xml",
                    use_container_width=True,
                )
                st.caption(f"Taille SVG : {len(svg_bytes)/1024:.1f} Ko")

            except Exception as e:
                st.error(f"Erreur : {e}")

# ══════════════════════════════════════════════════════════════════════════════
# SVG → PNG via sips
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.markdown('<div class="card-title">⚙️ Options · SVG → PNG (sips natif macOS)</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        scale = st.select_slider("Facteur d'échelle", options=[1, 2, 3, 4], value=2,
            help="2 = retina, 4 = qualité print")
    with col2:
        bg_white = st.checkbox("Fond blanc (remplace transparence)", value=True)

    st.markdown(
        '<div class="info-box">💡 <b>sips</b> est intégré à macOS — rendu via Core Graphics, '
        'fidèle aux couleurs, textes et dégradés.</div>',
        unsafe_allow_html=True,
    )

    if st.button("🔄 Convertir en PNG", use_container_width=True, type="primary", disabled=not sips_ok):
        with st.spinner("Rendu en cours…"):
            try:
                with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
                    f.write(raw); tmp_svg = f.name
                tmp_png = tmp_svg.replace(".svg", ".png")

                result = subprocess.run(
                    ["sips", "-s", "format", "png", tmp_svg, "--out", tmp_png],
                    capture_output=True,
                )
                os.unlink(tmp_svg)

                if result.returncode != 0:
                    st.error(f"Erreur sips : {result.stderr.decode()}")
                    st.stop()

                img = Image.open(tmp_png).convert("RGBA")
                if scale > 1:
                    w2, h2 = img.size
                    img = img.resize((w2 * scale, h2 * scale), Image.LANCZOS)
                if bg_white:
                    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
                    img = Image.alpha_composite(bg, img).convert("RGB")

                os.unlink(tmp_png)

                buf = io.BytesIO()
                img.save(buf, format="PNG", optimize=True)
                png_bytes = buf.getvalue()

                st.success("✅ Rendu terminé !")
                st.image(png_bytes, use_container_width=True)

                out_name = uploaded.name.replace(".svg", ".png")
                st.download_button(
                    f"⬇️ Télécharger {out_name}", png_bytes,
                    file_name=out_name, mime="image/png",
                    use_container_width=True,
                )
                w3, h3 = img.size
                st.caption(f"Dimensions : {w3} × {h3} px — {len(png_bytes)/1024:.1f} Ko")

            except Exception as e:
                st.error(f"Erreur : {e}")

st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.caption("PNG→SVG via **potrace** (brew) · SVG→PNG via **sips** (macOS natif) · compatible Python 3.14")
