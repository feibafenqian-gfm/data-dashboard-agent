"""把 output/ 下的 HTML 转成 PDF（用系统 Edge / Chrome 无头模式渲染）。

用法：
    python export_pdf.py           # 转换 output/ 下所有 .html
    python export_pdf.py output    # 同目录
"""
import os
import sys
import glob
import subprocess

BROWSER_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def find_browser():
    for p in BROWSER_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def html_to_pdf(html_path, pdf_path):
    browser = find_browser()
    if not browser:
        raise RuntimeError("未找到 Edge/Chrome 浏览器，无法转 PDF")
    url = "file:///" + os.path.abspath(html_path).replace("\\", "/")
    pdf_path = os.path.abspath(pdf_path)
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--virtual-time-budget=10000",
        f"--print-to-pdf={pdf_path}",
        url,
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=180)
    return pdf_path


def main():
    if len(sys.argv) > 1:
        dirs = [sys.argv[1]]
    else:
        dirs = sorted(glob.glob(os.path.join("datasets", "*", "output")))
        if not dirs:
            dirs = ["output"]
    for out_dir in dirs:
        htmls = sorted(glob.glob(os.path.join(out_dir, "*.html")))
        if not htmls:
            continue
        for html in htmls:
            pdf = os.path.splitext(html)[0] + ".pdf"
            html_to_pdf(html, pdf)
            size_mb = os.path.getsize(pdf) / 1e6
            print(f"-> {pdf}  ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
