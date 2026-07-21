# PDF 無損壓縮小工具

用 [pypdf](https://pypi.org/project/pypdf/) 對 PDF 做無損壓縮:重新用 deflate 壓縮內部的 content streams,並移除重複/未使用的物件(字型、圖片等)。完全不動圖片畫質或文字內容,壓縮前後頁數與文字逐一比對完全一致。

## 安裝

```bash
pip install -r requirements.txt
```

## 用法

```bash
# 單一檔案,預設輸出 input_compressed.pdf
python compress_pdf.py input.pdf

# 指定輸出檔名
python compress_pdf.py input.pdf output.pdf

# 整批處理資料夾,每個檔案旁邊產生 _compressed 版本
python compress_pdf.py 資料夾/

# 整批處理資料夾,鏡射資料夾結構到輸出資料夾
python compress_pdf.py 資料夾/ 輸出資料夾/

# 直接覆蓋原檔(小心使用)
python compress_pdf.py input.pdf --in-place

# 調整壓縮等級 0-9(預設 9,最大壓縮)
python compress_pdf.py input.pdf --level 9
```

## 效果說明

實際壓縮率依原始 PDF 而定:
- 文字/向量圖為主的檔案,效果通常最明顯(範例測試約 45% 縮小)
- 本來就是掃描圖片為主、或已經壓縮過的檔案,效果會比較有限
