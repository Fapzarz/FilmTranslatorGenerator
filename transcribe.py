import whisper
import pprint # For pretty printing the output

# 1. Load the Whisper model
# Models: "tiny", "base", "small", "medium", "large"
# Use "base.en" or "small.en" etc. for English-only models
model = whisper.load_model("base")
print("Whisper model loaded.")

# 2. Define the path to your video file
# !!! IMPORTANT: Replace this with the actual path to your video file !!!
video_path = "YOUR_VIDEO_FILE.mp4"

# 3. Transcribe the audio from the video file
# Set fp16=False if you don't have a CUDA-enabled GPU or run into issues
print(f"Starting transcription for: {video_path}")
try:
    # The 'verbose=True' option shows progress and detected language
    result = model.transcribe(video_path, verbose=True, fp16=False)

    # 4. Print the results (including segments with timestamps)
    print("\nTranscription Result:")
    # pprint.pprint(result) # Uncomment this to see the full raw result structure

    print("\nDetected language:", result["language"])

    print("\nSegments with Timestamps:")
    for segment in result["segments"]:
        start_time = segment['start']
        end_time = segment['end']
        text = segment['text']
        print(f"[{start_time:.2f}s -> {end_time:.2f}s] {text}")

except FileNotFoundError:
    print(f"\nError: Video file not found at '{video_path}'.")
    print("Please make sure the path is correct and the file exists.")
except Exception as e:
    print(f"\nAn error occurred during transcription: {e}")

print("\nTranscription finished.")
