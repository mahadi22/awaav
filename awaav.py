#version = 0.2.0.0
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementNotVisibleException
from bs4 import BeautifulSoup
import argparse, re, time, getpass, sys,inspect,os
from random import randint

# Main url and the regular expression to match against it.
# The subdomain can change according to region, and could be:
# my.alienwarearena.com, uk.alienwarearena.com, latam.alienwarearena.com etc
mainURL = 'https://www.alienwarearena.com'
mainURLRegex = 'https:\/\/(\S+)\.alienwarearena\.com\/'

# parsed main args
args = None

counterPS = 0
oldARP = 0 
total_votes = 0
options = None

# the driver that will emulate user interactions in the browser
driver = None

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
    parser.add_argument('--max-pages', type=checkUnsignedInt, help='The maximum topic pages to crawl into before jump to next topic')

    global args
    args = parser.parse_args()

def init_driver():
    print('Starting driver~~~♫')

    global driver

    dir_files = os.listdir(os.path.abspath(os.path.dirname(sys.argv[0])))

    if args.driver:
        if args.driver.lower() == 'firefox':
            if 'geckodriver.exe' not in dir_files:
                raise Exception('Firefox driver not found, place it on same folder with this script')
            
            options = Options()
            options.set_headless(headless=True)
            driver = webdriver.Firefox(firefox_options=options)
			
            #ffprofile = webdriver.FirefoxProfile(profileLoc)
            #driver = webdriver.Firefox(ffprofile)                                  
			
    if driver is None:
        if 'chromedriver.exe' not in dir_files:
            raise Exception('Chrome driver not found, place it on same folder with this script')
        driver = webdriver.Chrome()                

    driver.wait = WebDriverWait(driver, 30) # wait object that waits (you don't say?) for elements to appear
    
    print('Driver "' + driver.name + '" started. ♥\n')

def check_page_error(soup):
    errorElement = soup.find('h1', class_='content-title text-center')
    return (errorElement is not None)    

def enter_and_parse_url(url):
    tries = 0    
    success = False
    soupURL = None

    while not success:
        if tries > 5:
            raise Exception('Too many times trying to access URL ' + url)

        print('Going to ' + url + ' ~~~♪\n')
        driver.get(url)
        soupURL = BeautifulSoup(driver.page_source, 'html.parser')

        if check_page_error(soupURL):
            print('Error trying to access ' + url + '. Trying again...\n')
        else:
            success = True

        tries += 1

    return soupURL

def starter():
    print ('\n---------------------------------')
    print ('--  Alienware Arena Auto Vote  --')
    print ('--           adi_a12           --')
    print ('---------------------------------\n')
	
def login():
    print('Logging in~~~♫')
    
    logged = False

    global user

    while not logged:
        soupLogin = enter_and_parse_url(mainURL + '/login')

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
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'toast-header')))
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
   
def print_status():
    print('Reading status~~~♫')
    global counterPS
    global oldARP
    global total_votes1
    odometer = 0
    arpTotal = ""

    soupMain = BeautifulSoup(driver.page_source, 'html.parser')

    # search for error in the main page
    if check_page_error(soupMain):
        print('Error trying to access main page. Trying again...')
        soupMain = enter_and_parse_url(mainURL)

    userName = soupMain.find(class_='dropdown-header')
    name_detail = re.findall('\w+', userName.text)[0]
    arpLevel = soupMain.find(class_='arp-level')
    level_num = re.findall('\d+', arpLevel.text)[0]
    incQuest = soupMain.find(class_='incomplete-quests')
    quest_num = re.findall('\d+', incQuest.text)[0]
    arp_box = soupMain.find('div', id='arp-toast')
    arp_rows = arp_box.find_all('tr')
    arp_cols = arp_box.find_all("span", {"class": "odometer-value"})
    total_rows = len(arp_rows)
    total_cols = len(arp_cols)
    while odometer < total_cols :
        arp_piece = arp_cols[odometer]
        arpTotal = arpTotal + str(re.findall('\d+', arp_piece.text)[0])
        odometer += 1
    
    votes = arp_rows[total_rows - 5].find(class_='text-center')
    daily = arp_rows[total_rows - 6].find(class_='text-center')
    total_votes1 = int(re.findall('\d+', votes.text)[0])
    total_daily = int(re.findall('\d+', daily.text)[0])
    
    print('---------- STATUS START ----------')
    print(time.strftime("Today date %d %B %Y"))
    print('Username: ' + str(name_detail))
    print('Your Level: ' + str(level_num))
    print('Total Arp: ' + str(arpTotal))
    print('Incomplete Quest: ' + str(quest_num))
    print('Total Daily Login: ' + str(total_daily))
    print('Votes cast: ' + str(total_votes1))
    if counterPS == 0 :
	    oldARP = arpTotal
	    counterPS += 1
    elif oldARP != arpTotal  : print('ARP Change: ' + str(int(arpTotal) - int(oldARP)))
    print('----------  STATUS END  ----------\n')

# ---------- MAIN ----------
if __name__ == '__main__':
    try:
        starter()
        parse_arguments()
        init_driver()
        login()
        print_status()
        #vote_on_content()
            
    except TimeoutException:
        print('Error: Element could not be found due to load time limit reached')
    except SystemExit:
        pass
    except BaseException as e:
        print('Something went wrong: ' + str(e))
    finally:
        print('Exiting, bye~~~♪\n\n\n')

    if driver is not None:
            driver.quit()
