import sys
sys.stdout.reconfigure(encoding='utf-8')

libs = ['PIL', 'Pillow', 'matplotlib', 'reportlab', 'img2pdf', 'pdf2image', 'pdfplumber', 'python-pptx', 'pywin32', 'comtypes']
for lib in libs:
    try:
        m = __import__(lib.replace('-', '_'))
        ver = getattr(m, '__version__', 'installed')
        print(f'{lib}: {ver}')
    except ImportError:
        print(f'{lib}: NOT installed')
