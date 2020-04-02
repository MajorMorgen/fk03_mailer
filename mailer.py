import bs4 as bs
import urllib.request
from datetime import datetime
import time
import csv
import os
import pytz
from string import Template
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from secrets import mail_pw
import logging

MY_ADDRESS = 'schwarzesbrett.info@gmail.com'
PASSWORD = mail_pw
SLEEPTIME_HR = 0.5

def current_path():
        dir_path = os.path.dirname(os.path.realpath(__file__)) + "/"
        return dir_path    

class Scrape(object):

    brett_links = dict(

        FAB = "https://www.me.hm.edu/aktuelles/schwarzes_brett/schwarzes_brett_fab_seite.de.html",
        LRB = "https://www.me.hm.edu/aktuelles/schwarzes_brett/schwarzes_brett_lrb.de.html",
        MBB = "https://www.me.hm.edu/aktuelles/schwarzes_brett/schwarzes_brett_mbb.de.html",
        FAM = "https://www.me.hm.edu/aktuelles/schwarzes_brett/schwarzes_brett_fam_seite.de.html",
        LRM = "https://www.me.hm.edu/aktuelles/schwarzes_brett/schwarzes_brett_lrm_seite.de.html",
        MBM = "https://www.me.hm.edu/aktuelles/schwarzes_brett/schwarzes_brett_mbm_seite.de.html",
        FEM = "https://www.me.hm.edu/aktuelles/schwarzes_brett/schwarzes_brett_fem.de.html",
        TBM = "https://www.me.hm.edu/aktuelles/schwarzes_brett/schwarzes_brett_tbm.de.html",
        RSM = "https://www.me.hm.edu/aktuelles/schwarzes_brett/schwarzes_brett_rsm_seite.de.html",

    )

    def __init__(self):

        just_started = True
        old_posts = {}
        self.act_posts = {}

        print(*self.brett_links)


        for stud in [*self.brett_links]:
            old_posts[stud] = {
                'post-date':[],
                'title':[],
                'directed':[],
                'content':[]
                }


        print('scraper started...', flush=True)

        while True:

            posts_to_send_indexes = {}
            for stud in [*self.brett_links]:
                posts_to_send_indexes[stud] = []

            for stud in [*self.brett_links]:

                sauce = self.make_request(self.brett_links[stud])
                self.act_posts[stud] = self.objectise_posts(self.parse(sauce))
                new_post_count = 0

                for p, post in enumerate(self.act_posts[stud]['title']):

                    if post not in old_posts[stud]['title']:
                        new_post_count += 1
                        posts_to_send_indexes[stud].append(p)
                
                if not just_started:
                    self.send_mails(posts_to_send_indexes[stud], stud)


                old_posts[stud] = self.act_posts[stud]

                print("checked " + stud)


            just_started = False


            now = datetime.now(pytz.timezone('Europe/Amsterdam'))
            date_time = now.strftime("%d.%m.%Y_%H:%M:%S")

            print(date_time + ' waiting ...', flush=True)
            time.sleep(SLEEPTIME_HR*3600)    
        
    def objectise_posts(self, posts):

        obj_posts = {
            'post-date':[],
            'title':[],
            'directed':[],
            'content':[]
            }

        for post in posts:
            date = datetime.strptime(post.span.text, '[%d|%m|%y]').strftime('%d.%m.%y')
            obj_posts['post-date'].append(date)
            obj_posts['title'].append(post.strong.text)
            obj_posts['directed'].append(post.find_all('span', {'class': 'text-blau-studiengruppen'})[0].text)
            content = ''.join(str(v) for v in post.find_all('p'))
            obj_posts['content'].append(content)
        return obj_posts

    def send_mails(self, posts_to_send, stud):

        if len(posts_to_send) > 0:

            message_template = self.read_template(current_path() + 'mail_templates/message.html')
            post_template = self.read_template(current_path() + 'mail_templates/post_temp.html')
            contacts = self.get_contacts(current_path() + 'data/registered.csv')

            s = smtplib.SMTP(host='smtp.gmail.com', port=587)
            s.ehlo()
            s.starttls()
            s.login(MY_ADDRESS, PASSWORD)
            

            for contact in contacts:
                if contact[1] == stud:
                    msg = MIMEMultipart()       # create a message
                    postblock = ''
                    for p in posts_to_send:
                        postblock += post_template.substitute(TITLE=self.act_posts[stud]['title'][p],
                        DATE=self.act_posts[stud]['post-date'][p],
                        DIRECTED=self.act_posts[stud]['directed'][p],
                        CONTENT=self.act_posts[stud]['content'][p])

                    now = datetime.now(pytz.timezone('Europe/Amsterdam'))
                    date_time = now.strftime("%d.%m.%Y_%H:%M:%S")

                    # add in the actual person name to the message template
                    message = message_template.substitute(POST_COUNT=len(posts_to_send),
                        LINK=self.brett_links[stud],
                        POSTS=postblock,
                        SENDING_TIME=date_time,
                        STUD=stud)

                    msg['From']=MY_ADDRESS
                    msg['To']=contact[0]
                    msg['Subject']="Neues vom Schwarzen Brett"
                    # add in the message body
                    msg.attach(MIMEText(message, 'html'))
                    # send the message via the server set up earlier.
                    s.send_message(msg)
                    del msg
                    print(f'mail sent to {contact}', flush=True)

    def make_request(self, link):
        sauce = urllib.request.urlopen(link).read()
        return sauce

    def parse(self, sauce):
        soup = bs.BeautifulSoup(sauce, 'lxml')
        posts = soup.find_all('div', {'class': 'news-text'})
        return posts

    @staticmethod
    def read_template(filename):
        with open(filename, 'r', encoding='utf-8') as template_file:
            template_file_content = template_file.read()
        return Template(template_file_content)
        
    @staticmethod
    def get_contacts(filename) -> list:

        csv_list = []
        with open(filename, newline="") as file:
            reader = csv.reader(file, delimiter=";")
            for row in reader:
                csv_list.append(row)
        return csv_list
    

if __name__ == "__main__":
    logging.basicConfig(filename='mailer_exceptions.log',level=logging.DEBUG)
    while True:
        try:
            Scrape()
        except Exception as e:
            logging.error("Error occured \n \n \n",exc_info=e)
            print("Exception occured! waiting 60s")
            time.sleep(60)
            continue

