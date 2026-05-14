import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import mammoth
import base64
import os
import threading
from pathlib import Path


class DocxToHtmlConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("DOCX → HTML 변환기")
        self.root.geometry("620x440")
        self.root.resizable(True, True)
        self.selected_files = []
        self._setup_ui()

    def _setup_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # File list area
        frame_files = ttk.LabelFrame(self.root, text="변환 파일 목록", padding=8)
        frame_files.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 4))
        frame_files.columnconfigure(0, weight=1)
        frame_files.rowconfigure(0, weight=1)

        self.file_listbox = tk.Listbox(frame_files, selectmode=tk.EXTENDED, height=10)
        scrollbar_y = ttk.Scrollbar(frame_files, orient=tk.VERTICAL, command=self.file_listbox.yview)
        scrollbar_x = ttk.Scrollbar(frame_files, orient=tk.HORIZONTAL, command=self.file_listbox.xview)
        self.file_listbox.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.file_listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        # File control buttons
        frame_file_btns = ttk.Frame(self.root, padding=(10, 0))
        frame_file_btns.grid(row=1, column=0, sticky="ew")

        ttk.Button(frame_file_btns, text="파일 추가", command=self._add_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_file_btns, text="선택 제거", command=self._remove_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_file_btns, text="전체 제거", command=self._clear_files).pack(side=tk.LEFT, padx=2)

        self.convert_btn = ttk.Button(frame_file_btns, text="변환 시작", command=self._start_conversion)
        self.convert_btn.pack(side=tk.RIGHT, padx=2)

        # Status area
        frame_status = ttk.LabelFrame(self.root, text="상태", padding=8)
        frame_status.grid(row=2, column=0, sticky="ew", padx=10, pady=(6, 10))
        frame_status.columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="파일을 추가한 후 변환을 시작하세요.")
        ttk.Label(frame_status, textvariable=self.status_var, anchor="w").grid(row=0, column=0, sticky="ew")

        self.progress = ttk.Progressbar(frame_status, mode="determinate", maximum=100)
        self.progress.grid(row=1, column=0, sticky="ew", pady=(4, 0))

    # ------------------------------------------------------------------ #
    #  File list management                                                #
    # ------------------------------------------------------------------ #

    def _add_files(self):
        filetypes = [
            ("DOCX 파일", "*.docx"),
            ("모든 파일", "*.*"),
        ]
        paths = filedialog.askopenfilenames(title="파일 선택", filetypes=filetypes)
        for path in paths:
            if path not in self.selected_files:
                self.selected_files.append(path)
                self.file_listbox.insert(tk.END, path)

    def _remove_selected(self):
        for index in reversed(self.file_listbox.curselection()):
            self.file_listbox.delete(index)
            self.selected_files.pop(index)

    def _clear_files(self):
        self.file_listbox.delete(0, tk.END)
        self.selected_files.clear()

    # ------------------------------------------------------------------ #
    #  Conversion                                                          #
    # ------------------------------------------------------------------ #

    def _start_conversion(self):
        if not self.selected_files:
            messagebox.showwarning("경고", "변환할 파일을 먼저 추가하세요.")
            return
        self.convert_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._run_conversion, daemon=True).start()

    def _run_conversion(self):
        total = len(self.selected_files)
        success_count = 0
        errors = []

        for i, filepath in enumerate(self.selected_files):
            filename = os.path.basename(filepath)
            self._set_status(f"변환 중 ({i + 1}/{total}): {filename}", (i / total) * 100)

            try:
                output_path = Path(filepath).with_suffix(".html")
                with open(filepath, "rb") as docx_file:
                    result = mammoth.convert_to_html(
                        docx_file,
                        convert_image=mammoth.images.img_element(self._image_to_base64),
                    )
                html = self._wrap_html(Path(filepath).stem, result.value)
                output_path.write_text(html, encoding="utf-8")
                success_count += 1
            except Exception as exc:
                errors.append(f"{filename}: {exc}")

        self._set_status(
            f"완료: {success_count}/{total}개 성공" + (f", {len(errors)}개 실패" if errors else ""),
            100,
        )
        self.root.after(0, lambda: self._show_result(total, success_count, errors))

    def _set_status(self, message: str, progress: float):
        self.root.after(0, lambda: self.status_var.set(message))
        self.root.after(0, lambda: self.progress.configure(value=progress))

    def _show_result(self, total: int, success: int, errors: list):
        self.convert_btn.config(state=tk.NORMAL)
        if errors:
            messagebox.showerror(
                "변환 완료 (일부 실패)",
                f"{success}/{total}개 성공.\n\n실패 목록:\n" + "\n".join(errors),
            )
        else:
            messagebox.showinfo("변환 완료", f"{total}개 파일을 모두 성공적으로 변환했습니다.")

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _image_to_base64(image):
        with image.open() as img_file:
            data = base64.b64encode(img_file.read()).decode("utf-8")
        return {"src": f"data:{image.content_type};base64,{data}"}

    @staticmethod
    def _wrap_html(title: str, body: str) -> str:
        return (
            "<!DOCTYPE html>\n"
            '<html lang="ko">\n'
            "<head>\n"
            '<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            f"<title>{title}</title>\n"
            "<style>\n"
            "  body { font-family: 'Malgun Gothic', sans-serif; max-width: 960px;"
            " margin: 40px auto; padding: 0 20px; line-height: 1.6; }\n"
            "  img { max-width: 100%; height: auto; }\n"
            "</style>\n"
            "</head>\n"
            "<body>\n"
            f"{body}\n"
            "</body>\n"
            "</html>\n"
        )


def main():
    root = tk.Tk()
    DocxToHtmlConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
