# Brief

Brief is a desktop application that distills non-fiction books (epub and PDF formats) into concise overviews for learning purposes. It uses local AI to summarize content efficiently, handling large books through chunking to avoid token limits.

## Features

- **Drop-and-Drop Upload**: Easily add epub or PDF files via drag-and-drop.
- **AI Summarization**: Leverages Hugging Face transformers for local, privacy-focused summarization.
- **Library View**: Browse and read summaries in a grid layout.
- **Token Management**: Splits large texts into chunks for accurate, hierarchical summaries.

## Tech Stack

- **Language**: Python
- **UI**: PyQt6
- **Parsing**: ebooklib (epub), pypdf (PDF)
- **AI**: Hugging Face transformers (e.g., BART model)
- **Packaging**: PyInstaller

## Installation

1. Clone the repo: `git clone https://github.com/isfopo/Brief.git`
2. Run the setup script: `./setup.sh` (or `bash setup.sh`)
3. Activate the virtual environment: `source env/bin/activate`
4. Run: `python main.py`

## Usage

- Launch the app.
- Drag and drop a book file.
- View the generated summary in the library.

## Troubleshooting

### Slow Startup or Hanging on Summarization

The app uses a large AI model (`facebook/bart-large-cnn`) for summarization. If startup is slow or summarization hangs:

1. **Model Pre-downloading**: The setup script automatically downloads the model. If you skipped this, run:
   ```bash
   source env/bin/activate
   python -c "from services.summarizer import preload_model; preload_model()"
   ```

2. **Force CPU Usage**: The app is configured to use CPU only to avoid GPU issues. If you still experience problems, you can use a smaller model for testing:
   ```bash
   USE_SMALL_MODEL=true python main.py
   ```

3. **Environment Variables**:
   - `SUMMARIZER_MODEL`: Override the default model (default: `facebook/bart-large-cnn`)
   - `USE_SMALL_MODEL`: Use smaller model for testing (default: `false`)
   - `MAX_MODEL_TOKENS`: Maximum tokens per chunk (default: `1024`)

4. **Common Issues**:
   - **MPS/GPU Issues**: On macOS, MPS acceleration can cause slowdowns. The app forces CPU usage.
   - **Network Issues**: Model downloads require internet. Ensure stable connection during setup.
   - **Memory Issues**: Large books require significant RAM. Monitor system resources.

## Contributing

See issues for epics and tasks. Use the develop branch for PRs.

## License

MIT