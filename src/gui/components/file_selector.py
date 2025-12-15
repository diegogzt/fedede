from __future__ import annotations


class FileSelector:
    SUPPORTED_EXTENSIONS = [".xlsx", ".xls", ".csv"]

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        size = float(size_bytes)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0 or unit == "TB":
                if unit == "B":
                    return f"{int(size)} {unit}"
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size_bytes} B"
