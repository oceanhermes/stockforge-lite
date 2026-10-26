from io import BytesIO
from zipfile import ZipFile
from PIL import Image
from core import process_image, unique_filename, split_keywords, render_csv, build_zip, validate_metadata


def test_rgba_keeps_transparency_and_profiles():
    img = Image.new('RGBA', (128,64), (50, 100, 220, 0))
    for x in range(32,96):
        for y in range(16,48):
            img.putpixel((x,y),(50,100,220,255))
    b = BytesIO(); img.save(b,format='PNG')
    output = process_image(b.getvalue(), 4.2, False)
    assert output['mp'] >= 4.2
    assert output['ext']=='png'
    outim = Image.open(BytesIO(output['bytes']))
    assert outim.getpixel((0,0))[3]==0
    assert outim.info['icc_profile']
    assert abs(outim.width / outim.height -2) <0.002


def test_opaque_jpg_and_csv_export():
    img = Image.new('RGB',(128,64),'white'); b = BytesIO(); img.save(b,format='PNG')
    output = process_image(b.getvalue(),4.2,False)
    assert output['ext']=='jpg'
    occupied = set()
    filename = unique_filename('secure-login','jpg',occupied)
    assert len(filename)<=30
    assert unique_filename('secure-login','jpg',occupied)!=filename
    title = 'Secure Login Illustration'
    keywords = 'secure login, cybersecurity, laptop, protection, padlock'
    assert not validate_metadata(filename,title,keywords)
    csv_data=render_csv([{'Filename':filename,'Title':title,'Keywords':keywords,'Category':'19','Releases':''}])
    assert b'Filename,Title,Keywords,Category,Releases' in csv_data
    archive=build_zip([{**output,'filename':filename,'source_filename':'input.png','title':title,'keywords':keywords}],csv_data)
    with ZipFile(BytesIO(archive)) as z:
        assert 'images/'+filename in z.namelist()
        assert 'adobe_metadata.csv' in z.namelist()


def test_keyword_uniqueness():
    assert split_keywords('laptop, Laptop, privacy, secure login') == ['laptop','privacy','secure login']
