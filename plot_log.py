import sys
import csv
import matplotlib.pyplot as plt


def csv_to_dict(filename):
	dict_entries = dict()
	with open(filename) as file_obj:
		reader = csv.DictReader(file_obj)
		for row in reader:
			for k, v in dict(row).items():
				if k in dict_entries.keys():
					dict_entries[k].append(float(v))
				else:
					dict_entries[k] = []
	return dict_entries


def extract_data(filename):
	reader = csv.DictReader(filename, delimiter=',')
	return csv_to_dict(filename)


def plot_data(data):
	fig, ax = plt.subplots()
	x_key = list(data.keys())[0]
	x_values = data[x_key]
	data.pop(x_key)

	for v in data.values():
		ax.plot(x_values, v)

	ax.legend(list(data.keys()))
	plt.show()



if __name__ == "__main__":
	data = extract_data(sys.argv[1])
	# print(type(data))
	plot_data(extract_data(sys.argv[1]))
