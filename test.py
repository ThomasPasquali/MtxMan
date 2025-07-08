
import re
from bs4 import BeautifulSoup
import requests

name = 'ash219'
group = 'HB'
full_name = f"{group}/{name}"
url = f"https://sparse.tamu.edu/{full_name}"

try:
    response = requests.get(url)
    response.raise_for_status()
except Exception as e:
    pass

soup = BeautifulSoup(response.text, "html.parser")

def extract_text_between(th_text):
    for th in soup.find_all("th"):
        if th_text.strip().lower() == th.get_text(strip=True).split("\n")[0].strip().lower():
            td = th.find_next("td")
            if td:
                return td.get_text(strip=True)
    return ""


def extract_image_link():
    div = soup.find("div", class_="carousel-item active")
    if div and (a_tag := div.find("a", href=True)):
        return a_tag["href"]
    return ""

name_field = extract_text_between("Name")
group_field = extract_text_between("Group")
matrix_id = extract_text_between("Matrix ID")
num_rows = int(re.sub(",", "", extract_text_between("Num Rows")) or 0)
num_cols = int(re.sub(",", "", extract_text_between("Num Cols")) or 0)
nonzeros = int(re.sub(",", "", extract_text_between("Nonzeros")) or 0)
spr = nonzeros / (num_rows * num_cols) if num_rows and num_cols else 0
image_link = extract_image_link()

print(name_field)
print(num_rows)