import sys

'''
eg 9th Aug 2019 to 2019-08-09
'''
def reformatDate(dates):
	days=('1st', '2nd', '3rd', '4th', '5th','6th', '7th','8th', '9th', '10th',
		'11th', '12th', '13th', '14th', '15th', '16th', '17th', '18th', '19th', '20th',
		'21st', '22nd', '23rd', '24th', '25th', '26th', '27th', '28th', '29th', '30th',
		'31st')
	months=('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
	new = []
	for date in dates:
		date = date.split()
		day = date[0]
		month = date[1]
		if day in days and month in months:
			new.append(date[2]+ '-'+
				(str(months.index(month)+1)).zfill(2)+ '-' +
				(str(days.index(day)+1)).zfill(2))
	return new
if __name__ == '__main__':

	dates = sys.stdin.read().splitlines()
	print(dates)

	print('new: ', reformatDate(dates))