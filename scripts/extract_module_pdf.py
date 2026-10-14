#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_module_pdf.py — 从模组 PDF 里抽出「文本」和「地图图片」，供后续整理成数据包。

用法:
    python extract_module_pdf.py <module.pdf> [-o 输出目录]

产出（默认写到 <pdf名>_extract/）:
    pages.txt     —— 每页文本，带 `===== PAGE n =====` 分隔，便于 grep 定位章节
    maps/pXX_0.png —— 每页内嵌的图片（地图多半是整页大图）
    toc.txt       —— PDF 的目录（如果 PDF 带书签，直接给你章节页码）

提示:
    * 中译 PDF 常有全角/兼容字形（⼤ ⼀ ⻔ …）。整理数据时用
      unicodedata.normalize('NFKC', text) 归一化。
    * 地图页通常“整页只有一张大图、几乎没有文字”，可用图片尺寸辅助判断。
"""
import sys, os, argparse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args()

    try:
        import pymupdf
    except ImportError:
        sys.exit("需要 PyMuPDF：pip install pymupdf")

    pdf = args.pdf
    outdir = args.out or (os.path.splitext(os.path.basename(pdf))[0] + "_extract")
    os.makedirs(os.path.join(outdir, "maps"), exist_ok=True)

    doc = pymupdf.open(pdf)
    print(f"页数: {doc.page_count}")

    # 1) 文本
    buf = []
    for i in range(doc.page_count):
        buf.append(f"\n\n===== PAGE {i+1} =====\n" + doc[i].get_text())
    with open(os.path.join(outdir, "pages.txt"), "w", encoding="utf-8") as f:
        f.write("".join(buf))
    print(f"文本 -> {os.path.join(outdir,'pages.txt')}")

    # 2) 目录
    toc = doc.get_toc()
    with open(os.path.join(outdir, "toc.txt"), "w", encoding="utf-8") as f:
        for lvl, title, pg in toc:
            f.write("  " * (lvl - 1) + f"[p{pg}] {title}\n")
    print(f"目录 {len(toc)} 条 -> {os.path.join(outdir,'toc.txt')}")

    # 3) 图片（地图）
    n = 0
    for i in range(doc.page_count):
        for j, im in enumerate(doc[i].get_images(full=True)):
            xref = im[0]
            try:
                pix = pymupdf.Pixmap(doc, xref)
                if pix.n - pix.alpha >= 4:
                    pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                p = os.path.join(outdir, "maps", f"p{i+1}_{j}.png")
                pix.save(p)
                n += 1
                print(f"  图片 p{i+1} {pix.width}x{pix.height} -> {p}")
            except Exception as e:
                print(f"  ! p{i+1} 图片失败: {e}")
    print(f"共导出 {n} 张图片到 {os.path.join(outdir,'maps')}")


if __name__ == "__main__":
    main()
