from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementNotVisibleException
from bs4 import BeautifulSoup
import re
import time
from random import randint
import getpass
import sys
import os

# Main url and the regular expression to match against it.
# The subdomain can change according to region, and could be:
# latam.alienwarearena.com, eu.alienwarearena.com etc
mainURL = 'https://na.alienwarearena.com'
mainURLRegex = 'https:\/\/(\S+)\.alienwarearena\.com\/'

# the driver that will emulate user interactions in the browser
driver = None

user = ''
password = ''
total_threads = 0
total_votes = 0
#total_this_that = 0

def init_driver():
    print('Starting driver...')

    newDriver = None
    dir_files = os.listdir()

    if len(sys.argv) > 1:
        if sys.argv[1].lower() == 'firefox':
            if 'geckodriver.exe' not in dir_files:
                raise Exception('Firefox driver not found')

            newDriver = webdriver.Firefox()                                  
                
    if newDriver is None:
        if 'chromedriver.exe' not in dir_files:
            raise Exception('Chrome driver not found')

        newDriver = webdriver.Chrome()                

    newDriver.wait = WebDriverWait(newDriver, 120) # wait object that waits (you don't say?) for elements to appear
    
    print('Driver "' + newDriver.name + '" started.\n')

    return newDriver

def check_page_error(soup):
    errorElement = soup.find('h3', class_='text-error')
    return (errorElement is not None)    

def enter_and_parse_url(url):
    tries = 0    
    success = False
    soupURL = None

    while not success:
        if tries > 5:
            raise Exception('Too many times trying to access URL ' + url)

        print('Going to ' + url + ' ...')
        driver.get(url)
        soupURL = BeautifulSoup(driver.page_source, 'html.parser')

        if check_page_error(soupURL):
            print('Error trying to access ' + url + '. Trying again...')
        else:
            success = True

        tries += 1

    return soupURL

def login():
    print('Logging in...\n')
    
    logged = False

    global user

    while not logged:
        soupLogin = enter_and_parse_url(mainURL + '/login')

        input_user = driver.wait.until(EC.presence_of_element_located((By.NAME, '_username')))
        input_pass = driver.wait.until(EC.presence_of_element_located((By.NAME, '_password')))
        bt_login = driver.wait.until(EC.element_to_be_clickable((By.NAME, '_login')))

        user = input('username: ')
        password = getpass.getpass('password: ')
        #user = user1
        #password = getpass.getpass(password1)		

        input_user.send_keys(user)
        input_pass.send_keys(password)
        bt_login.click();

        # since firefox driver doesn't wait for the page to load after a button click, we need to check if an 
        # element of the main page is present by setting a timer, so then we know we're logged in
        if driver.name == 'firefox':
            try:
                WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'panel-arp-status')))
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
    print('Reading status...\n')

    soupMain = BeautifulSoup(driver.page_source, 'html.parser')

    # search for error in the main page
    if check_page_error(soupMain):
        print('Error trying to access main page. Trying again...')
        soupMain = enter_and_parse_url(mainURL)

    # find html elements for status
    level_parent = soupMain.find(class_='media-heading')
    level = level_parent.find('strong')
    remaining = level_parent.find('i')
    points_parent = level_parent.find_next_sibling('h5')
    points = points_parent.find('strong')

    # find daily tasks numbers
    global total_threads
    global total_votes
    #global total_this_that

    # the ARP box is a folding div that contains all points earned on the current day
    arp_box = soupMain.find('div', id='arp-toast')
    arp_rows = arp_box.find_all('tr')
    threads = arp_rows[1].find(class_='text-center')
    votes = arp_rows[2].find(class_='text-center')
    #this_that = arp_rows[3].find(class_='text-center')

    # extract numbers from status fields
    level_num = re.findall('\d+', level.text)[0]
    remaining_num = re.findall('\d+', remaining.text)[0]
    points_num = re.findall('\d+', points.text)[0]
    total_threads = int(re.findall('\d+', threads.text)[0])
    total_votes = int(re.findall('\d+', votes.text)[0])
    #total_this_that = int(re.findall('\d+', this_that.text)[0])

    print('---------- STATUS ----------')
    print('Your level: ' + level_num)
    print('Total points: ' + points_num + ' (' + remaining_num + ' remaining to next level)\n')
    print('Threads created: ' + str(total_threads))
    print('Votes cast: ' + str(total_votes))
    #print('This or That votes: ' + str(total_this_that))
    print('---------- STATUS ----------\n')

def vote_on_content():
    print('Voting on content...')

    global total_votes

    def check_total_votes():
        return (total_votes >= 50)

    if check_total_votes(): 
        print('All votes already cast')
        return

    # enter and parse the news forum
    soupNewsForum = enter_and_parse_url(mainURL + '/forums/board/458/gaming-news')
    print('- Entered news forum')

    # get the topics
    topics_table = soupNewsForum.find(class_='table-topic')
    table_rows = topics_table.find_all('tr')

    # for every row (from the second one - first is header), get the first <a> - link to the forum thread
    for row_number, row in enumerate(table_rows[1:], 1):
        if check_total_votes(): break

        print('-- Entering news ' + str(row_number) + ': ')

        topic_link = row.find('a').get('href')

        # enter the topic and parse its content
        soupTopic = enter_and_parse_url(mainURL + topic_link)

        # number of comments pages 
        page_count = 1

        # check if there's an element "pagination" which indicates more than 10 comments
        pagination = soupTopic.find('ul', class_='pagination')
        next_page = None

        if pagination is not None:
            next_page = pagination.find('li', class_='next')
            pagination_total = next_page.previous_sibling.find('a')
            page_count = int(pagination_total.text)

        for page_index in range(0, page_count):
            if check_total_votes(): break

            # if page is not the first, parse it
            if page_index > 0:
                soupTopic = BeautifulSoup(driver.page_source, 'html.parser')

            # if there is any error in this page, go to the next news
            if check_page_error(soupTopic): 
                print('!-- Error on page. Going to the next news --!')
                break    

            # get the upvote buttons
            upvotes = soupTopic.find_all(class_='post-up-vote')
            votes_on_page = 0

            for upvote in upvotes:
                if check_total_votes(): break

                item_up = upvote.find('i')
                
                if item_up.get('style') != 'color: gold;':
                    bt_upvote = driver.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-post-id=\'' + upvote.get('data-post-id') + '\'][title=\'Up Vote\']')))
                    driver.execute_script('arguments[0].scrollIntoView(false);', bt_upvote);
                    driver.execute_script('window.scrollTo(0, window.scrollY + ' + str(150) + ')')
                    bt_upvote.click()

                    total_votes += 1
                    votes_on_page += 1

            print('--- Votes on page ' + str(page_index + 1) + ': ' + str(votes_on_page))

            if check_total_votes(): break
            # if it's not the last page, go to the next
            if (page_index < (page_count - 1)):
                print('--- Going to comment page ' + str(page_index + 2))
                bt_next_page = driver.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.next a')))

                # scroll to the next button (it will be on the bottom of the page) and then a little bit lower to be sure it will not be blocked by any element
                driver.execute_script('arguments[0].scrollIntoView(false);', bt_next_page);
                driver.execute_script('window.scrollTo(0, window.scrollY + ' + str(150) + ')')
                
                bt_next_page.click()

                # wait for the next button to be active, then we know the comments were loaded
                try:
                    bt_number_next_page = driver.wait.until(EC.element_to_be_clickable((By.XPATH, "//ul[@class='pagination pagination-sm']/li[@class='active']/a[text()='" + str(page_index + 2) + "']")))
                except TimeoutException:
                    print('!-- Page ' + str(page_index + 2) + ' didn\'t load in time. Going to the next news...')
                    break

    print('Done! All votes cast')

def vote_on_this_or_that():
    has_chosen1 = False
    choice1 = ''

    while not has_chosen1:
        choice1 = input('Do you want to skip this or that? (y/n) ')
        has_chosen1 = (choice1 == 'y' or choice1 == 'n')

    if choice1 == 'y': return
	
    def check_total_tt_votes():
        return (total_this_that >= 25)

    if check_total_tt_votes():
        print('All This or That votes already cast')
        return
	
    print('Voting on This or That...')

    # enter and parse the This or That forum
    soupTT = enter_and_parse_url(mainURL + '/forums/board/293/this-or-that')
    print('- Entered This or That forum')

    # get the link to the first post
    topic_link = soupTT.find('a', class_='board-topic-title')['href']
    soupTT = enter_and_parse_url(mainURL + topic_link)
    print('- Entered first This or That topic')

    global total_this_that

    # This will determine if, after a page refresh, the ToT totals really reached the limit.
    # This is needed because voting on ToT is based on clicking on the vote button in 
    # a time interval. The time interval may not be enough for the voting click to load 
    # the next button, so it's not guaranteed all votes will be cast
    all_tt_on_refresh = False

    while not all_tt_on_refresh:
        # find, scroll to and click the "start voting now" button
        bt_start = driver.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.btn.btn-primary.btn-show-vote')))
        driver.execute_script('arguments[0].scrollIntoView(false);', bt_start);
        driver.execute_script('window.scrollTo(0, window.scrollY + ' + str(150) + ')')
        bt_start.click()

        print('-- Now voting...')

        while not check_total_tt_votes():
            img_vote = driver.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.img.pull-right')))
            
            if driver.name == 'firefox':
                driver.execute_script('arguments[0].scrollIntoView(false);', img_vote);
                driver.execute_script('window.scrollTo(0, window.scrollY + ' + str(150) + ')')
            
            hover = ActionChains(driver).move_to_element(img_vote)
            hover.perform()
            
            time.sleep(1)
            img_vote.click()

            total_this_that += 1
            time.sleep(5)

        # now we need to check if all votes were really cast by refreshing the page and getting the status
        soupTT = enter_and_parse_url(mainURL + topic_link)

        arp_box = soupTT.find('div', id='arp-toast')
        arp_rows = arp_box.find_all('tr')
        this_that = arp_rows[3].find(class_='text-center')
        total_this_that = int(re.findall('\d+', this_that.text)[0])

        if total_this_that >= 25: all_tt_on_refresh = True

    print('Done! All This or That votes cast')

def post_on_news_forum():
    has_chosen = False
    choice = ''

    while not has_chosen:
        choice = input('Do you want to post on news forum? (y/n) ')
        has_chosen = (choice == 'y' or choice == 'n')

    if choice == 'n': return

    has_chosen = False
    num_posts = 0

    while not has_chosen:
        try:
            num_posts = int(input('How many posts? '))
        except ValueError:
            print('Please, enter a number')
        else:
            if num_posts <= 0:
                print('Please, enter a positive number')
            else:
                has_chosen = True

    # open the posts file and count how many lines are in it
    file = open('posts.txt')
    file_lines = sum(1 for line in file)
    
    total_posts = 0
    current_news_page = 1

    while total_posts < num_posts:
        # enter and parse the current news forum page
        soupNewsForum = enter_and_parse_url(mainURL + '/forums/board/458/gaming-news/' + str(current_news_page))

        # get the total responses from every topic
        total_responses = soupNewsForum.find_all('td', class_='td-topic-total')

        # the "td-topic-total" class is used for numbers of views too, so we are only getting the value every two table cells
        for total in total_responses[::2]:
            if int(total.text) >= 10: # we just want posts with less than 10 responses because they give us more visibility (front page!)
                continue

            # here we have the link to a topic with less than 10 responses, let's get in
            topic_link = total.find_previous_sibling('td').find('a')['href']
            soupTopic = enter_and_parse_url(mainURL + topic_link)

            # get all the usernames that have posted
            usernames = soupTopic.find_all('a', class_='username')

            if user in [u.text for u in usernames]:
                print('You already have posted in this topic')
            else:
                # go to the start of the file stream so we can read it again
                file.seek(0)

                line_number = randint(0, (file_lines - 1))
                post = ''

                # get the line number randomized earlier
                for i, line in enumerate(file):
                    if i == line_number:
                        post = line
                        break

                # the string without the new line character "\n"
                post = post.split('\n')[0]

                iframe = driver.find_element_by_css_selector('iframe.cke_wysiwyg_frame.cke_reset')
                driver.switch_to.frame(iframe)
                post_text_area = driver.find_element_by_xpath('html/body')                
                post_text_area.send_keys(post)

                driver.switch_to.default_content()
                
                bt_post = driver.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'form .btn.btn-primary')))
                
                # scroll to the button and click on it
                driver.execute_script('arguments[0].scrollIntoView(false);', bt_post);
                driver.execute_script('window.scrollTo(0, window.scrollY + ' + str(150) + ')')
                bt_post.click()

                # firefox doesn't wait after a click, so we need to wait on our own
                if driver.name == 'firefox': time.sleep(5)

                print('Posted \"' + post + '\"')

                total_posts += 1
                
                if total_posts >= num_posts: break
                
        current_news_page += 1

    file.close()
    print('Done! All posts made')        

# ---------- MAIN ----------

if __name__ == '__main__':
    try:
        driver = init_driver()

        login()
        print_status()
        vote_on_content()
        vote_on_this_or_that()
        post_on_news_forum()
    
    except TimeoutException:
        print('Error: element could not be found due to load time limit reached')
    except BaseException as e:
        print('Something went wrong: ' + str(e))
    finally:
        print('Exiting...')

        if driver is not None:
            driver.quit()