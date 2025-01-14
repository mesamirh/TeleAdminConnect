import asyncio
import logging
import os
from dotenv import load_dotenv
from pyrogram import Client, enums
from rich.console import Console
from rich.live import Live
from rich.prompt import Prompt
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.application import create_app_session
from prompt_toolkit.patch_stdout import patch_stdout

# Configure console
console = Console()

# Load environment variables
load_dotenv()
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')

def check_api_credentials():
    """Validate API credentials from .env file"""
    
    if not os.path.exists('.env'):
        console.print(Panel(
            "[bold red]ERROR: .env file not found![/bold red]\n\n"
            "[yellow]Please create a .env file with the following content:[/yellow]\n"
            "API_ID=your_api_id\n"
            "API_HASH=your_api_hash\n\n"
            "[blue]Get your API credentials from:[/blue]\n"
            "https://my.telegram.org/apps",
            title="[bold red]Missing Configuration[/bold red]",
            border_style="red"
        ))
        return False

    api_id = os.getenv('API_ID')
    api_hash = os.getenv('API_HASH')

    if not api_id or not api_hash or api_id == 'your_api_id' or api_hash == 'your_api_hash':
        console.print(Panel(
            "[bold red]ERROR: Invalid API credentials![/bold red]\n\n"
            "[yellow]Please update your .env file with valid credentials:[/yellow]\n"
            "API_ID=your_api_id\n"
            "API_HASH=your_api_hash\n\n"
            "[blue]Get your API credentials from:[/blue]\n"
            "https://my.telegram.org/apps",
            title="[bold red]Invalid Configuration[/bold red]",
            border_style="red"
        ))
        return False

    try:
        int(api_id)
        return True
    except ValueError:
        console.print(Panel(
            "[bold red]ERROR: API_ID must be a number![/bold red]",
            title="[bold red]Invalid Configuration[/bold red]",
            border_style="red"
        ))
        return False

class MenuManager:
    def __init__(self, options):
        self.options = options
        self.admins = []
        self.current_group = None
        self.total_members = 0

    def clear_current_group(self):
        """Clear current group and admin list"""
        old_group = self.current_group
        self.current_group = None
        self.admins = []
        console.print(f"[green]Successfully cleared group:[/green] [bold yellow]{old_group}[/bold yellow]")

    def display_menu(self):
        menu_options = self.options.copy()
        
        if self.current_group:
            menu_options.insert(-1, f"6. Exit from [bold yellow]{self.current_group}[/bold yellow]")
            console.print(Panel(
                f"[bold blue]Current Group:[/bold blue] [bold yellow]{self.current_group}[/bold yellow]\n"
                f"[blue]Total Members:[/blue] {self.total_members:,}\n"
                f"[blue]Total Admins:[/blue] {len(self.admins)}",
                title="[bold green]Group Status[/bold green]",
                border_style="blue"
            ))
        
        console.print(Panel(
            "\n".join(f"  {option}" for option in menu_options),
            title="[bold green]Telegram Admin Connect[/bold green]",
            border_style="blue"
        ))

    async def send_message_to_admins(self, app):
        if not self.admins:
            console.print("[red]No admins loaded. Please fetch admins first.[/red]")
            return

        message = Prompt.ask("\nEnter message to send to admins")
        if not message:
            console.print("[red]Message cannot be empty[/red]")
            return

        with Progress(SpinnerColumn(), TextColumn("{task.description}")) as progress:
            task = progress.add_task("Sending messages...", total=len(self.admins))
            
            for admin_id, admin_name in self.admins:
                try:
                    await app.send_message(admin_id, message)
                    progress.update(task, advance=1, description=f"Sent to {admin_name}")
                    await asyncio.sleep(2)
                except Exception as e:
                    console.print(f"[red]Failed to send message to {admin_name}: {str(e)}[/red]")

    async def save_admins_to_file(self):
        if not self.admins:
            console.print("[red]No admins loaded. Please fetch admins first.[/red]")
            return

        filename = Prompt.ask("\nEnter filename to save", default="admins.txt")
        try:
            with open(filename, 'w') as f:
                for admin_id, admin_name in self.admins:
                    f.write(f"{admin_name} (ID: {admin_id})\n")
            console.print(f"[green]Admins saved to {filename}[/green]")
        except Exception as e:
            console.print(f"[red]Error saving file: {str(e)}[/red]")

    async def export_admin_data(self):
        if not self.admins:
            console.print("[red]No admins loaded. Please fetch admins first.[/red]")
            return

        format_type = Prompt.ask(
            "Export format",
            choices=["txt", "csv", "json"],
            default="txt"
        )

        filename = f"admins.{format_type}"
        try:
            if format_type == "txt":
                with open(filename, 'w') as f:
                    for admin_id, admin_name in self.admins:
                        f.write(f"{admin_name} (ID: {admin_id})\n")
            elif format_type == "csv":
                import csv
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["ID", "Name"])
                    writer.writerows(self.admins)
            elif format_type == "json":
                import json
                with open(filename, 'w') as f:
                    json.dump([
                        {"id": id, "name": name} 
                        for id, name in self.admins
                    ], f, indent=2)
            
            console.print(f"[green]Data exported to {filename}[/green]")
        except Exception as e:
            console.print(f"[red]Error exporting data: {str(e)}[/red]")

    async def load_groups_from_file(self):
        filepath = Prompt.ask("\nEnter path to groups file (one group per line)")
        try:
            with open(filepath, 'r') as f:
                groups = [line.strip().lstrip('@') for line in f if line.strip()]
            return groups
        except Exception as e:
            console.print(f"[red]Error reading file: {str(e)}[/red]")
            return []

    async def fetch_admins_for_group(self, app, group):
        self.admins = []
        self.current_group = group
        console.print(f"\n[yellow]Fetching group info for {group}...[/yellow]")
        
        try:
            chat = await app.get_chat(group)
            self.total_members = chat.members_count
            
            async for member in app.get_chat_members(
                chat.id,
                filter=enums.ChatMembersFilter.ADMINISTRATORS
            ):
                if not member.user.is_bot:
                    name = member.user.first_name
                    if member.user.last_name:
                        name += f" {member.user.last_name}"
                    self.admins.append((member.user.id, name))
            
            return True
        except Exception as e:
            console.print(f"[red]Error fetching group info: {str(e)}[/red]")
            return False

    async def show(self):
        try:
            self.display_menu()
            choices = [str(i) for i in range(1, len(self.options) + 1)]
            if self.current_group:
                choices.append("6")
            
            choice = Prompt.ask("Select option", choices=choices)
            
            if choice == "6":
                self.clear_current_group()
                return "0"
                
            return choice
            
        except Exception as e:
            console.print(f"[red]Menu error: {str(e)}[/red]")
            return "5"

async def fetch_admins(app, chat_id):
    """Fetch admin list from group"""
    try:
        chat = await app.get_chat(chat_id)
        
        admins = []
        async for member in app.get_chat_members(
            chat.id, 
            filter=enums.ChatMembersFilter.ADMINISTRATORS
        ):
            if not member.user.is_bot:
                name = member.user.first_name
                if member.user.last_name:
                    name += f" {member.user.last_name}"
                admins.append((member.user.id, name))
        return admins
    except Exception as e:
        console.print(f"[red]Error fetching admins: {str(e)}[/red]")
        return []

async def main():
    if not check_api_credentials():
        return

    try:
        menu_options = [
            "1. Fetch group admins (single group)",
            "2. Load groups from file",
            "3. Send message to admins",
            "4. Export admin data",
            "5. Exit"
        ]

        async with Client("my_account", api_id=api_id, api_hash=api_hash) as app:
            menu = MenuManager(menu_options)
            while True:
                choice = await menu.show()
                
                if choice == "1":
                    group_link = Prompt.ask("\nEnter Telegram group link or username").strip().lstrip('@')
                    await menu.fetch_admins_for_group(app, group_link)
                
                elif choice == "2":
                    groups = await menu.load_groups_from_file()
                    for group in groups:
                        await menu.fetch_admins_for_group(app, group)
                        await asyncio.sleep(2)
                
                elif choice == "3":
                    await menu.send_message_to_admins(app)
                
                elif choice == "4":
                    await menu.export_admin_data()
                
                elif choice == "5":
                    break

                if Prompt.ask("\nContinue?", choices=["y", "n"]) == "n":
                    break

    except KeyboardInterrupt:
        console.print("\n[yellow]Process interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")

if __name__ == "__main__":
    load_dotenv()
    os.system('clear')
    asyncio.run(main())
