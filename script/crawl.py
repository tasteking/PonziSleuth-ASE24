"""
    crwal etherscan verified contracts
    <a class="me-1" data-bs-trigger="hover" data-bs-toggle="tooltip" href="/address/0x6894448f65B828E7ff96674ad7372dD061de41A4#code"><span class="d-flex align-items-center"><i class="far fa-file-alt text-secondary me-1"></i> <span data-highlight-target="0x6894448f65B828E7ff96674ad7372dD061de41A4">0x6894448f...061de41A4</span></span></a>
    
    For the actual contract source codes use the api endpoints at https://docs.etherscan.io/api-endpoints/contracts
"""

import bs4
import time
import datetime
import requests

def crawl_address(url: str):
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0'
    }
    addresses = []

    for page in range(1, 21):
        complete_url = url + str(page) + '?filter=solc'
        while(True):
            try:
                response = requests.get(url=complete_url, headers=header).text
                break

            except Exception as e:
                print('Error: ', e)
                time.sleep(1)
                continue

        soup = bs4.BeautifulSoup(response, 'html.parser')
        addresses.extend([element['data-highlight-target'] for element in soup.find_all('span', {'data-highlight-target': True})])

    return addresses

def crawl_date(date: str):
    # addresses
    today = str(datetime.date.today().month) + '.' + str(datetime.date.today().day)
    if date == today:
        return crawl_address('https://etherscan.io/contractsVerified/')
    else:
        return []

if __name__ == '__main__':
    print(crawl_address('https://etherscan.io/contractsVerified/'))