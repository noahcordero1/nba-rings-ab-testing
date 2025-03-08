import streamlit as st
# Set page config must be the first Streamlit command
st.set_page_config(
    page_title="NBA Championship Rings A/B Test",
    page_icon="🏀",
    layout="wide"
)

# Import other libraries
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import random
import time
from datetime import datetime
import numpy as np

# Custom CSS for improved styling
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background-color: #f8f9fa;
        padding: 10px;
    }
    
    /* Header and title styling */
    h1 {
        color: #17408B;
        font-size: 36px !important;
        padding-bottom: 10px;
        border-bottom: 2px solid #C9082A;
        margin-bottom: 20px;
    }
    
    h2, h3 {
        color: #17408B;
        margin-top: 1rem;
    }
    
    /* Button styling */
    .stButton button {
        background-color: #17408B;
        color: white;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        border: none;
        transition: all 0.3s;
    }
    
    .stButton button:hover {
        background-color: #C9082A;
        color: white;
    }
    
    /* Timer styling */
    .timer-container {
        background-color: #f1f3f4;
        padding: 10px;
        border-radius: 10px;
        border-left: 5px solid #17408B;
        margin-bottom: 20px;
    }
    
    .timer {
        font-size: 24px;
        font-weight: bold;
        color: #17408B;
    }
    
    /* Chart container styling */
    .chart-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    
    /* Player button customization */
    .player-button button {
        margin: 5px;
        min-height: 60px;
        width: 100%;
        font-size: 16px;
        text-align: center;
    }
    
    /* Success and error message styling */
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 10px 15px;
        border-radius: 5px;
        border-left: 5px solid #155724;
        margin: 10px 0;
    }
    
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 10px 15px;
        border-radius: 5px;
        border-left: 5px solid #721c24;
        margin: 10px 0;
    }
    
    /* Result tables styling */
    .dataframe {
        width: 100%;
        border-collapse: collapse;
    }
    
    .dataframe th {
        background-color: #17408B;
        color: white;
        padding: 8px;
        text-align: left;
    }
    
    .dataframe td {
        padding: 8px;
        border-bottom: 1px solid #ddd;
    }
    
    .dataframe tr:nth-child(even) {
        background-color: #f2f2f2;
    }
    
    /* Caption styling */
    .caption {
        font-size: 12px;
        color: #6c757d;
        font-style: italic;
    }
    
    /* NBA theme colors */
    .nba-blue {
        color: #17408B;
    }
    
    .nba-red {
        color: #C9082A;
    }
    
    /* Instructions styling */
    .instructions {
        background-color: #e9ecef;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "chart_type" not in st.session_state:
    st.session_state.chart_type = None
if "chart_shown" not in st.session_state:
    st.session_state.chart_shown = False
if "current_time" not in st.session_state:
    st.session_state.current_time = 0
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d%H%M%S")
    st.session_state.results = []
if "correct_answer" not in st.session_state:
    st.session_state.correct_answer = False
if "feedback_message" not in st.session_state:
    st.session_state.feedback_message = ""

# Function to update timer
def update_timer():
    if st.session_state.start_time and st.session_state.chart_shown and not st.session_state.correct_answer:
        st.session_state.current_time = time.time() - st.session_state.start_time
        st.rerun()

# Main page layout
col_header1, col_header2 = st.columns([3, 1])

with col_header1:
    st.title("🏀 NBA Championship Rings Analysis")
    st.markdown('<div class="instructions">This experiment tests which chart type better helps users identify the NBA player with the most championship rings.</div>', unsafe_allow_html=True)

with col_header2:
    st.markdown('<br>', unsafe_allow_html=True)
    # Session info and controls in the sidebar instead
    st.sidebar.markdown(f"<div class='caption'>Session ID: {st.session_state.session_id}</div>", unsafe_allow_html=True)
    
    if st.sidebar.button("🔄 Start New Session"):
        st.session_state.session_id = datetime.now().strftime("%Y%m%d%H%M%S")
        st.session_state.results = []
        st.session_state.chart_shown = False
        st.session_state.correct_answer = False
        st.rerun()

# Create main containers
question_container = st.container()
chart_container = st.container()
answer_container = st.container()
feedback_container = st.container()
results_container = st.container()

# Create a connection object
conn = st.connection("gsheets", type=GSheetsConnection)

# Load the data from Google Sheets
try:
    # First try to access directly from the secrets structure used in Streamlit Cloud
    if "connections" in st.secrets and "gsheets" in st.secrets["connections"] and "spreadsheet" in st.secrets["connections"]["gsheets"]:
        spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        df = conn.read(spreadsheet=spreadsheet_url)
    # Then try the flatter structure often used locally
    elif "spreadsheet" in st.secrets:
        df = conn.read(spreadsheet=st.secrets["spreadsheet"])
    # If neither is found, show a helpful error
    else:
        st.error("Google Sheet URL not found in secrets. Please check your configuration.")
        st.stop()
except Exception as e:
    st.error(f"Error connecting to Google Sheets: {e}")
    st.stop()


# Make sure rings column is numeric
df["Rings"] = pd.to_numeric(df["Rings"])

# Display the business question
with question_container:
    st.header("Question")
    st.markdown('<div style="font-size: 20px; font-weight: bold; margin-bottom: 20px;">Which NBA player has won the most championship rings?</div>', unsafe_allow_html=True)
    
    # Button to show a random chart
    if not st.session_state.chart_shown:
        st.markdown('<br>', unsafe_allow_html=True)
        if st.button("🏁 Start the Test", key="start_button"):
            # Record start time
            st.session_state.start_time = time.time()
            st.session_state.current_time = 0
            st.session_state.correct_answer = False
            st.session_state.feedback_message = ""
            
            # Randomly select chart A or B
            st.session_state.chart_type = random.choice(["A", "B"])
            st.session_state.chart_shown = True
            
            # Force refresh
            st.rerun()

# If a chart is shown, display it and player selection buttons
if st.session_state.chart_shown:
    # Timer display
    st.markdown(f"""
    <div class="timer-container">
        <div class="timer">⏱️ Time: {st.session_state.current_time:.1f} seconds</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sort data by ring count
    sorted_df = df.sort_values(by="Rings", ascending=False).head(10)
    correct_player = sorted_df.iloc[0]["Player"]
    
    with chart_container:
        st.markdown(f'<h3>Chart {st.session_state.chart_type}</h3>', unsafe_allow_html=True)
        
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        # Display the appropriate chart with NBA theme colors
        if st.session_state.chart_type == "A":
            # Chart A: Bar chart
            fig, ax = plt.subplots(figsize=(12, 7))
            bar_plot = sns.barplot(x="Rings", y="Player", data=sorted_df, ax=ax, color="#17408B")
            plt.title("NBA Players by Championship Rings", fontsize=16, fontweight='bold')
            plt.xlabel("Number of Championship Rings", fontsize=12)
            plt.ylabel("Player", fontsize=12)
            ax.tick_params(axis='both', labelsize=11)
            st.pyplot(fig)
        else:
            # Chart B: Single stacked bar chart with player names in the middle
            fig, ax = plt.subplots(figsize=(12, 7))
            
            # Prepare data for stacked bar
            # Convert player names to a numeric value for stacking
            players = sorted_df["Player"].tolist()
            rings = sorted_df["Rings"].tolist()
            
            # Create a single stacked bar
            bottom = 0
            colors = plt.cm.Blues(np.linspace(0.4, 0.8, len(players)))[::-1]  # Reverse to have darkest color at top
            
            # Draw each segment separately to add text
            for i, (player, ring, color) in enumerate(zip(players, rings, colors)):
                p = ax.bar(0, ring, bottom=bottom, color=color, width=0.7)
                
                # Add player name in the middle of each segment
                middle_y = bottom + ring/2
                ax.text(0, middle_y, f"{player} ({ring})", 
                       ha='center', va='center', color='white', fontweight='bold',
                       fontsize=10 if ring > 5 else 9)  # Smaller text for smaller segments
                
                bottom += ring
            
            # Remove x-axis labels and ticks
            ax.set_xticks([])
            ax.set_xticklabels([])
            
            # Set the y-axis limits and ticks
            ax.set_ylim(0, bottom)
            max_rings = int(bottom)
            ax.set_yticks(range(0, max_rings + 1, 5))
            
            # Clean up the plot
            plt.title("NBA Players by Championship Rings (Stacked)", fontsize=16, fontweight='bold')
            plt.ylabel("Number of Championship Rings", fontsize=12)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            
            st.pyplot(fig)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with answer_container:
        if not st.session_state.correct_answer:
            st.subheader("Who has the most championship rings?")
            
            # Get list of players
            top_players = sorted_df["Player"].tolist()
            
            # Create columns for layout - 3 columns for desktop, adjust as needed
            cols = st.columns(3)
            
            # Create buttons for each player with improved styling
            for i, player in enumerate(top_players):
                col_idx = i % 3
                with cols[col_idx]:
                    st.markdown('<div class="player-button">', unsafe_allow_html=True)
                    if st.button(player, key=f"player_{i}"):
                        # Calculate time taken
                        end_time = time.time()
                        time_taken = end_time - st.session_state.start_time
                        
                        if player == correct_player:
                            # Save result with current time
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            st.session_state.results.append({
                                "chart_type": st.session_state.chart_type,
                                "time": time_taken,
                                "timestamp": timestamp
                            })
                            
                            # Set feedback message
                            st.session_state.feedback_message = f"✅ Correct! You identified {player} as having the most rings in {time_taken:.2f} seconds using Chart {st.session_state.chart_type}."
                            st.session_state.correct_answer = True
                        else:
                            # Set error message but keep timer running
                            st.session_state.feedback_message = f"❌ Incorrect. {player} does not have the most championship rings. Try again!"
                        
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display feedback message
    if st.session_state.feedback_message:
        with feedback_container:
            if "Correct!" in st.session_state.feedback_message:
                st.markdown(f'<div class="success-message">{st.session_state.feedback_message}</div>', unsafe_allow_html=True)
                
                # Show button to try again
                if st.button("Try Another Chart", key="try_again"):
                    st.session_state.chart_shown = False
                    st.session_state.chart_type = None
                    st.session_state.start_time = None
                    st.session_state.correct_answer = False
                    st.session_state.feedback_message = ""
                    st.rerun()
            else:
                st.markdown(f'<div class="error-message">{st.session_state.feedback_message}</div>', unsafe_allow_html=True)
    
    # Update the timer if still answering
    if not st.session_state.correct_answer:
        time.sleep(0.1)  # Small delay
        update_timer()

# Display all results from the current session in a collapsible expander
if st.session_state.results:
    with results_container:
        with st.expander("📊 View Test Results", expanded=False):
            st.header("Current Session Results")
            
            # Convert to DataFrame
            results_df = pd.DataFrame(st.session_state.results)
            
            # Display all individual results
            st.subheader("Individual Test Results")
            individual_results = results_df[["chart_type", "time"]].copy()
            if "timestamp" in results_df.columns:
                individual_results = results_df[["chart_type", "time", "timestamp"]].copy()
                individual_results.columns = ["Chart Type", "Time (seconds)", "Time of Test"]
            else:
                individual_results.columns = ["Chart Type", "Time (seconds)"]
            
            individual_results["Time (seconds)"] = individual_results["Time (seconds)"].round(2)
            
            # Sort by timestamp if available
            if "Time of Test" in individual_results.columns:
                individual_results = individual_results.sort_values("Time of Test", ascending=False)
            
            st.table(individual_results)
            
            # Only show summary if we have enough data
            if len(results_df) >= 2:
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    # Group by chart type for average times
                    st.subheader("Average Times by Chart Type")
                    summary = results_df.groupby("chart_type")["time"].agg(['mean', 'count', 'min', 'max']).reset_index()
                    summary.columns = ["Chart Type", "Average Time (sec)", "Number of Tests", "Min Time (sec)", "Max Time (sec)"]
                    
                    # Round time values
                    for col in summary.columns[1:]:
                        if col != "Number of Tests":
                            summary[col] = summary[col].round(2)
                    
                    st.table(summary)
                
                with col2:
                    # Visualization of results
                    st.subheader("Average Time by Chart Type")
                    fig, ax = plt.subplots(figsize=(8, 5))
                    
                    # Use NBA colors
                    colors = ["#17408B", "#C9082A"] if len(summary) > 1 else ["#17408B"]
                    
                    # Create a simpler bar chart using matplotlib 
                    chart_types = summary["Chart Type"].tolist()
                    avg_times = summary["Average Time (sec)"].tolist()
                    
                    bars = ax.bar(chart_types, avg_times, color=colors)
                    
                    # Add data labels on bars
                    for bar in bars:
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                                f"{height:.2f}s",
                                ha='center', va='bottom', fontweight='bold')
                    
                    plt.title("Average Answer Time by Chart Type", fontsize=14, fontweight='bold')
                    plt.xlabel("Chart Type", fontsize=12)
                    plt.ylabel("Time (seconds)", fontsize=12)
                    plt.ylim(0, max(avg_times) * 1.2)  # Add some space above the bars for labels
                    st.pyplot(fig)
            
            # Button to reset session results
            if st.button("🗑️ Reset Results", key="reset_results"):
                st.session_state.results = []
                st.rerun()

# Add information about the experiment in the sidebar
st.sidebar.markdown("## About this Test")
st.sidebar.markdown("""
This experiment compares two different chart types to determine which one helps users more effectively identify the NBA player with the most championship rings.

**Chart A**: Traditional bar chart  
**Chart B**: Single stacked bar chart

The app measures how quickly you can find the correct answer with each chart type.
""")

# Footer
st.markdown("---")
st.markdown('<div class="caption">NBA Championship Rings Analysis | A/B Testing Tool | Data from Google Sheets</div>', unsafe_allow_html=True)
