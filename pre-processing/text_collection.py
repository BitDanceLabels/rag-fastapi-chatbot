from PyPDF2 import PdfReader
import pandas as pd
import os
import re
from collections import Counter



class Preprocessing:
    def __init__(self, dir_path: str) -> None:
        self.dir_path = dir_path
        self.pdf_files = [f for f in os.listdir(dir_path) if f.endswith(".pdf")]

    def get_all_text_from_file(self, file_name: str) -> str:
        file_path = os.path.join(self.dir_path, file_name)
        reader = PdfReader(file_path)
        all_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                all_text.append(text.strip())
        return "\n".join(all_text)

    def get_all_text_from_folder(self) -> pd.DataFrame:
        records = []
        for pdf_file in self.pdf_files:
            text = self.get_all_text_from_file(pdf_file)
            records.append({"file_name": pdf_file, "text": text})
        return pd.DataFrame(records)

    def word_frequency(self, df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
        """Đếm tần suất từ trong toàn bộ PDF"""
        # Ghép toàn bộ text
        all_text = " ".join(df["text"].dropna())

        # Làm sạch: bỏ ký tự đặc biệt, chuyển về lowercase
        words = re.findall(r"\b\w+\b", all_text.lower())

        # Đếm tần suất
        counter = Counter(words)

        # Trả về DataFrame top N từ phổ biến
        freq_df = pd.DataFrame(counter.most_common(top_n), columns=["word", "count"])
        return freq_df


# --- Test ---
if __name__ == "__main__":
    pdf_processor = Preprocessing("../document")  # thay bằng đường dẫn thật
    df = pdf_processor.get_all_text_from_folder()
    freq_df = pdf_processor.word_frequency(df, top_n=100)
    print(freq_df)


