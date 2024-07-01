import os
import re
import requests
from bs4 import BeautifulSoup
import subprocess

# Function to scrape setlists
def scrape_setlists(base_url, date):
    url = f"{base_url}/setlists/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'lxml')
    
    setlist_data = {}
    setlist_section = soup.find('a', {'name': f'setlist-{date}'})
    if setlist_section:
        setlist_body = setlist_section.find_next('div', class_='setlist-body')
        songs = setlist_body.find_all('span', class_='setlist-songbox')
        setlist_data[date] = [song.get_text(strip=True) for song in songs]
    return setlist_data

# Function to extract chapters
def extract_chapters(file_name, output_file):
    try:
        result = subprocess.run(['mkvextract', 'chapters', file_name], capture_output=True, text=True)
        if result.stdout:
            with open(output_file, 'w') as file:
                file.write(result.stdout)
            print(f"Extracted chapters from {file_name} to {output_file}")
        if result.stderr:
            print(f"Error extracting chapters: {result.stderr}")
    except Exception as e:
        print(f"Failed to extract chapters from {file_name}: {e}")

import re

# Function to clean song names by removing unwanted characters and annotations
def clean_song_name(song):
    # Remove anything inside square brackets and any trailing commas or spaces
    cleaned_song = re.sub(r'\[.*?\]', '', song).strip(', ')
    return cleaned_song

# Function to replace ChapterUID with song names
def replace_chapters(setlist, xml_file):
    try:
        print(f"Setlist: {setlist}")  # Print the setlist for debugging
        # Clean the setlist song names
        cleaned_setlist = [clean_song_name(song) for song in setlist]
        print(f"Cleaned Setlist: {cleaned_setlist}")  # Print cleaned setlist for debugging

        with open(xml_file, 'r', encoding='utf-8') as file:
            xml_content = file.read()

        soup = BeautifulSoup(xml_content, 'xml')  # Use xml parser explicitly
        chapter_atoms = soup.find_all('ChapterAtom')

        print(f"Number of chapters in XML: {len(chapter_atoms)}")  # Print the number of chapters
        
        if len(chapter_atoms) != len(cleaned_setlist):
            raise ValueError("Number of chapters does not match number of songs in setlist")

        for chapter, song in zip(chapter_atoms, cleaned_setlist):
            chapter_display = chapter.find('ChapterDisplay')
            if not chapter_display:
                chapter_display = soup.new_tag('ChapterDisplay')
                chapter.append(chapter_display)
            
            chapter_string = chapter_display.find('ChapterString')
            if not chapter_string:
                chapter_string = soup.new_tag('ChapterString')
                chapter_display.append(chapter_string)
            chapter_string.string = song

            chapter_lang = chapter_display.find('ChapterLanguage')
            if not chapter_lang:
                chapter_lang = soup.new_tag('ChapterLanguage')
                chapter_display.append(chapter_lang)
            chapter_lang.string = 'eng'

            chap_lang_ietf = chapter_display.find('ChapLanguageIETF')
            if not chap_lang_ietf:
                chap_lang_ietf = soup.new_tag('ChapLanguageIETF')
                chapter_display.append(chap_lang_ietf)
            chap_lang_ietf.string = 'en'
        
        new_xml_content = str(soup)
        with open(xml_file, 'w', encoding='utf-8') as file:
            file.write(new_xml_content)
        print(f"Replaced chapters in {xml_file}")
    except Exception as e:
        print(f"Failed to replace chapters in {xml_file}: {e}")



# Function to update chapters in MKV files
def update_mkv_chapters(file_name, new_xml_file):
    try:
        result1 = subprocess.run(['mkvpropedit', file_name, '--chapters', ''], capture_output=True, text=True)
        print(f"Removed old chapters from {file_name}: {result1.stdout}")
        if result1.stderr:
            print(f"Error removing old chapters: {result1.stderr}")
            
        result2 = subprocess.run(['mkvpropedit', file_name, '--chapters', new_xml_file], capture_output=True, text=True)
        print(f"Added new chapters to {file_name} from {new_xml_file}: {result2.stdout}")
        if result2.stderr:
            print(f"Error adding new chapters: {result2.stderr}")
    except Exception as e:
        print(f"Failed to update chapters in {file_name}: {e}")

# Utility function to convert MM_DD_YY to YYYY-MM-DD
def convert_date_format(date_str):
    if re.match(r'\d{2}_\d{2}_\d{2}', date_str):  # Matches MM_DD_YY
        month, day, year = date_str.split('_')
        return f"20{year}-{month}-{day}"  # Convert to YYYY-MM-DD
    return date_str  # Return the original if already in YYYY-MM-DD

# Main function
def main(directory, base_url):
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist.")
        return

    for file_name in os.listdir(directory):
        if file_name.endswith('.mkv'):
            # Look for both date formats in the filename
            date_match = re.search(r'\d{4}-\d{2}-\d{2}', file_name) or re.search(r'\d{2}_\d{2}_\d{2}', file_name)
            if date_match:
                date = convert_date_format(date_match.group(0))
                print(f"Processing file {file_name} for date {date}")
                setlist = scrape_setlists(base_url, date).get(date)
                
                if setlist:
                    xml_file = os.path.join(directory, f"{file_name}.xml")
                    extract_chapters(os.path.join(directory, file_name), xml_file)
                    replace_chapters(setlist, xml_file)
                    update_mkv_chapters(os.path.join(directory, file_name), xml_file)
                else:
                    print(f"No setlist found for date {date}")
            else:
                print(f"No date found in file name {file_name}")

if __name__ == "__main__":
    directory = r'C:\Users\Neil\Downloads\Nugs-Downloader-main\Nugs downloads\test_scripts\video'
    base_url = 'https://elgoose.net'
    main(directory, base_url)
