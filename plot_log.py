import sys
import debug


if __name__ == "__main__":
	log = debug.Log(file_variant=sys.argv[1])
	debug.plot_data(log.to_dict())
