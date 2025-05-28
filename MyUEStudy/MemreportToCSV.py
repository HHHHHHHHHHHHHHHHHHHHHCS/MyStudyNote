import os
import re

DEFAULT_TITLE = "Total"
LIST_PARTICLE_SYSTEMS = "ListParticleSystems"
CLASS_STATIC_MESH = "class=StaticMesh "
CLASS_SKELETAL_MESH = "class=SkeletalMesh "

class CSVFile:
	csv_type = ""
	is_open = False
	start_line = -1
	end_line = -1
	last_to_top_line = 0
	is_texture_group = False
	is_special_class = False

	def __str__(self):
		return f"CSVFile(csv_type={self.csv_type}, start_line={self.start_line}, end_line={self.end_line})"

def DoMain(file_path):
	lines = None
	with open(file_path, 'r', encoding='utf-8') as file:
		lines = file.readlines()
		
	if lines is None:
		print("Open File Fauired, Lines is null!")
		return

	csv_list = []
	curr_line = 0
	temp_csv = CSVFile()
	for line in lines:
		if temp_csv.is_open:
			if line.startswith("MemReport: End command"):
				temp_csv.end_line = curr_line

				if temp_csv.start_line >= 0 and temp_csv.end_line > temp_csv.start_line:
					csv_list.append(temp_csv)

					if temp_csv.is_special_class:
						header_index = temp_csv.start_line+1
						header = re.findall(r'\S+', lines[header_index])
						lines[header_index] = (','.join(header)) + '\n'
						header_index = temp_csv.end_line-4
						header = re.findall(r'\S+', lines[header_index])
						lines[header_index] = (','.join(header)) + '\n'
						header_index = temp_csv.end_line-3
						lines[header_index] = ','.join(lines[header_index].rsplit(' ', 1))

				temp_csv = CSVFile()

			elif temp_csv.start_line < 0:
				if temp_csv.csv_type == LIST_PARTICLE_SYSTEMS or temp_csv.is_texture_group:
					temp_csv.start_line = curr_line + 1 # 跳过这行
				elif line.startswith(','):
					temp_csv.start_line = curr_line
				elif temp_csv.is_special_class:
					temp_csv.start_line = curr_line + 2 # 跳过这行和下行
			
			if temp_csv.is_open:
				if line.startswith(','):
					lines[curr_line] = line[1:]
				elif temp_csv.is_texture_group:
					if line.startswith("Total "):
						temp_csv.last_to_top_line += 1
					elif line.find(" KB, ") > 0:
						lines[curr_line] = line.replace(" KB, ", " KB| ", 1)
				elif temp_csv.is_special_class:
					match = re.match(r'^(.*?)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)$', line.strip())
					if match:
						lines[curr_line] = (','.join(match.groups()))+'\n'

		elif line.startswith("MemReport: Begin command"):
			title_start = line.find('"') + 1
			title_end = line.rfind('"')
			csv_type = line[title_start:title_end]

			if "-CSV" in csv_type:
				temp_csv.is_open = True
				class_start = csv_type.find("class=")

				if class_start >= 0:
					class_end = csv_type.find(" ", class_start)
					csv_type = csv_type[class_start+len("class="):class_end]
				else:
					split_index = csv_type.find(" ")
					if split_index >= 0:
						csv_type = csv_type[:split_index]
						if csv_type == "obj":
							csv_type = DEFAULT_TITLE
				temp_csv.csv_type = csv_type
				temp_csv.last_to_top_line = 1

			elif " CSV" in csv_type:
				temp_csv.is_open = True
				split_index = csv_type.rfind(" ")
				if split_index >= 0:
					csv_type = csv_type[:split_index]
				temp_csv.csv_type = csv_type
				temp_csv.is_texture_group = True
				temp_csv.last_to_top_line = 0

			elif CLASS_STATIC_MESH in csv_type or CLASS_SKELETAL_MESH in csv_type:
				temp_csv.is_open = True
				class_start = csv_type.find("class=")
				class_end = csv_type.find(" ", class_start)
				csv_type = csv_type[class_start+len("class="):class_end]
				temp_csv.csv_type = csv_type
				temp_csv.last_to_top_line = 1
				temp_csv.is_special_class = True

		curr_line += 1

	if len(csv_list) > 0:
		save_dir = os.path.dirname(file_path) + "/OutCSV"

		if not os.path.exists(save_dir):
			os.makedirs(save_dir)

		for item in csv_list:
			out_file_path = format(f"{save_dir}/{item.csv_type}.csv")
			with open(out_file_path, "w", encoding="utf-8") as f:
				last_line = item.end_line

				f.writelines(lines[last_line - item.last_to_top_line : last_line])
				last_line -= item.last_to_top_line

				f.write('\n')

				if item.csv_type == LIST_PARTICLE_SYSTEMS or item.is_texture_group:
					pass
				elif item.csv_type != DEFAULT_TITLE:
					f.write(lines[last_line-3])
					f.write(lines[last_line-2])
					f.write(lines[last_line-1])
					last_line -= 3

				f.writelines(lines[item.start_line:last_line])

if __name__ == "__main__":
	file_path = input("Input memreport file path: ")
	if not os.path.exists(file_path):
		print("File does not exist")
	else:
		DoMain(file_path)