# MCU_teaching

銘傳大學資訊管理學系　林漢洲　課程教材與教學工具。

教材成品透過 GitHub Pages 提供：

**<https://actuallife.github.io/MCU_teaching/>**

## 目前內容

| 課程 | 單元 | 內容 | 網址 |
| --- | --- | --- | --- |
| 統計學（一） | 第 5 章　離散機率分配 | 期中考複習網站：可重複測驗、自動批改、完整詳解 | [開啟](https://actuallife.github.io/MCU_teaching/statistics/ch5-discrete-distributions/) |

## 目錄結構

```
MCU_teaching/
├── docs/        ← GitHub Pages 的根目錄，放建置完成的成品
│   ├── index.html                                 教材總覽頁
│   └── <課程>/<單元>/index.html                    各單元成品
└── src/         ← 原始碼與題庫
    └── <課程>/<單元>/                              各單元的建置腳本與資料
```

成品與原始碼分開擺，好處是 GitHub Pages 只服務 `docs/`，
`src/` 裡的 Python 腳本與題庫資料不會被當成網頁公開路徑。

每個單元的詳細說明、建置方式與改題方法，看該單元 `src/` 目錄下的 `README.md`。

## 新增一個單元

1. 複製一份現有單元的 `src/<課程>/<單元>/` 資料夾，改成新名稱
2. 修改裡面的題庫與模板
3. 在該資料夾內執行 `python3 bank.py && python3 build.py`

建置腳本會依資料夾位置自動把成品輸出到對應的 `docs/<課程>/<單元>/`，
網址跟著目錄結構走，GitHub Pages 的設定不必再動。

最後記得把新單元加進本檔案的「目前內容」表格，以及 `docs/index.html` 的清單。

## Pages 設定

只需設定一次：**Settings → Pages → Deploy from a branch → 分支 `main`、資料夾 `/docs`**。

## 授權

程式碼可自由取用與修改。

題目內容與教材著作權屬作者。部分教材改編自原文教科書的範例架構，
如需在課堂以外的場合散布，請自行確認是否符合原出版社的授權範圍。
