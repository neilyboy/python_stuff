import requests
from bs4 import BeautifulSoup

def scrape_goose_setlists(url):
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to retrieve the webpage.")
        return
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    shows = soup.find_all('section', class_='setlist setlist-class')
    
    with open('goose_2024_tour_setlists.txt', 'w') as file:
        for show in shows:
            header = show.find('div', class_='setlist-header')
            if header:
                title_elements = header.find_all('a')
                title = ', '.join([elem.text.strip() for elem in title_elements])
                file.write(title + '\n')
                
                setlist_body = show.find('div', class_='setlist-body')
                if setlist_body:
                    paragraphs = setlist_body.find_all('p')
                    for paragraph in paragraphs:
                        set_title = paragraph.find('b', class_='setlabel')
                        if set_title:
                            file.write(set_title.text.strip() + ':\n')
                        
                        song_boxes = paragraph.find_all('span', class_='setlist-songbox')
                        for song_box in song_boxes:
                            song = song_box.find('a')
                            if song:
                                file.write(f"- {song.text.strip()}")
                                
                                # Include any additional information like footnotes
                                sup = song_box.find('sup')
                                if sup:
                                    file.write(f" {sup.text.strip()}")
                                file.write('\n')
                
                # Add Coach's Notes and Show Notes
                setlist_meta = show.find('span', class_='showmeta setlist-meta')
                if setlist_meta:
                    coach_notes = setlist_meta.find('p', class_='setlist-footnotes')
                    if coach_notes:
                        file.write("\nCoach's Notes:\n")
                        notes = coach_notes.get_text(separator="\n").strip()
                        file.write(notes + '\n')
                    
                    show_notes = setlist_meta.find('p', class_='shownotes-label')
                    if show_notes:
                        file.write("\nShow Notes:\n")
                        notes = show_notes.find_next_sibling('p').get_text(separator="\n").strip()
                        file.write(notes + '\n')
                
                # Add a line break between shows
                file.write('\n\n')

# URL of the webpage to scrape
url = 'https://elgoose.net/setlists/goose'
scrape_goose_setlists(url)
