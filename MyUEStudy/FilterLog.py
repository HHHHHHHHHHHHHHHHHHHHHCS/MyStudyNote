import re
import os

KEY_WORD = "DefaultMaterial"

def filter_unique_default_material_lines(log_path):
	unique_lines = set()
	re_str = r"\[.*?\]\[.*?\]\s*LogTemp: {0}\s*(.*)".format(KEY_WORD)
	pattern = re.compile(re_str)

	with open(log_path, 'r', encoding='utf-8') as file:
		for line in file:
			match = pattern.search(line)
			if match:
				content = match.group(1).strip()
				unique_lines.add(content)

	return list(unique_lines)

def save_list_to_txt(lines, output_path):
	with open(output_path, 'w', encoding='utf-8') as file:
		for line in lines:
			file.write(line + '\n')

if __name__ == "__main__":
	file_path = input("Input memreport file path: ")
	if not os.path.exists(file_path):
		print("File does not exist")
	else:
		result_lines = filter_unique_default_material_lines(file_path)
		save_list_to_txt(result_lines, os.path.join(os.path.dirname(file_path), "Output.txt"))
		
