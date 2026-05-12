const Tesseract = require('tesseract.js');
const fs = require('fs');
const path = require('path');

async function processImage(imagePath) {
    console.log('========================================');
    console.log('Processing:', imagePath);
    console.log('========================================');
    const result = await Tesseract.recognize(imagePath, 'eng+chi_sim', {
        logger: m => {
            if (m.status === 'recognizing text') {
                process.stdout.write(`\rProgress: ${(m.progress * 100).toFixed(1)}%`);
            }
        }
    });
    console.log('\n--- Extracted Text ---');
    console.log(result.data.text);
    console.log('--- End ---\n');
    return result.data.text;
}

// Use original images instead of small versions
const images = [
    'C:/Users/11489/.openclaw/workspace/temp_images/微信图片_20260424134130_153_109.jpg',
    'C:/Users/11489/.openclaw/workspace/temp_images/微信图片_20260424134130_154_109.jpg',
    'C:/Users/11489/.openclaw/workspace/temp_images/微信图片_20260424134419_156_109.jpg'
];

(async () => {
    for (const img of images) {
        if (fs.existsSync(img)) {
            await processImage(img);
        } else {
            console.log('File not found:', img);
        }
    }
    console.log('All images processed.');
})();