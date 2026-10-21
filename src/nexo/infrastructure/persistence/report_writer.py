from pathlib import Path


class CsvReportWriter:
    def write(self, path: str, content: str) -> None:
        # UTF-8 BOM preserves Portuguese characters in Windows spreadsheet tools.
        Path(path).write_text(content, encoding="utf-8-sig", newline="")
