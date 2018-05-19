from urllib.request import urlopen
from bs4 import BeautifulSoup
import ssl
import re

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "http://www.konagrill.com/menu/dinner"
html = urlopen(url, context=ctx).read()
soup = BeautifulSoup(html, "html.parser")

item_cats = soup('div', attrs={'class':'category'})
item_cats2 = soup('ul', attrs={'class':'menu-items'})

menu_dict = dict()
counter = 0;

for cat in item_cats2:
    category = item_cats[counter].contents[0]
    items = cat.findAll('div', attrs={'class' : 'name'})
    descs = cat.findAll('div', attrs={'class' : 'description'})
    counter = counter + 1
    item_desc = dict()
    for i in range(len(items)):
        item_desc[items[i].contents[0]]=descs[i].contents[0]
    menu_dict[category]=item_desc

print('')
for category in menu_dict:
    print(category)
print('')
while True:
    cat_key = input('Enter menu category to view items: ')
    try:
        for item in menu_dict[cat_key]:
            print('')
            print(item)
            print('\t',menu_dict[cat_key][item],'\n')
    except:
        print('Enter a category from the list:\n')
        for category in menu_dict:
            print(category)
