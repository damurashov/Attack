import argparse

def getarparser():

	parser = argparse.ArgumentParser()

	parser.add_argument('--min_hits', type=int,  default=3,  help='minimum hits before state tracker will be CONFIRMED')
	parser.add_argument('--max_age',  type=int,  default=10, help='maximum predictes without updates')
	parser.add_argument('--tracker_name', type=str, default='kcf', choices=['csrt', 'kcf', 'mil'])
	parser.add_argument('--pid_input', type=str, default='pixels', choices=['pixels', 'angles'])
	return parser