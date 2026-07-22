# PDF 無損壓縮小工具

用 [pypdf](https://pypi.org/project/pypdf/) 對 PDF 做無損壓縮:重新用 deflate 壓縮內部的 content streams,並移除重複/未使用的物件(字型、圖片等)。完全不動圖片畫質或文字內容,壓縮前後頁數與文字逐一比對完全一致。

## 安裝

```bash
pip install -r requirements.txt
```

## Windows 快速使用

把要壓縮的 PDF 丟進這個資料夾,直接雙擊 `compress.bat` 就會自動壓縮資料夾內所有 *.pdf(第一次執行會自動安裝所需套件)。

## 用法

```bash
# 不加任何參數:把 PDF 直接丟進這個資料夾,執行後會自動抓資料夾裡的所有 *.pdf 逐一壓縮
# (已經是 *_compressed.pdf 的檔案會自動跳過,不會重複壓縮)
python compress_pdf.py

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
