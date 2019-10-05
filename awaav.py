<<<<<<< HEAD
#version = 1.1.4.1
=======
#version = 1.1.3.1
>>>>>>> parent of ec1ca74... non headless option
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import argparse, re, time, getpass, sys, inspect, os

os.system('cls')  # clear screen

mainURL = 'https://www.alienwarearena.com'
mainURLRegex = 'https:\/\/(\S+)\.alienwarearena\.com\/'

# parsed main args and the driver that will emulate user interactions in the browser
args = driver = options = None

# Location to your firefox profile with adblock/ublock/another addon on, keep the r in front of address location (r"address")
profileLoc = (r"C:\Users\xxxxxx\AppData\Roaming\Mozilla\Firefox\Profiles\xxxxx.default")

tsTime = teTime = votesToday = counterPS = total_votes = arpTotal = 0
nTime = time.strftime("%a, %d %b %Y %H:%M:%S %z")
tsTime = time.time()

def parse_arguments():
    parser = argparse.ArgumentParser('awaav.py')

    # condition to check the driver argument
    def checkDriver(arg_driver):
        if arg_driver.lower() != 'chrome' and arg_driver.lower() != 'firefox' :
            raise argparse.ArgumentTypeError('must be either chrome or firefox')

        return arg_driver

    def checkUnsignedInt(arg_uint):
        error = 'must be an number and greater than 0'

        try:
            number = int(arg_uint)
        except ValueError:
            raise argparse.ArgumentTypeError(error)

        if number < 1:
            raise argparse.ArgumentTypeError(error)

        return number

    parser.add_argument('--username', type=str, help='Login username')
    parser.add_argument('--password', type=str, help='Login password')
    parser.add_argument('--driver', type=checkDriver, help='The driver to be used: \'chrome\'(default) or \'firefox\'')

    global args
    args = parser.parse_args()
    global nFile
    nFile = (args.username + '.xml' )

def init_driver():
    global driver
    print('Starting driver')
    dir_files = os.listdir(os.path.abspath(os.path.dirname(sys.argv[0])))

    if args.driver:
        if args.driver.lower() == 'firefox':
            if 'geckodriver.exe' not in dir_files:
                raise Exception('Firefox driver not found, place it on same folder with this script')

            options = Options()
            options.headless = True
            driver = webdriver.Firefox(options=options)

    if driver is None:
        if 'chromedriver.exe' not in dir_files:
            raise Exception('Chrome driver not found, place it on same folder with this script')
        options = webdriver.ChromeOptions()
        #options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(options=options)
    
    #if driver is None:
        #if 'chromedriver.exe' not in dir_files:
            #raise Exception('Chrome driver not found, place it on same folder with this script')
        #driver = webdriver.Chrome()   

    driver.wait = WebDriverWait(driver, 30) # wait object that waits (you don't say?) for elements to appear
    
    print('Driver "' + driver.name + '" started.\n')

def check_page_error(soup):
    errorElement = soup.find('h1', class_='content-title text-center')
    return (errorElement is not None)    

def enter_and_parse_url(url, printS):
    tries = 1    
    success = False
    soupURL = None

    while not success:
        if tries > 3:
            raise Exception('Too many times trying to access URL ' + url)

        if printS == 1 : 
            sys.stdout.write('Going to ' + url)
            sys.stdout.flush()
        driver.get(url)
        soupURL = BeautifulSoup(driver.page_source, 'html.parser')

        if check_page_error(soupURL):
            print('Page Not Found ' + url + '. Trying again...\n')
        else:
            success = True
            if printS == 1 : 
                sys.stdout.write(", loaded \n")
                sys.stdout.flush()

        tries += 1

    return soupURL

def starter():
    print ('\n---------------------------------')
    print ('--  Alienware Arena Auto Vote  --')
    print ('--           adi_a12           --')
    print ('---------------------------------\n')
	
def login():
    logged = False
    global user, soupLogin
    errorLogin = 0

    print('Logging in')

    while not logged:
        while errorLogin < 1 : 
            soupLogin = enter_and_parse_url(mainURL + '/login', 1)
            loginError = soupLogin.find_all('input', id='_username')
            errorLogin = len(loginError)

        input_user = driver.wait.until(EC.presence_of_element_located((By.NAME, '_username')))
        input_pass = driver.wait.until(EC.presence_of_element_located((By.NAME, '_password')))
        bt_login = driver.wait.until(EC.element_to_be_clickable((By.NAME, '_login')))

        if args.username:
            user = args.username
        else:
            user = input('Username: ')
        
        password = ''
        if args.password:
            password = args.password
        else:
            password = getpass.getpass('Password: ')

        input_user.send_keys(user)
        input_pass.send_keys(password)
        bt_login.click();

        # since firefox driver doesn't wait for the page to load after a button click, we need to check if an 
        # element of the main page is present by setting a timer, so then we know we're logged in
        if driver.name == 'firefox':
            try:
                #WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'toast-header')))
                driver.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'toast-header')))
                logged = True
            except TimeoutException:
                print('!-- Wrong user/pass or site error --!\n')

        # chrome driver waits for the page to load after the click command, so we just need to confirm if the
        # browser redirected to the main page        
        elif driver.name == 'chrome':
            if re.fullmatch(mainURLRegex, driver.current_url) is not None:
                logged = True
            else:
                print('!-- Wrong user/pass or site error --!\n')                   

    print('User logged in successfully\n')
    soupLogin = BeautifulSoup(driver.page_source, 'html.parser')

def print_status():
    global votesToday, counterPS, total_votes, oldARP, odometer, arpTotal, soupLogin
    odometer = total_votes = arpTotal = 0
    print('Reading status')
    if counterPS > 0 :
        soupMain = enter_and_parse_url(mainURL, 1)
    else: soupMain = soupLogin

    userName = soupMain.find(class_='dropdown-header')
    name_detail = re.findall('\w+', userName.text)[0]
    arpLevel = soupMain.find(class_='arp-level')
    level_num = re.findall('\d+', arpLevel.text)[0]
    incQuest = soupMain.find(class_='incomplete-quests')
    quest_num = re.findall('\d+', incQuest.text)[0]
    arp_box = soupMain.find('div', id='arp-toast')
    arp_rows = arp_box.find_all('tr')
    total_rows = len(arp_rows)
    votes = arp_rows[total_rows - 5].find(class_='text-center')
    daily = arp_rows[total_rows - 6].find(class_='text-center')
    total_votes = int(re.findall('\d+', votes.text)[0])
    total_daily = int(re.findall('\d+', daily.text)[0])

    arp_cols1 = arp_box.find_all('span', {'class': 'odometer-value'})
    arp_cols2 = arp_box.find_all('div', {'class': 'odometer-last-value'})
    total_cols1 = len(arp_cols1)
    total_cols2 = len(arp_cols2)
    if total_cols1 > 2 :
        while odometer < total_cols1 :
            arp_piece = arp_cols1[odometer]
            arpTotal = int(str(arpTotal) + str(re.findall('\d+', arp_piece.text)[0]))
            odometer += 1
    elif total_cols2 > 2 : 
        while odometer < total_cols2 :
            arp_piece = arp_cols2[odometer]
            arpTotal = int(str(arpTotal) + str(re.findall('\d+', arp_piece.text)[0]))
            odometer += 1
    else :
        soupStatus  = enter_and_parse_url(mainURL + '/member/', 1)
        arp_cols = soupStatus.find(class_='user-arp-total')
        arpTotal = int(re.findall('\w+', arp_cols.text)[0])

    if counterPS < 1 :
        oldARP = str(arpTotal)

    if total_votes == 20 :
        printLog('---------- STATUS START ----------')
        printLog(time.strftime("Today date %d %B %Y"))
        printLog('Username: ' + str(name_detail))
        printLog('Your Level: ' + str(level_num))
        printLog('Total Arp: ' + str(arpTotal))
        printLog('Incomplete Quest: ' + str(quest_num))
        printLog('Total Daily Login: ' + str(total_daily))
        printLog('Votes cast: ' + str(total_votes))
        if counterPS > 0 : 
            printLog('ARP Change: ' + str(int(arpTotal) - int(oldARP)))
        printLog('----------  STATUS END  ----------')
        teTime = time.time() - tsTime
        printLog("Elapsed time: " + str(teTime) + "sec")
    elif total_votes < 20 : print("Going to vote a post")

def header():
    with open(nFile,'w') as file:
        print('<?xml version="1.0" encoding="ISO-8859-1"?>',file=file)
        print('<rss version="2.0">',file=file)
        print('<channel>',file=file)
        print('<title>' + args.username + ' AWAAV Log</title>',file=file)
        print('<description>A simple RSS working as a log of AWAAV</description>',file=file)
        print('<item>',file=file)
        print('<title>Executed at', nTime, '</title>', file=file)
        print('<description>',file=file)
        print('<![CDATA[<table border=0>',file=file)

def footer():
    with open(nFile,'a') as file:
        print('</table>]]>',file=file)
        print('</description>',file=file)
        print('</item>',file=file)
        print('</channel>',file=file)
        print('</rss>',file=file)
        eTime = time.strftime("%a, %d %b %Y %H:%M:%S %z")
        print(eTime, file=file)

def printLog(*args, **kwargs):
    print(*args, **kwargs)
    with open(nFile,'a') as file:
        print("<tr><td>", file=file)
        print(*args, **kwargs, file=file)
        print("</td></tr>", file=file)

def voteLinks():
	global total_votes, counterPS
	linkPage = 1
	forumNum = voting = postInPage = 0
	need_votes = 20 - total_votes
	searchLinks = [
		'/forums/board/464/in-game-media-2/',
		'/forums/board/440/cosplay-1/',
		'/forums/board/113/off-topic-4/',
		'/forums/board/458/gaming-news/']

	if need_votes > 0 :
		print ("Voting " + str(need_votes) + " times...")
		soupSearch = enter_and_parse_url(mainURL + searchLinks[forumNum] + str(linkPage) + '?sort=topic', 1)
		postList = soupSearch.find_all('a', class_='board-topic-title')
		postInPage = len(postList)
		#votesWidth = need_votes
		sys.stdout.write("[%s]" % (" " * need_votes)) 
		sys.stdout.flush() 
		sys.stdout.write("\b" * (need_votes+1)) 
		
		while need_votes > 0 :
			postIDVote = postList[25-postInPage].get('data-topic-id')
			postInPage -= 1
			if need_votes > 0 :
				status_vote = doingVote(postIDVote)
				if status_vote == 200 : 
					need_votes -= 1
					sys.stdout.write("#")
					sys.stdout.flush()
					# votesDone = votesWidth - need_votes
					# sys.stdout.write("[%s]" % ("#" * votesDone) + str((votesDone)*votesPercent) + "%")
					# sys.stdout.write("\b" * (votesDone+7))
					# sys.stdout.flush()
			
			if postInPage == 0 and need_votes > 0 :
				linkPage += 1
				soupSearch = enter_and_parse_url(mainURL + searchLinks[forumNum] + str(linkPage) + '?sort=topic', 0)
				driver.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'board-topic-title')))
				postList = soupSearch.find_all('a', class_='board-topic-title')
				postInPage = len(postList)

		sys.stdout.write("]100%\n")
		counterPS += 1
		print_status()
	else : print ('No need to vote')

def doingVote(voteNum):
	soupRead = enter_and_parse_url(mainURL + '/ucf/vote/up/' + voteNum, 0)
	if soupRead.find(text=re.compile('successfully voted')) and soupRead.find('div', id='json').text :
		return 200
	else :
		return 404

# ---------- MAIN ----------
if __name__ == '__main__':
    try:
        starter()
        parse_arguments()
        header()
        init_driver()
        login()
        print_status()
        voteLinks()
            
    except TimeoutException:
        printLog('Error: Element could not be found due to load time limit reached')
    except SystemExit:
        pass
    except BaseException as e:
        printLog('Something went wrong: ' + str(e))
    finally:
        print('Exiting, bye\n\n')
        footer()
        driver.quit()

    if driver is not None:
            driver.quit()
