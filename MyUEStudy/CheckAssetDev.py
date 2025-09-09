import os

def find_files_with_pattern(root_folder, pattern, output_file):
	matched_files = []

	for dirpath, _, filenames in os.walk(root_folder):
		for filename in filenames:
			file_path = os.path.join(dirpath, filename)

			try:
				with open(file_path, "rb") as f:
					content = f.read()
					if pattern in content:
						# print(f"Add file: {file_path}")
						matched_files.append(file_path)
			except (UnicodeDecodeError, PermissionError, IsADirectoryError):
				# print(f"Break file: {file_path}")
				continue

	with open(output_file, "w", encoding="utf-8") as f:
		for path in matched_files:
			f.write(path + "\n")

	print(f"扫描完成, 共找到 {len(matched_files)} 个文件, 结果保存在 {output_file}")

if __name__ == "__main__":
	root = r"UEProject\Content" # 修改成你要扫描的文件夹
	output = "output.txt" # 输出文件
	pattern = b"/Game/Developers/" # 关键词
	find_files_with_pattern(root, pattern, output)