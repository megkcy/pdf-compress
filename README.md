# PDF 無損壓縮小工具

用 [pypdf](https://pypi.org/project/pypdf/) 對 PDF 做無損壓縮:只重新用 deflate 壓縮內部的 content streams(繪圖指令),完全不動圖片畫質或文字內容。

> **注意**:早期版本有多加一個「移除重複物件」(`compress_identical_objects`)的步驟想再壓縮更多,但這個 pypdf 功能有已知的 hash 誤判 bug,可能把不同的圖片誤判成相同而合併錯誤,導致輸出的圖片跑掉。現在預設不會執行這一步,只保留確定無損的 content stream 壓縮;如果想要更高的壓縮率,可以用下面的 `--dedup`,會自動驗證安全性。

## 安裝

```bash
pip install -r requirements.txt
```

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

# 調整壓縮等級 0-9(預設 9,最大壓縮,只影響 content stream,不影響圖片)
python compress_pdf.py input.pdf --level 9

# 有損模式:連圖片也重新壓縮(會降畫質,但檔案可以小很多)
python compress_pdf.py input.pdf --lossy

# 有損模式 + 指定 JPEG 品質 1-100(預設 80,數字越小檔案越小、畫質越差)
python compress_pdf.py input.pdf --lossy --image-quality 60

# 去重複模式:合併重複的字型/圖片/移除孤兒物件,壓縮率明顯更高,仍然無損
python compress_pdf.py input.pdf --dedup
```

## 效果說明

**預設(無損)模式**只重新壓縮 content stream(頁面繪圖指令),完全不動圖片,實際壓縮率依原始 PDF 而定:
- 文字/向量圖為主的檔案,效果通常最明顯(範例測試約 45% 縮小)
- 圖片為主的檔案(例如產品 DM、掃描文件),content stream 占比很小,無損模式能省的空間很有限(通常只有個位數 %)

**`--dedup` 模式**額外合併文件裡真正重複的物件(同一張圖片/字型被內嵌多次、沒被引用到的孤兒物件),對圖片為主但內容有重複素材的檔案(例如多語言版型共用美編圖片)效果明顯(實測 SMP 產品 DM 約 14% 縮小),而且**仍然是無損**——工具會在合併前後對每一張圖片算 hash 指紋比對,只要有任何一張對不上,就會自動捨棄合併結果、改用安全的無 dedup 版本輸出,並印出警告,不會讓你收到跑掉圖片的檔案。

**`--lossy` 模式**會把內嵌圖片重新編碼成 JPEG,能大幅縮小圖片為主的檔案,但畫質會下降。工具會自動比較重新編碼後是否真的比較小,不會的話會保留原圖(所以有些圖片可能沒被壓到,這是正常的)。`--dedup` 和 `--lossy` 可以一起用。
