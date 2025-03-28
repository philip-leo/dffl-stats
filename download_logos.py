import pandas as pd
import os
import requests
import instaloader
from urllib.parse import urlparse
import time

def get_instagram_username(url):
    """Extract Instagram username from URL."""
    if not url or pd.isna(url):
        return None
    path = urlparse(url).path
    return path.strip('/').split('/')[-1]

def download_profile_pic(username, save_path):
    """Download profile picture using instaloader."""
    if not username:
        return False
    
    try:
        L = instaloader.Instaloader()
        # Download the profile picture
        profile = instaloader.Profile.from_username(L.context, username)
        response = requests.get(profile.profile_pic_url)
        
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ Successfully downloaded logo for {username}")
            return True
    except Exception as e:
        print(f"❌ Error downloading logo for {username}: {str(e)}")
    return False

def main():
    # Create logos directory if it doesn't exist
    if not os.path.exists('logos'):
        os.makedirs('logos')

    # Read team info CSV
    df = pd.read_csv('team_info.csv')
    
    # Process each team
    for _, row in df.iterrows():
        team_name = row['Team']
        logo_path = row['LogoPath']
        instagram_url = row['InstagramURL']
        
        # Skip if logo already exists
        if os.path.exists(logo_path):
            print(f"⏩ Logo already exists for {team_name}")
            continue
            
        # Get Instagram username and download profile picture
        username = get_instagram_username(instagram_url)
        if username:
            success = download_profile_pic(username, logo_path)
            if not success:
                print(f"⚠️ Could not download logo for {team_name}")
        else:
            print(f"⚠️ No Instagram URL for {team_name}")
        
        # Add a small delay to avoid rate limiting
        time.sleep(1)

if __name__ == "__main__":
    print("Starting logo download process...")
    main()
    print("\nLogo download process completed!") 