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

## Contributing

See issues for epics and tasks. Use the develop branch for PRs.

## License

MIT