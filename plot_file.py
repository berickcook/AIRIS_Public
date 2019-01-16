import sys
import matplotlib.pyplot as plt


# verify file was specified
args = sys.argv
if len(args) == 2:
	filename = sys.argv[1]
else:
	print('Invalid inputs. Proper input:')
	print('python plot_data.py <filename>')
	sys.exit()

# get data from specified file
data = []
for line in open(filename, 'r'):
	try:
		data.append(float(line))
	except:
		print('Invalid file data.')
		print('File must have 1 number per line.')
		sys.exit()

# plot data 
fig = plt.figure()
plt.plot(data)
plt.title('Training Accuracy')
plt.xlabel('Sample Number')
plt.ylabel('Accuracy %')
plt.show()

