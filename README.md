# PDF 無損壓縮小工具

用 [pypdf](https://pypi.org/project/pypdf/) 對 PDF 做無損壓縮:只重新用 deflate 壓縮內部的 content streams(繪圖指令),完全不動圖片畫質或文字內容。壓縮率不會很誇張,但保證輸出跟原檔在視覺上完全一致。

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

# 實驗性:額外合併重複物件(字型/圖片/孤兒物件),壓縮率可以到 10-20%,但風險見下方警告
python compress_pdf.py input.pdf --dedup
```

## 效果說明

**預設模式**只重新壓縮 content stream,實際壓縮率依原始 PDF 而定:
- 文字/向量圖為主的檔案,效果通常比較明顯
- 圖片為主的檔案(例如產品 DM、掃描文件),content stream 占比很小,能省的空間很有限(通常只有個位數 %)

`--lossy` 模式會把內嵌圖片重新編碼成 JPEG,能大幅縮小圖片為主的檔案,但畫質會下降。工具會自動比較重新編碼後是否真的比較小,不會的話會保留原圖。

## ⚠️ `--dedup` 是實驗性功能,已確認會弄丟內容,先別用在正式文件上

`--dedup` 用 pypdf 的 `compress_identical_objects` 合併重複的字型/圖片/孤兒物件,壓縮率可以到 10-20%(比預設模式高很多),但這個 pypdf 功能有已知的 hash 誤判 bug。

實測時發現:對 `SMP-2400-two-outputs-tw.pdf` 用 `--dedup` 壓縮後,把輸出頁面實際渲染成圖片跟原檔比對,**第一頁裝置照片中間的「+」圖示整個消失了**——這代表誤判不只會發生在點陣圖片上,連向量繪製的圖層都可能被誤判成「沒被引用的孤兒物件」而砍掉。

工具原本有加一個保護:合併前後對每一張內嵌點陣圖片算 hash 比對,對不上就自動退回安全版本。**但這個「+」圖示不見的案例證明這個保護不夠**——因為那個圖示不是點陣圖片,驗證機制沒有涵蓋到,所以放過了一個實際上有問題的輸出。

結論:目前 `--dedup` 只適合拿來測試、實驗,**不要**用在需要保證內容完整的正式文件上。除非之後把驗證機制改成「整頁渲染成圖片再逐像素比對」這種更嚴格的方式,才能真正信任這個功能。
