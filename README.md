# TeleAdminConnect

A Python-based CLI tool for managing Telegram group administrators. Easily fetch, export, and interact with group admins.

## Features

- 🔍 Fetch admin lists from Telegram groups
- 📁 Load multiple groups from text file
- 💬 Send messages to group admins
- 📊 Export admin data in multiple formats (TXT, CSV, JSON)
- 👥 View group member statistics
- 🔄 Switch between multiple groups

## Installation

To install TeleAdminConnect, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/mesamirh/TeleAdminConnect.git
   ```
2. Navigate to the project directory:
   ```bash
   cd TeleAdminConnect
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Get your API credentials from [Telegram's API Development Tools](https://my.telegram.org/apps)

2. Create a .env file in the project root:
   ```bash
   API_ID=your_api_id
   API_HASH=your_api_hash
   ```

## Usage

1. To start using TeleAdminConnect, run the following command:

    ```bash
    python3 main.py
    ```

2. Available options:

   - Fetch admins from a single group
   - Load multiple groups from file
   - Send messages to admins
   - Export admin data
   - View group statistics

3. Group file format:
   ```bash
   @group1
   @group2
   group3
   ```

## Requirements

- Python 3.7+
- Pyrogram
- python-dotenv
- rich