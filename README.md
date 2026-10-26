# StockForge Lite

**Live:** https://stockforge.conoisseur.xyz/  
Self-hosted Streamlit instance. Runs entirely on the host machine — uploaded images are
never sent to an external service.

**Tool lokal untuk menyiapkan gambar ilustrasi stock**: resize/upscale CPU dengan Pillow Lanczos, menjaga alpha PNG, memeriksa megapiksel/file size, dan menghasilkan metadata CSV untuk Adobe Stock.

> Aplikasi ini **bukan AI upscaler** dan metadata **bukan hasil image recognition**. Metadata awal disediakan lewat 12 preset cybersecurity, untuk direvisi sesuai gambar. Tidak ada API key, cloud model, atau koneksi Adobe.

## Jalankan di Windows 11

1. Ekstrak `stockforge-lite.zip`.
2. Pastikan Python 3.10 atau lebih baru tersedia di Windows dan `py` dikenali di Command Prompt.
3. Klik dua kali **setup.bat** satu kali (butuh internet untuk instalasi pustaka).
4. Klik dua kali **run.bat**. Browser akan membuka aplikasi Streamlit lokal (`http://localhost:8501`).
5. Upload PNG/JPG/WebP, pilih preset konsep, sesuaikan title/keywords.
6. Klik **Process & Pack**, lalu download ZIP. Isi ZIP:
    - `images/` — gambar PNG transparan/JPEG hasil resize, dengan profil output sRGB.
    - `adobe_metadata.csv` — 5 kolom resmi: `Filename,Title,Keywords,Category,Releases`.
    - `metadata_manifest.json` — catatan internal bahwa aset berasal dari AI.
    - `README_UPLOAD.txt` — instruksi umum.

## Batasan penting

- Resize menggunakan Lanczos, tidak memperbaiki detail yang hilang dari gambar asli.
- File transparan tetap PNG; gambar tanpa transparansi diekspor menjadi JPEG.
- Gambar dengan profil ICC sumber akan dikonversi ke sRGB jika memungkinkan. Untuk gambar tanpa ICC (atau ICC tidak valid) aplikasi mengasumsikan nilai RGB aslinya sRGB; warna sumber yang berbeda bisa bergeser.
- Ukuran target tidak dipaksakan jika gambar asli sudah lebih besar.
- Pilih dan perbaiki keyword agar benar-benar cocok dengan masing-masing gambar. Jika preset tidak pas, ganti teks manual.
- Kualitas visual, identitas, hak cipta, model/property releases, konten duplikat, dan kebijakan Adobe tidak dapat diverifikasi otomatis.
- **CSV Adobe tidak menyertakan flag Generative AI**. Tandai secara manual di portal.
- Adobe Stock Contributor mensyaratkan usia 18+. Portofolio dan metadata bisa dipersiapkan sebagai latihan sebelum memenuhi syarat.

## Format CSV yang dipakai

`Filename,Title,Keywords,Category,Releases`

Adobe menyebut batas CSV 1MB/5000 baris, nama file hingga 30 karakter, title hingga 70 karakter, 50 keyword maksimum. Aplikasi membatasi hingga 49 keyword agar kompatibel dengan label portal saat ini, dan menggunakan `Category=19` (Technology) untuk preset cybersecurity.

Sumber (diakses 2026-10-25):
- https://helpx.adobe.com/stock/contributor/manage-your-portfolio/csv-requirements-content.html
- https://helpx.adobe.com/stock/contributor/submit-your-content/submit-pngs/technical-requirements-png-submission.html
- https://helpx.adobe.com/stock/contributor/submit-your-content/submit-generative-ai-content/submit-generative-ai-content.html
- https://helpx.adobe.com/stock/contributor/manage-your-portfolio/upload-csv-file.html

## Untuk developer

```bash
python3 -m venv .venv
# Windows: .venv\Scripts\activate
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

### Run as a persistent service (Linux)

```bash
# systemd user unit, survives reboot, restarts on crash
systemctl --user enable --now stockforge.service
systemctl --user status stockforge.service
```

Public exposure goes through a dedicated cloudflared tunnel (`stockforge-tunnel.service`),
not a shared config — every hostname owns its own tunnel so one app cannot break another.

Logic utama ada di `core.py`; UI di `app.py`.
