import requests
from bs4 import BeautifulSoup
import json
import os
import tkinter as tk
from tkinter import messagebox

# Mapping set identifiers to full names
SET_NAME_MAPPING = {
    "mythical_island": "Mythical Island (A1a)",
    "genetic_apex": "Genetic Apex (A1)",
    "space_time_smackdown": "Space-Time Smackdown (A2)",
    "triumphant_light": "Triumphant Light (A2a)"
}

def load_card_database():
    #Load the combined JSON file and create a lookup dictionary
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Get script directory
    json_path = os.path.join(script_dir, "card_data.json")  # Full path to JSON

    card_db = {}
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            cards = json.load(f)
            for card in cards:
                card_number = card["id"].split("-")[-1]  
                lookup_key = f"{card['set']}-{card_number}"
                card_db[lookup_key] = (card["name"], card_number)
    except FileNotFoundError:
        print(f"Error: {json_path} not found!")  # Debugging print

    return card_db

CARD_DATABASE = load_card_database()

def get_cards(url):
    #Extracts wanted and tradable cards from a given profile URL

    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to fetch page content!")
        return None, None

    soup = BeautifulSoup(response.text, 'html.parser')

    def extract_cards(section_class):
        wrapper = soup.find("div", class_="cards-wrapper")
        if not wrapper:
            print("No card wrapper found!")  
            return set()

        section = wrapper.find("div", class_=section_class)
        if not section:
            print(f"Section '{section_class}' not found within wrapper!")
            return set()

        cards_section = section.find("div", class_="cards")
        if not cards_section:
            print(f"Cards section not found inside '{section_class}'!")
            return set()

        cards = set()
        for img in cards_section.find_all("img"):
            src_parts = img["src"].split("/")
            if len(src_parts) >= 3:
                pack_key = src_parts[-3]
                card_number = src_parts[-1].replace(".webp", "")
                
                if pack_key in SET_NAME_MAPPING:
                    full_set_name = SET_NAME_MAPPING[pack_key]
                    card_number = card_number.zfill(3)  # Ensures three digits (e.g., "8" -> "008", "80" -> "080")
                    lookup_key = f"{full_set_name}-{card_number}"
                    card_name, actual_card_number = CARD_DATABASE.get(lookup_key, ("Unknown", card_number))
                    cards.add(f"{card_name} ({full_set_name}-{actual_card_number})")

        return cards

    wanted_cards = extract_cards("wanted")
    tradable_cards = extract_cards("tradable")

    return wanted_cards, tradable_cards

def find_matches():
    my_url = my_url_entry.get()
    other_url = other_url_entry.get()
    if not my_url or not other_url:
        messagebox.showerror("Error", "Both URLs must be provided!")
        return
    
    my_wanted, my_tradeable = get_cards(my_url)
    other_wanted, other_tradeable = get_cards(other_url)
    
    if not my_wanted or not my_tradeable or not other_wanted or not other_tradeable:
        messagebox.showerror("Error", "Could not retrieve all card lists.")
        return

    you_receive = my_wanted.intersection(other_tradeable)
    they_receive = other_wanted.intersection(my_tradeable)

    result_text.set("=== Trade Matches ===\n")
    result_text.set(result_text.get() + "You can receive from them:\n" + "\n".join(you_receive if you_receive else ["None"]) + "\n\n")
    result_text.set(result_text.get() + "They can receive from you:\n" + "\n".join(they_receive if they_receive else ["None"]))
    
    with open("user_profile.txt", "w") as f:
        f.write(my_url)

def load_saved_profile():
    #Load the saved user profile URL if available
    if os.path.exists("user_profile.txt"):
        with open("user_profile.txt", "r") as f:
            return f.read().strip()
    return ""

# UI Setup
root = tk.Tk()
root.title("Pokémon TCG Pocket Trade Matcher")

tk.Label(root, text="Your Profile URL:").grid(row=0, column=0)
my_url_entry = tk.Entry(root, width=50)
my_url_entry.grid(row=0, column=1)
my_url_entry.insert(0, load_saved_profile())

tk.Label(root, text="Other User's Profile URL:").grid(row=1, column=0)
other_url_entry = tk.Entry(root, width=50)
other_url_entry.grid(row=1, column=1)

tk.Button(root, text="Find Matches", command=find_matches).grid(row=2, columnspan=2)

result_text = tk.StringVar()
result_label = tk.Label(root, textvariable=result_text, justify="left", anchor="w")
result_label.grid(row=3, columnspan=2, sticky="w")

root.mainloop()
