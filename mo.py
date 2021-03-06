"""
mo.py
0.0.8
*********************************************************************************************
Script pentru generarea de documente .pdf, pe baza imaginilor publicate de M.O.
Documentul .pdf va fi salvat pe Desktop.

Funcționează numai pentru numerele publicate din 06.06.2017 (de la Partea I, nr. 414/2017)
până în prezent.

Formatul de input este:
	[parte/]număr/an

Note:
* indicarea părții este opțională doar dacă se caută un număr din Partea I

Exemple de utilizare:
1. 1/414/2017 echivalent cu 414/2017 => Partea I, nr. 414 din 2017
2. 4/2378/2019 => Partea a IV-a, nr. 2378 din 2019
3. 2/17c/2019 => Partea a II-a, nr. 17/C din 2019
*********************************************************************************************
"""
print(__doc__) #comment this line to supress the manifest

import requests, re, sys, os, platform, tempfile
from fpdf import FPDF

#set up the fpdf object
pdf = FPDF('P', 'mm', 'A4')
pdf.set_display_mode('real', 'continuous')

#set the working folder paths
system = platform.system()
if system == 'Windows':
	file_location = tempfile.gettempdir() + "\\"
	pdf_location = os.path.join(
	    os.path.join(os.environ['USERPROFILE']), 'Desktop') + "\\"
elif system == 'Linux' or system == 'Darwin':
	file_location = tempfile.gettempdir() + "/"
	pdf_location = os.path.join(os.path.join(os.path.expanduser('~')),
	                            'Desktop') + "/"
	if not os.path.exists(pdf_location): #useful for Android running in qpython
		pdf_location = '/sdcard/' #assume there is such a folder; I won't bother to really check further for writeable folder...
else:
	print("Sistem de operare necunoscut. Programul nu poate continua.")
	sys.exit()

#the input loop: check the input and continue only if it is valid
while True:
	issue = input("Monitorul Oficial ([parte/]număr/an): ").replace(' ',
	                                                                '').lower()
	pattern = r"(?:(\dm*?)/)*?([\dbis c]+?)/(\d{4})$"
	part = '01'
	result = re.match(pattern, issue, re.IGNORECASE)
	if result == None: #test a regex pattern [\dbis]*?/\d{4}
		print(
		    "\nPartea, numărul sau anul nu sunt scrise corect. Mai încearcă o dată."
		)
		continue
	else:
		#if the part is specified, use it, else consider it to be part 01
		#part numbers above 1 are mapped in fact to index + 1
		if result.groups()[0] != None:
			index = result.groups()[0].replace("/", "")
			if index == "1m": #Hungarian language version of part 01 is mapped internally to 02; currently, no longer accessible
				index = "2"
			elif int(index) > 1:
				index = str(int(index) + 1)
			part = "0" + index
		#if the issue is valid separate number from year and return the two values
		number = result.groups()[1] #remove spaces and make the string lowercase
		if number.find('bis') >= 0: #check if bis is present
			number = number.replace('b', 'B').zfill(7)
		elif number.find('c') >= 0: #check if c is present
			number = number.zfill(5)
		else:
			number = number.zfill(4)
		year = result.groups()[2]
		break

#prepare the HTTP request to retrieve the images
url = 'http://www.monitoruloficial.ro/emonitornew/services/view.php'
user_agent = 'Mozilla/5.0 (Windows NT 6.2; rv:68.0) Gecko/20100101 Firefox/68.0' #this could be randomized
referer = 'http://www.monitoruloficial.ro/emonitornew/emonviewmof.php'
headers = {
    'User-Agent': user_agent,
    'Referer': referer,
    'X-Requested-With': 'XMLHttpRequest'
}
params = {'doc': part + year + number, 'format': 'jpg', 'page': '1'}
session = requests.Session()
file_list = [
] #a list containing full paths of downloaded files; later used for .pdf generation and then cleanup

#the HTTP request loop, using given criteria
print("\nSe descarcă imaginile.\n")
for i in range(
    1, 2500
): #2500 is arbitrary, but probably wouldn't be reached in realistic scenarios
	params['page'] = str(i)
	response = session.get(url, headers=headers, params=params)

	if str(response.content).find(
	    'Error') >= 0: #exit the loop if 'Error' is detected in the response
		break

	file_name = file_location + number + '-' + params['page'] + '.jpg'
	with open(file_name, 'wb') as fd:
		for chunk in response.iter_content(chunk_size=128):
			fd.write(chunk)
	print(str(i), end=' ') #display the progress
	sys.stdout.flush()
	file_list.append(file_name) #add image location to the list


def make_pdf(image_list):
	"""Iterate through the list of downloaded images and generate a .pdf"""
	if (not image_list):
		print("\nNu s-a găsit niciun document!")
		return 0
	print("\nSe generează PDF din imaginile descărcate.")
	for image in image_list:
		pdf.add_page()
		pdf.image(image, 0, 0, 210, 297)
	pdf.output(pdf_location + number + ".pdf", "F")


def cleanup(image_list):
	"""Iterate through the list of downloaded images and delete them"""
	if (not image_list):
		return 0
	print("\nSunt șterse imaginile descărcate.")
	for image in image_list:
		if os.path.exists(image):
			os.remove(image)
		else:
			print("\nNu există imaginea de la adresa: " + image)


if make_pdf(file_list) != 0:
	"""Do the document generation and then cleanup, but only if there were images found"""
	cleanup(file_list)
	print('\nGata! Documentul este salvat aici: ' + pdf_location + number +
	      ".pdf")

#prevent the console window from exiting without the user being able to see the output
if system == "Windows":
	os.system("<nul set /p \"=Apasă orice tastă pentru a ieși din aplicație...\""
	         ) #localized pause message
	os.system("pause >nul")
elif system == 'Linux' or system == 'Darwin':
	input("Apasă ENTER pentru a ieși din aplicație...")