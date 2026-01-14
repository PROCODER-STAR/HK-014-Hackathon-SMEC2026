import streamlit as st
import lyricsgenius
import re
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import io

# Page configuration
st.set_page_config(
    page_title="Song Lyrics Word Cloud Generator",
    page_icon="🎵",
    layout="wide"
)

# Sidebar for user inputs
st.sidebar.header("⚙️ Settings")

# API Token input
api_token = st.sidebar.text_input(
    "Genius API Token",
    type="default",
    help="Enter your Genius API token. Get one at https://genius.com/api-clients"
)

# Number of songs slider
num_songs = st.sidebar.slider(
    "Number of Songs",
    min_value=1,
    max_value=10,
    value=5,
    help="Select how many top songs to fetch for the artist"
)

# Color palette dropdown
color_palette = st.sidebar.selectbox(
    "Color Palette",
    options=["magma", "viridis", "cool", "plasma", "inferno", "winter", "autumn"],
    help="Choose a color scheme for your word cloud"
)

# Main page
st.title("🎵 Song Lyrics Word Cloud Generator")
st.markdown("---")

# Artist search bar
artist_name = st.text_input(
    "Enter Artist Name",
    placeholder="e.g., Taylor Swift, The Beatles, Drake...",
    help="Type the name of the artist whose lyrics you want to visualize"
)

def clean_lyrics(lyrics):
    """Clean lyrics by removing Genius tags and common words."""
    if not lyrics:
        return ""
    
    # Remove Genius tags like [Chorus], [Verse], [Bridge], etc.
    lyrics = re.sub(r'\[.*?\]', '', lyrics)
    
    # Remove the word 'Embed'
    lyrics = re.sub(r'\bEmbed\b', '', lyrics, flags=re.IGNORECASE)
    
    # Remove extra whitespace
    lyrics = re.sub(r'\s+', ' ', lyrics)
    
    return lyrics.strip()

def generate_wordcloud(text, color_palette):
    """Generate a word cloud from text."""
    if not text:
        return None
    
    # Use built-in English stopwords and filter out common words
    stopwords = set(STOPWORDS)
    # Add any additional common words to filter
    stopwords.update(['embed', 'lyrics', 'genius'])
    
    # Create WordCloud with high resolution
    wordcloud = WordCloud(
        width=1200,
        height=800,
        background_color='white',
        max_words=200,
        relative_scaling=0.5,
        colormap=color_palette,
        collocations=False,
        stopwords=stopwords
    ).generate(text)
    
    return wordcloud

def main():
    if not api_token:
        st.warning("⚠️ Please enter your Genius API Token in the sidebar to get started.")
        return
    
    if not artist_name:
        st.info("👆 Enter an artist name above to generate a word cloud from their lyrics!")
        return
    
    # Initialize Genius API
    try:
        genius = lyricsgenius.Genius(api_token)
        genius.verbose = False  # Suppress verbose output
        genius.remove_section_headers = True  # Remove section headers automatically
    except Exception as e:
        st.error(f"❌ Error initializing Genius API: {str(e)}")
        return
    
    # Fetch artist and songs
    with st.spinner(f"🎤 Fetching lyrics for {artist_name}..."):
        try:
            # Search for the artist
            artist = genius.search_artist(artist_name, max_songs=num_songs, sort="popularity")
            
            if not artist or len(artist.songs) == 0:
                st.error(f"❌ No songs found for artist: {artist_name}")
                return
            
            # Collect lyrics from all songs
            all_lyrics = []
            songs_processed = []
            
            for song in artist.songs[:num_songs]:
                try:
                    # Fetch full song details
                    song_lyrics = song.lyrics
                    if song_lyrics:
                        cleaned = clean_lyrics(song_lyrics)
                        if cleaned:
                            all_lyrics.append(cleaned)
                            songs_processed.append(song.title)
                except Exception as e:
                    st.warning(f"⚠️ Could not fetch lyrics for '{song.title}': {str(e)}")
                    continue
            
            if not all_lyrics:
                st.error("❌ No lyrics were successfully fetched. Please try another artist.")
                return
            
            # Combine all lyrics
            combined_lyrics = " ".join(all_lyrics)
            
            # Generate word cloud
            with st.spinner("🎨 Generating word cloud..."):
                wordcloud = generate_wordcloud(combined_lyrics, color_palette)
            
            if wordcloud:
                # Create two columns
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("📊 Word Cloud")
                    # Display word cloud
                    fig, ax = plt.subplots(figsize=(12, 8))
                    ax.imshow(wordcloud, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig)
                    
                    # Download button
                    buf = io.BytesIO()
                    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', pad_inches=0)
                    buf.seek(0)
                    
                    st.download_button(
                        label="📥 Download Word Cloud as PNG",
                        data=buf,
                        file_name=f"{artist_name.replace(' ', '_')}_wordcloud.png",
                        mime="image/png"
                    )
                
                with col2:
                    st.subheader("📈 Statistics")
                    
                    # Calculate statistics
                    total_songs = len(songs_processed)
                    total_words = len(combined_lyrics.split())
                    unique_words = len(set(combined_lyrics.lower().split()))
                    
                    st.metric("Total Songs Found", total_songs)
                    st.metric("Total Words Processed", f"{total_words:,}")
                    st.metric("Unique Words", f"{unique_words:,}")
                    
                    st.markdown("---")
                    st.subheader("🎼 Songs Analyzed")
                    for i, song_title in enumerate(songs_processed, 1):
                        st.write(f"{i}. {song_title}")
            
        except Exception as e:
            st.error(f"❌ Error fetching artist data: {str(e)}")
            st.info("💡 Make sure:")
            st.info("• Your API token is correct")
            st.info("• The artist name is spelled correctly")
            st.info("• You have an internet connection")

if __name__ == "__main__":
    main()

