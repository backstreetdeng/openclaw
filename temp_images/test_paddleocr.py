from paddleocr import PaddleOCR
import os
import json

os.environ['FLAGS_selected_devices'] = 'cpu'

ocr = PaddleOCR(lang='ch')

img_path = r'C:\Users\11489\.openclaw\workspace\temp_images\small_微信图片_20260424134130_153_109.jpg'

# Use predict instead of ocr (ocr is deprecated)
result = ocr.predict(img_path)

print('Result type:', type(result))
print('Result:', result)

# Try iterating
if hasattr(result, '__iter__') and not isinstance(result, (str, bytes)):
    result_list = list(result)
    print('\nAs list:')
    print('Length:', len(result_list))
    for i, item in enumerate(result_list[:5]):
        print(f'{i}: {item}')
