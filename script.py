from bs4 import BeautifulSoup as bs
from datetime import datetime
from selenium import webdriver # pip install selenium
from webdriver_manager.chrome import ChromeDriverManager # pip install webdriver-manager
from time import sleep
import re
import csv

driver = webdriver.Chrome(ChromeDriverManager().install()) #might take a while on first time
baseUrl = "https://www.propertyguru.com.sg"
knownBldType=["Apartment","Condominium","Walk-up Apartment","Cluster House","Executive Condominum","Detached House","Semi-Detached House","Corner Terrace","Bungalow House","Good Class Bungalow","Shophouse","Land Only","Town House","Terraced House","HDB Flat"]
#D01-D28
for d in range(1,29):
    print(f"Scanning D{d:02d}")
    url = f"https://www.propertyguru.com.sg/property-for-rent?market=residential&listing_type=rent&district_code[]=D{d:02d}&search=true"
    bldList = []
    while(True):
        driver.get(url)
        souped = bs(driver.page_source,"html.parser")
        if souped.find("div",{"class":re.compile("error txtC")})!=None:
            #print("Whoops!!! We Are Detected!")
            driver.delete_all_cookies()
            continue
        next_page = souped.find("li",{"class":re.compile("pagination-next")})

        #If reached end of the page or wrong page
        if next_page is None or next_page.a is None: break

        # Manual way, it will be better if get all objects in div listing-card class
        bldDivList = souped.find_all("div",{"class":"listing-card"})
        
        
        for n,bldDiv in enumerate(bldDivList):
            if bldDiv is None: continue
            innerSoup = bs(str(bldDiv),'html.parser')

            bldName    = innerSoup.find("h3",{"class":"h4 ellipsis text-transform-none"}).a.text
            bldLink    = innerSoup.find("h3",{"class":"h4 ellipsis text-transform-none"}).a['href']

            bldType    = "NA"
            bldYear    = "NA"
            bldFurnish = "NA"
            bldTags = innerSoup.find("ul",{"class":"listing-property-type"}).find_all('li') # ul li list
            for bldTag in bldTags: 
                bldTagDet = bldTag.span.text
                #if bldTagDet in knownBldType: bldType = bldTagDet
                if 'Built: ' in bldTagDet: bldYear = bldTagDet.replace('Built: ',"")
                elif 'Furnished' in bldTagDet: bldFurnish = bldTagDet
                else: bldType = bldTagDet

            bldAddress = innerSoup.find("span",{"itemprop":"streetAddress"})
            if bldAddress: bldAddress = bldAddress.text
            else: bldAddress = 'NA'

            bldPrice   = innerSoup.find("span",{"class":"price"})
            if bldPrice: 
                bldPrice = bldPrice.text
                bldPeriod  = innerSoup.find("span",{"class":"period"}).text
            else: 
                bldPrice = 'NA'
                bldPeriod = ''
            

            isStudio = True if len(innerSoup.find_all("span",{"class":"studio"}))>0 else False
            if isStudio:
                bldBedRoom = "Studio"
                bldToilet = "NO"
            else:
                bldBedRoom = innerSoup.find("span",{"class":"bed"}) #If studio no toilet detail
                if bldBedRoom: bldBedRoom = bldBedRoom.text
                else: bldBedRoom = 'NA'
                bldToilet  = innerSoup.find("span",{"class":"bath"})
                if bldToilet: bldToilet=bldToilet.text
                else: bldToilet = 'NA'

            bldSize    = innerSoup.find("li",{"class":"listing-floorarea pull-left"}).text
            print(f"Found item/bld {bldName} at district D{d:02d}")
            #if bldName.a.text not in bldList:
            now = datetime.now()
            date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
            bldList.append({
                'BldLink'     :bldLink,
                'BldName'     :bldName, #or listing name
                'BldAddress'  :bldAddress,
                'BldSize'     :bldSize,
                'BldType'     :bldType,
                'BldBuilt'    :bldYear,
                'BldFurnish'  :bldFurnish,
                'BldBedRoomCount' :bldBedRoom,
                'BldToiletCount'  :bldToilet,
                'BldRentFee'      :bldPrice,
                'BldRentFeePeriod':bldPeriod,
                'timestamp':date_time
            })
        sleep(1) # Prevent cloudflare detection
        url=baseUrl+next_page.a['href']
    #print(bldList)
    if len(bldList)>0:
        with open(f'data\PropGuru_raw_D{d:02d}.csv', 'w' , encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile,fieldnames=bldList[0].keys())
            writer.writeheader()
            writer.writerows(bldList)
    print(f"District D{d:02d} stored in csv!")
    break