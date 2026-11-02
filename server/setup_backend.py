"""Fetch the exact original backend without its gigabytes of unrelated model chunks."""
import pathlib,urllib.request
ROOT=pathlib.Path(__file__).resolve().parent
COMMIT='99c43fd773a567a56212b2efdbc934b158215d48'
files=['__init__.py','background.py','clothing.py','compositing.py','config.py','detection.py','faceswap.py','idm_tryon.py','models.py','net.py','pipeline.py','tryon.py']
for name in ['coverswap/'+x for x in files]+['requirements.txt','chunker.py','scripts/download_models.py']:
 p=ROOT/'backend'/name;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_bytes(urllib.request.urlopen('https://raw.githubusercontent.com/atosonik/coverswap/'+COMMIT+'/'+name,timeout=60).read())
print('Original backend restored to',ROOT/'backend')
