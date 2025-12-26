def generate_title_and_hashtags(original_title):
    """
    Simple title + hashtags generator.
    """
    hook = original_title.split("|")[0][:70]
    hashtags = "#fyp #viral #shorts #reels #tiktok"
    return f"{hook} 👀", hashtags
