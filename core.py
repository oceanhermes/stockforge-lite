"""Core image and metadata utilities for StockForge Lite.

Designed to run entirely on the user's machine without any cloud APIs.
"""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO, StringIO
from pathlib import Path
from math import sqrt, ceil
import csv
import json
import re
import zipfile

from PIL import Image, ImageCms, ImageFilter, ImageOps, UnidentifiedImageError

MAX_MP = 100
MIN_MP = 4
MAX_BYTES = 45 * 1024 * 1024
CATEGORY_TECHNOLOGY = '19'
CSV_HEADERS = ['Filename', 'Title', 'Keywords', 'Category', 'Releases']

# These are curated starting points, not image recognition or AI-written metadata.
PRESETS = {
    'Secure Login': {
        'slug': 'secure-login',
        'title': 'Secure Login with Laptop Shield and Padlock Illustration',
        'keywords': 'secure login, cybersecurity, laptop, authentication, password protection, data security, shield, padlock, account security, digital security, login interface, computer, privacy, online safety, access control, technology, illustration, security concept, digital protection, isolated, transparent background',
    },
    'Password Protection': {
        'slug': 'password-protect',
        'title': 'Password Protection with Lock and Secure Account Illustration',
        'keywords': 'password protection, cybersecurity, password, padlock, account security, secure access, data protection, authentication, shield, digital security, privacy, computer security, login, encryption, online safety, illustration, technology, isolated, transparent background',
    },
    'Phishing Warning': {
        'slug': 'phishing-warning',
        'title': 'Phishing Email Warning and Online Scam Protection Illustration',
        'keywords': 'phishing, phishing warning, email security, scam, cybersecurity, suspicious email, online fraud, warning, data protection, security alert, inbox, computer security, digital protection, cyber threat, illustration, online safety, technology, isolated, transparent background',
    },
    'Firewall Shield': {
        'slug': 'firewall-shield',
        'title': 'Firewall Shield and Network Security Protection Illustration',
        'keywords': 'firewall, network security, cybersecurity, shield, data protection, firewall protection, computer network, security system, cyber defense, digital security, intrusion prevention, secure network, illustration, technology, isolated, transparent background',
    },
    'Cloud Security': {
        'slug': 'cloud-security',
        'title': 'Cloud Security and Protected Online Data Storage Illustration',
        'keywords': 'cloud security, cloud computing, data protection, secure cloud, cybersecurity, cloud storage, encryption, padlock, data privacy, online backup, network security, digital security, technology, illustration, isolated, transparent background',
    },
    'Encrypted Data': {
        'slug': 'encrypted-data',
        'title': 'Encrypted Data Files and Secure Information Transfer Illustration',
        'keywords': 'data encryption, encrypted data, cybersecurity, data protection, secure transfer, privacy, information security, file security, padlock, digital security, encryption, computer network, technology, illustration, isolated, transparent background',
    },
    'Two-Factor Authentication': {
        'slug': 'two-factor-auth',
        'title': 'Two Factor Authentication on Smartphone Security Illustration',
        'keywords': 'two factor authentication, verification, smartphone, cybersecurity, authentication, secure login, mobile security, security code, digital security, account protection, identity verification, online safety, technology, illustration, isolated, transparent background',
    },
    'Cybersecurity Monitoring': {
        'slug': 'cyber-monitoring',
        'title': 'Cybersecurity Monitoring Dashboard and Threat Detection Illustration',
        'keywords': 'cybersecurity monitoring, threat detection, security dashboard, cyber threat, network monitoring, cybersecurity, computer security, analytics, security alert, system protection, digital security, dashboard, technology, illustration, isolated, transparent background',
    },
    'Safe Payment': {
        'slug': 'safe-payment',
        'title': 'Secure Digital Payment with Shield Protection Illustration',
        'keywords': 'secure payment, online payment, digital payment, payment security, cybersecurity, financial security, card payment, shield, transaction protection, ecommerce, digital wallet, privacy, online shopping, technology, illustration, isolated, transparent background',
    },
    'Identity Protection': {
        'slug': 'identity-protect',
        'title': 'Digital Identity Protection and Privacy Security Illustration',
        'keywords': 'identity protection, digital identity, cybersecurity, privacy protection, identity verification, personal data, secure account, shield, data privacy, authentication, computer security, digital security, technology, illustration, isolated, transparent background',
    },
    'Malware Detection': {
        'slug': 'malware-detect',
        'title': 'Malware Detection and Computer Virus Security Illustration',
        'keywords': 'malware detection, computer virus, cybersecurity, antivirus, cyber threat, malware, security scan, warning, computer protection, virus detection, digital security, security alert, technology, illustration, isolated, transparent background',
    },
    'Secure Server': {
        'slug': 'secure-server',
        'title': 'Secure Server Infrastructure and Data Center Protection Illustration',
        'keywords': 'secure server, server security, cybersecurity, data center, server protection, network security, data protection, infrastructure, encryption, shield, cloud computing, digital security, technology, illustration, isolated, transparent background',
    },
}


def derive_preset(filename: str) -> str:
    stem = Path(filename).stem.lower().replace('_', ' ').replace('-', ' ')
    for name, preset in PRESETS.items():
        needle = name.lower().replace('-', ' ')
        if needle in stem or preset['slug'].replace('-', ' ') in stem:
            return name
    words = set(stem.split())
    if {'login', 'laptop'} & words:
        return 'Secure Login'
    if 'password' in words:
        return 'Password Protection'
    if 'cloud' in words:
        return 'Cloud Security'
    if 'server' in words:
        return 'Secure Server'
    return 'Secure Login'


def slugify(raw: str) -> str:
    s = re.sub(r'[^a-z0-9]+', '-', raw.lower()).strip('-')
    return s or 'asset'


def unique_filename(slug: str, ext: str, occupied: set[str]) -> str:
    """Stay at or below Adobe CSV's documented 30-char filename guidance."""
    ext = ext.lower().lstrip('.')
    base = 'cyber-' + slugify(slug)
    for n in range(1, 1000):
        suffix = '' if n == 1 else f'-{n:02d}'
        cap = 30 - len(ext) - 1 - len(suffix)
        candidate = base[:cap].rstrip('-') + suffix + '.' + ext
        if candidate not in occupied:
            occupied.add(candidate)
            return candidate
    raise ValueError('Terlalu banyak nama file yang sama')


def split_keywords(raw: str) -> list[str]:
    out, seen = [], set()
    for part in raw.split(','):
        kw = ' '.join(part.strip().split())
        if kw and kw.casefold() not in seen:
            out.append(kw)
            seen.add(kw.casefold())
    return out


def validate_metadata(filename: str, title: str, keywords: str) -> list[str]:
    errors = []
    if len(filename) > 30:
        errors.append('Nama file lebih dari 30 karakter')
    if not title.strip() or len(title) > 70 or ',' in title:
        errors.append('Title harus 1–70 karakter dan tanpa koma')
    kws = split_keywords(keywords)
    if not 5 <= len(kws) <= 49:
        errors.append('Isi 5–49 keyword unik dan relevan')
    return errors


def read_image(payload: bytes) -> Image.Image:
    im = Image.open(BytesIO(payload))
    im.load()
    im = ImageOps.exif_transpose(im)
    # Preserve transparency if present; composite nothing behind the asset.
    if im.mode in ('P', 'PA') and 'transparency' in im.info:
        im = im.convert('RGBA')
    elif im.mode not in ('RGB', 'RGBA'):
        im = im.convert('RGBA' if 'A' in im.getbands() else 'RGB')
    return im


def has_transparency(img: Image.Image) -> bool:
    if 'A' not in img.getbands():
        return False
    return img.getchannel('A').getextrema()[0] < 255


def convert_to_srgb(im: Image.Image) -> tuple[Image.Image, bool]:
    """Convert an embedded source ICC when present, else assume its RGB is sRGB."""
    source_icc = im.info.get('icc_profile')
    had_source_profile = bool(source_icc)
    if not source_icc:
        return im, False
    try:
        src = ImageCms.ImageCmsProfile(BytesIO(source_icc))
        dst = ImageCms.createProfile('sRGB')
        if im.mode == 'RGBA':
            alpha = im.getchannel('A')
            rgb = ImageCms.profileToProfile(im.convert('RGB'), src, dst, outputMode='RGB')
            rgb.putalpha(alpha)
            return rgb, had_source_profile
        return ImageCms.profileToProfile(im, src, dst, outputMode='RGB'), had_source_profile
    except Exception:
        # Keep the original channels, but don't present this as a verified conversion.
        return im, False


def resize_image(im: Image.Image, target_mp: float, use_sharpen: bool) -> Image.Image:
    original_mp = im.width * im.height / 1_000_000
    if original_mp >= target_mp:
        return im.copy()
    factor = sqrt(target_mp / original_mp)
    new_size = ceil(im.width * factor), ceil(im.height * factor)
    resized = im.resize(new_size, Image.Resampling.LANCZOS)
    if use_sharpen:
        if resized.mode == 'RGBA':
            alpha = resized.getchannel('A')
            rgb = resized.convert('RGB').filter(ImageFilter.UnsharpMask(radius=1.1, percent=65, threshold=3))
            rgb.putalpha(alpha)
            return rgb
        return resized.filter(ImageFilter.UnsharpMask(radius=1.1, percent=65, threshold=3))
    return resized


def process_image(payload: bytes, target_mp: float, sharpen: bool):
    source = read_image(payload)
    source_size = source.size
    prepared, icc_converted = convert_to_srgb(source)
    transparent = has_transparency(prepared)
    resized = resize_image(prepared, target_mp, sharpen)
    ext = 'png' if transparent else 'jpg'
    srgb_profile = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    output = BytesIO()
    if transparent:
        resized.save(output, format='PNG', optimize=True, icc_profile=srgb_profile)
    else:
        resized.convert('RGB').save(output, format='JPEG', quality=95, optimize=True, subsampling=0, icc_profile=srgb_profile)
    result = output.getvalue()
    mp = resized.width * resized.height / 1_000_000
    checks = []
    if not MIN_MP <= mp <= MAX_MP:
        checks.append(f'Resolusi di luar 4–100 MP: {mp:.2f} MP')
    if len(result) > MAX_BYTES:
        checks.append(f'File melebihi 45 MB: {len(result)/1024/1024:.1f} MB')
    if not icc_converted:
        checks.append('Profil sumber tak terbukti sRGB; output diberi profil sRGB dengan asumsi warna RGB sumber benar')
    return {
        'bytes': result,
        'ext': ext,
        'original_size': source_size,
        'dimensions': resized.size,
        'mp': mp,
        'size_bytes': len(result),
        'transparent': transparent,
        'warnings': checks,
    }


def render_csv(rows: list[dict]) -> bytes:
    out = StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=CSV_HEADERS, lineterminator='\r\n')
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, '') for key in CSV_HEADERS})
    payload = out.getvalue().encode('utf-8-sig')
    if len(payload) > 1_000_000:
        raise ValueError('CSV melebihi 1MB')
    if len(rows) > 5000:
        raise ValueError('CSV melebihi 5000 baris')
    return payload


def build_zip(outputs: list[dict], csv_payload: bytes) -> bytes:
    result = BytesIO()
    with zipfile.ZipFile(result, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for item in outputs:
            z.writestr('images/' + item['filename'], item['bytes'])
        z.writestr('adobe_metadata.csv', csv_payload)
        z.writestr('README_UPLOAD.txt',
            'STOCKFORGE LITE - TAHAP PERSIAPAN\n\n'
            '1. Extract ZIP, upload file di folder images/ ke Adobe Stock (hanya jika memenuhi persyaratan Contributor).\n'
            '2. Uploaded Files > New > Upload CSV > pilih adobe_metadata.csv.\n'
            '3. Pastikan nama file dan CSV tepat sama, cek judul dan keyword.\n'
            '4. Atur Content Type menjadi Illustrations untuk ilustrasi AI, serta kategori dan release sesuai gambar.\n'
            '5. Centang Created using generative AI tools di Adobe; CSV TIDAK bisa mencentangnya.\n'
            '6. Cek ketajaman pada zoom 100%, tepi objek, artefak dan hak komersial.\n'
            '7. Resize Lanczos bukan AI super-resolution dan tidak menciptakan detail baru.\n'
            '8. Adobe Stock Contributor mensyaratkan pengguna minimal 18 tahun.\n'
            '9. Gunakan judul/keyword hanya yang benar-benar menggambarkan aset.\n')
        manifest = [{
            'filename': obj['filename'],
            'source_filename': obj['source_filename'],
            'title': obj['title'],
            'keywords': split_keywords(obj['keywords']),
            'category': CATEGORY_TECHNOLOGY,
            'created_using_generative_ai': True,
            'note': 'Centang AI secara manual di Adobe Stock Contributor; tidak termasuk dalam CSV.'
        } for obj in outputs]
        z.writestr('metadata_manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
    return result.getvalue()
