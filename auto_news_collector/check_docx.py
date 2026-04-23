"""
检查Word文档的字体设置 - 检查正文部分
"""
from docx import Document

doc = Document(r"E:\openclaw\workspace\auto_news_collector\output\汽车产业资讯简报_20260418-20260424_182206.docx")

print("检查正文段落:")
print("="*60)

found_content = False
for i, para in enumerate(doc.paragraphs):
    text = para.text.strip()
    # 找正文内容（比较长的段落）
    if text and len(text) > 50 and "时间" not in text and "来源" not in text and "http" not in text and "豪华品牌" not in text and "数据" not in text and "中国汽车" not in text and "2026年" not in text:
        found_content = True
        print(f"\n段落{i+1} (正文): {text[:60]}...")
        for run in para.runs:
            if run.text.strip():
                print(f"  Run字体: {run.font.name}")
                try:
                    rFonts = run.font.element.get_or_add_rPr().get_or_add_rFonts()
                    east_asia = rFonts.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}eastAsia")
                    print(f"  EastAsia字体: {east_asia}")
                except Exception as e:
                    print(f"  EastAsia检查失败: {e}")
                break
        if found_content and i > 20:
            break
