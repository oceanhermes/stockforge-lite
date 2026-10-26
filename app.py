import html
from io import BytesIO
import streamlit as st
from PIL import Image, UnidentifiedImageError
from core import (
    PRESETS, derive_preset, process_image, unique_filename,
    split_keywords, validate_metadata, render_csv, build_zip,
    CATEGORY_TECHNOLOGY,
)

st.set_page_config(page_title='StockForge Lite · Adobe Stock Prep', page_icon='🛠️', layout='wide')
# Design Read: local stock-illustration workbench, in a bright print-proofing
# language; ENERGY 2 / RHYTHM 2 / MOTION 1. Paper and ink establish the proof-sheet
# feel, terracotta marks the primary action, and serif headings echo print labels.
st.markdown('''<style>
:root {
    color-scheme: light;
    --paper: #f2efe7;
    --sheet: #fbfaf6;
    --ink: #252821;
    --muted: #5b6056;
    --line: #d6d1c5;
    --wash: #e9e5db;
    --accent: #98432f;
    --accent-hover: #793522;
}
.stApp, [data-testid="stAppViewContainer"] {background:var(--paper); color:var(--ink);}
[data-testid="stHeader"] {background:var(--paper); border-bottom:1px solid var(--line);}
[data-testid="stHeader"] button {color:var(--ink) !important;}
[data-testid="stHeader"] button svg {color:var(--ink) !important; fill:currentColor;}
[data-testid="stHeader"] button svg path {stroke:var(--ink) !important;}
button[data-testid="stExpandSidebarButton"], button[data-testid="stCollapseSidebarButton"] {color:var(--ink) !important;}
button[data-testid="stExpandSidebarButton"] svg path, button[data-testid="stCollapseSidebarButton"] svg path {stroke:var(--ink) !important;}
[data-testid="stAppViewContainer"] p, [data-testid="stAppViewContainer"] label {color:var(--ink);}
[data-testid="stCaptionContainer"] {color:var(--muted) !important;}
.block-container {max-width:1280px; padding:4rem 2.6rem 3.5rem;}
[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3 {
    color:var(--ink); font-family:Georgia, 'Times New Roman', serif !important;
    font-weight:500 !important; letter-spacing:-0.035em !important;
}
[data-testid="stAppViewContainer"] h1 {font-size:clamp(2.5rem, 5vw, 4.3rem) !important; line-height:1.02 !important;}
[data-testid="stAppViewContainer"] h2 {font-size:2rem !important;}
[data-testid="stSidebar"] {background:var(--wash); border-right:1px solid var(--line);}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label {color:var(--ink);}
.sidebar-note {background:var(--sheet); border-left:2px solid var(--accent); padding:.8rem .9rem; color:var(--muted); font-size:.86rem; line-height:1.55;}
.sidebar-note strong {display:block; color:var(--ink); font-size:.7rem; letter-spacing:.06em; margin-bottom:.3rem;}
.masthead {display:flex; justify-content:space-between; align-items:center; gap:1rem; padding:.55rem 0 1rem; margin-bottom:2.1rem; border-bottom:1px solid var(--line); color:var(--muted); font-size:.72rem; letter-spacing:.08em;}
.masthead strong {color:var(--ink); font-weight:700;}
.intro {max-width:780px; margin-bottom:2rem;}
.intro p {font-size:1.08rem; line-height:1.65; color:#4f544b !important; margin:.25rem 0 0;}
.section-label {display:flex; align-items:baseline; gap:.85rem; padding:.8rem 0 .65rem; margin-top:1.4rem; border-top:1px solid var(--line);}
.section-label span {font-size:.72rem; color:var(--accent); font-weight:700; letter-spacing:.08em;}
.section-label strong {font-size:1.05rem; color:var(--ink); font-weight:600;}
[data-testid="stFileUploader"] {padding:.45rem; border:1px solid var(--line); border-radius:8px; background:var(--sheet);}
[data-testid="stFileUploaderDropzone"] {background:#f6f3ec; border:1px dashed #aaa495; border-radius:5px;}
[data-testid="stFileUploaderDropzone"] * {color:var(--ink) !important;}
[data-testid="stFileUploaderDropzone"] button {border:1px solid var(--line); background:var(--sheet); color:var(--ink) !important;}
[data-testid="stFileUploaderDropzone"] button:hover {border-color:var(--accent); color:var(--accent) !important;}
[data-testid="stFileUploader"] small {color:var(--muted) !important;}
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background:var(--sheet); border-color:#c9c4b8; color:var(--ink); border-radius:5px;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div {background:var(--sheet) !important; border:1px solid var(--line) !important; color:var(--ink) !important; box-shadow:none !important;}
[data-testid="stSidebar"] [data-baseweb="select"] * {color:var(--ink) !important;}
[data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus {border-color:var(--accent); box-shadow:0 0 0 1px var(--accent);}
button[kind="primary"] {background:var(--accent); border:1px solid var(--accent); border-radius:5px; color:#fff; font-weight:650;}
button[kind="primary"]:hover {background:var(--accent-hover); border-color:var(--accent-hover); color:#fff;}
button[kind="secondary"] {border-color:#bdb7aa; border-radius:5px; color:var(--ink);}
button:focus-visible, a:focus-visible, input:focus-visible, textarea:focus-visible {outline:3px solid #98432f !important; outline-offset:2px !important;}
[data-testid="stMetric"] {background:transparent; border:0; border-top:2px solid var(--ink); border-radius:0; padding:.8rem .1rem;}
[data-testid="stMetricLabel"], [data-testid="stMetricValue"] {color:var(--ink) !important;}
[data-testid="stImage"] img {border:1px solid var(--line); background:var(--sheet); padding:5px;}
[data-testid="stExpander"] {background:var(--sheet); border:1px solid var(--line); border-radius:6px;}
[data-testid="stExpander"] summary {color:var(--ink);}
hr {border-color:var(--line) !important;}
.empty-guide {display:grid; grid-template-columns:1.1fr .9fr; gap:2.5rem; padding:1.5rem 0 0;}
.guide-title {font-family:Georgia, 'Times New Roman', serif; font-size:1.35rem; color:var(--ink); margin:0 0 .9rem;}
.guide-steps {display:grid; grid-template-columns:1fr 1fr; gap:0 1.5rem;}
.guide-step {display:flex; gap:.75rem; align-items:baseline; padding:.65rem 0; border-top:1px solid var(--line); color:#42473f; font-size:.92rem; line-height:1.45;}
.guide-step span {color:var(--accent); font-size:.72rem; font-weight:700; letter-spacing:.04em;}
.guide-note {border-left:2px solid var(--accent); padding:.1rem 0 .1rem 1.1rem; color:var(--muted); font-size:.9rem; line-height:1.65; align-self:center;}
.guide-note strong {display:block; color:var(--ink); font-size:.76rem; letter-spacing:.07em; margin-bottom:.35rem;}
.footerhint {font-size:.78rem; color:var(--muted); margin-top:2.5rem; padding-top:1rem; border-top:1px solid var(--line);}
@media (max-width:760px) {
    .block-container {padding:4rem 1rem 2rem;}
    .masthead {margin-bottom:1.4rem; font-size:.64rem;}
    .intro {margin-bottom:1.4rem;}
    .intro p {font-size:1rem;}
    .empty-guide {grid-template-columns:1fr; gap:1rem;}
    .guide-steps {grid-template-columns:1fr;}
    .guide-note {margin-top:.5rem;}
}
</style>''', unsafe_allow_html=True)

st.markdown('<div class="masthead"><span><strong>STOCKFORGE</strong> &nbsp; / &nbsp; IMAGE PREP</span><span>PEMROSESAN LOKAL</span></div>', unsafe_allow_html=True)
st.title('StockForge Lite')
st.markdown('<div class="intro"><p>Siapkan ilustrasi stock dalam satu alur: perbesar, jaga transparansi, lalu rapikan metadata sebelum ekspor.</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header('Pengaturan')
    target = st.selectbox('Target minimum resolusi', [6.3, 4.2, 9.0, 12.0], index=0,
        format_func=lambda n: f'{n:g} MP')
    sharpen = st.toggle('Sharpen ringan setelah upscale', value=False,
        help='Bisa memunculkan halo di tepi ilustrasi. Selalu periksa pada 100%.')
    st.markdown('<div class="sidebar-note"><strong>METODE UPSCALE</strong>Memakai Pillow Lanczos pada CPU. Proses ini memperbesar ukuran, tetapi tidak menciptakan detail baru.</div>', unsafe_allow_html=True)
    st.markdown('**Catatan Adobe Stock**')
    st.caption('PNG wajib benar-benar transparan. JPEG digunakan bila gambar tidak transparan. 4–100 MP, maks. 45 MB. CSV tidak menyimpan checkbox Generative AI.')

st.markdown('<div class="section-label"><span>01</span><strong>Tambahkan ilustrasi</strong></div>', unsafe_allow_html=True)
uploads = st.file_uploader('Tarik PNG, JPEG, atau WebP ke sini. Bisa pilih beberapa file sekaligus.', type=['png','jpg','jpeg','webp'], accept_multiple_files=True)
if not uploads:
    st.markdown('''<div class="empty-guide">
<div><p class="guide-title">Dari file mentah ke paket siap ditinjau</p><div class="guide-steps">
<div class="guide-step"><span>01</span> Masukkan gambar yang ingin diproses.</div>
<div class="guide-step"><span>02</span> Pilih konsep dan periksa tiap preview.</div>
<div class="guide-step"><span>03</span> Sesuaikan judul serta urutan keyword.</div>
<div class="guide-step"><span>04</span> Proses batch, lalu unduh gambar dan CSV.</div>
</div></div>
<div class="guide-note"><strong>CATATAN METADATA</strong>Judul dan keyword dimulai dari preset berdasarkan nama file. Semuanya bisa diedit dan bukan hasil analisis visual otomatis.</div>
</div>''', unsafe_allow_html=True)
    st.stop()

uploaded = [(f.name, f.getvalue()) for f in uploads]
st.markdown(f'<div class="section-label"><span>02</span><strong>Periksa metadata</strong></div><p class="intro">{len(uploaded)} file diterima. Periksa preview dan sesuaikan metadata sebelum memproses batch.</p>', unsafe_allow_html=True)

with st.form('batch'):
    entries = []
    for idx, (filename, data) in enumerate(uploaded):
        st.divider()
        left, right = st.columns([1, 2.25], gap='large')
        with left:
            try:
                thumb = Image.open(BytesIO(data))
                st.image(thumb, caption=filename, use_container_width=True)
                st.caption(f'Input: {thumb.width} × {thumb.height} · {len(data)/1024/1024:.2f} MB')
            except (UnidentifiedImageError, OSError):
                st.error(f'Tidak bisa membaca {filename}')
        with right:
            suggested = derive_preset(filename)
            topic = st.selectbox('Preset / konsep gambar', list(PRESETS),
                index=list(PRESETS).index(suggested), key=f'topic-{idx}')
            data_preset = PRESETS[topic]
            title = st.text_input('Title (English, max 70 karakter)', value=data_preset['title'],
                key=f'title-{idx}', max_chars=70)
            keywords = st.text_area('Keywords (pisahkan dengan koma, urutkan dari terpenting)',
                value=data_preset['keywords'], key=f'keywords-{idx}', height=125)
            st.caption('Category: Technology (19) · Content type: Illustrations · AI label wajib dicentang manual di portal')
            entries.append(dict(filename=filename, data=data, topic=topic, title=title.strip(), keywords=keywords))
    go = st.form_submit_button('⚡ Process & Pack', type='primary', use_container_width=True)

if go:
    output_items = []
    csv_rows = []
    occupied = set()
    problems = []
    for entry in entries:
        try:
            result = process_image(entry['data'], target_mp=target, sharpen=sharpen)
            outfile = unique_filename(PRESETS[entry['topic']]['slug'], result['ext'], occupied)
            errors = validate_metadata(outfile, entry['title'], entry['keywords'])
            if errors:
                problems.append(entry['filename'] + ': ' + '; '.join(errors))
                continue
            keywords = ', '.join(split_keywords(entry['keywords']))
            output_items.append({**result, 'filename': outfile, 'source_filename': entry['filename'],
                'title': entry['title'], 'keywords': keywords})
            csv_rows.append({'Filename': outfile, 'Title': entry['title'], 'Keywords': keywords,
                'Category': CATEGORY_TECHNOLOGY, 'Releases': ''})
        except (UnidentifiedImageError, OSError, ValueError, MemoryError) as exc:
            problems.append(entry['filename'] + ': ' + str(exc))
    if problems:
        for p in problems: st.error(p)
    if output_items:
        try:
            csv_bytes = render_csv(csv_rows)
            archive = build_zip(output_items, csv_bytes)
            st.session_state['result'] = (archive, csv_bytes, output_items)
        except ValueError as exc:
            st.error(str(exc))

if 'result' in st.session_state:
    archive, csv_bytes, items = st.session_state['result']
    st.divider()
    st.subheader('📦 Output siap diunduh')
    col1, col2, col3 = st.columns(3)
    col1.metric('File diproses', len(items))
    col2.metric('Minimal resolusi', f'{min(i["mp"] for i in items):.2f} MP')
    col3.metric('PNG transparan', sum(bool(i['transparent']) for i in items))
    st.download_button('⬇️ Download ZIP (gambar + CSV + catatan)', archive,
        file_name='stockforge_export.zip', mime='application/zip', type='primary', use_container_width=True)
    st.download_button('Download CSV saja', csv_bytes, file_name='adobe_metadata.csv', mime='text/csv')
    for row in items:
        with st.expander(f'{row["filename"]} · {row["dimensions"][0]}×{row["dimensions"][1]} · {row["mp"]:.2f} MP'):
            st.write(f'Format: {row["ext"].upper()} · Transparansi: {"Ya" if row["transparent"] else "Tidak"} · Ukuran: {row["size_bytes"]/1024/1024:.2f} MB')
            st.write('Title:', row['title'])
            st.write('Keywords:', row['keywords'])
            st.download_button('Download gambar ini', row['bytes'], file_name=row['filename'],
                mime='image/png' if row['transparent'] else 'image/jpeg', key='dl'+row['filename'])
            if row['warnings']:
                for warning in row['warnings']:
                    st.warning(warning)
            else:
                st.success('Ukuran file, megapiksel dan format teknis memenuhi pengecekan dasar aplikasi.')
    st.warning('Hasil resize tidak dijamin lolos Adobe. Periksa detail gambar pada zoom 100%, kepemilikan hak, duplikasi, logo, dan metadata. Checkbox Created using generative AI tools harus diisi manual. Syarat usia Contributor Adobe Stock adalah minimal 18 tahun.')

st.markdown('<div class="footerhint">StockForge Lite · Offline, tanpa API key dan tanpa mengirim gambarmu ke server eksternal. Tidak berafiliasi dengan Adobe.</div>', unsafe_allow_html=True)
