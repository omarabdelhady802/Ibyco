import os

# هنا حدد مسار المشروع
project_path = "./IBYCO"  # أو path كامل للمشروع

# هنا تحدد أنواع الملفات اللي عايز تنظفها
file_extensions = [".py", ".txt", ".md"]  # ضيف أي امتداد تاني لو محتاج

# function تمسح U+00A0 وتستبدلها بـ space عادي
def clean_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = content.replace("\u00A0", " ")  # replace non-breaking space
    if new_content != content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Cleaned: {file_path}")

# function تمشي على كل الملفات داخل المشروع
def clean_project(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            if any(file.endswith(ext) for ext in file_extensions):
                clean_file(os.path.join(root, file))

if __name__ == "__main__":
    clean_project(project_path)
    print("✅ Finished cleaning all files.")